"""Telegram handlers for chat admin management and message deletion."""

import logging
from html import escape

from aiogram import F, Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ChatMemberUpdated, ForceReply, Message
from aiogram.utils.i18n import gettext as _

from enums import CommandEnum, ConfirmEnum, ManageEnum, NamespaceEnum
from errors import AdminAlreadyExistsError, AdminNotFoundError
from telegram.callbacks import AdminCallback, ConfirmCallback, ManageCallback
from telegram.filters import IsAdmin, IsInteractionOwner, IsOwner
from telegram.fsm.context import InteractionContextKeys
from telegram.fsm.states import AdminManage
from telegram.keyboards import AdminKeyboard, CommonKeyboard
from use_cases import GrantAdminUseCase, ListAdminsUseCase, RevokeAdminUseCase

router = Router()
logger = logging.getLogger(__name__)

NAMESPACE = NamespaceEnum.ADMINS
DELETE_NAMESPACE = NamespaceEnum.ADMINS_DELETE


def _format_user_label(*, user_id: int, username: str | None, full_name: str) -> str:
    """Return the most readable label for a Telegram user."""

    if username:
        return username
    if full_name:
        return full_name
    return str(user_id)


def _format_user_reference(*, user_id: int, label: str) -> str:
    """Format a user label for HTML output, falling back to the numeric ID."""

    if label == str(user_id):
        return f"<code>{user_id}</code>"
    return escape(label)


async def _resolve_user_label(message: Message, user_id: int) -> str:
    """Resolve a display label for a user who should belong to the chat."""

    bot = message.bot
    try:
        member = await bot.get_chat_member(message.chat.id, user_id)
        user = member.user
        return _format_user_label(
            user_id=user_id,
            username=user.username,
            full_name=user.full_name,
        )
    except TelegramAPIError:
        return str(user_id)


async def _resolve_admin_labels(
    message: Message, admin_ids: tuple[int, ...]
) -> tuple[tuple[int, str], ...]:
    """Resolve display labels for all admin IDs in the chat."""

    items: list[tuple[int, str]] = []
    for user_id in admin_ids:
        label = await _resolve_user_label(message, user_id)
        items.append((user_id, label))
    return tuple(items)


async def _render_admins_text(message: Message, list_admins: ListAdminsUseCase) -> str:
    """Render the admin management panel text."""

    chat_id = message.chat.id
    admin_ids = await list_admins(chat_id)
    if not admin_ids:
        return _("admins_empty")

    admin_labels = await _resolve_admin_labels(message, admin_ids)
    lines = [_("admins_title")]
    for user_id, label in admin_labels:
        if label == str(user_id):
            lines.append(_("common_bullet_user_id").format(user_id=user_id))
        else:
            lines.append(_("common_bullet_user_label").format(user_label=escape(label)))
    return "\n".join(lines)


async def _resolve_target_user_id(message: Message) -> int | None:
    """Resolve a target user from reply, mention, username, or raw numeric ID."""

    bot = message.bot
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id

    for entity in message.entities or []:
        if entity.type == "text_mention" and entity.user is not None:
            try:
                await bot.get_chat_member(message.chat.id, entity.user.id)
            except TelegramAPIError:
                return None
            return entity.user.id

    text = (message.text or "").strip()
    if text.isdigit():
        user_id = int(text)
        try:
            await bot.get_chat_member(message.chat.id, user_id)
        except TelegramAPIError:
            return None
        return user_id

    if text and message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
        username = text if text.startswith("@") else f"@{text}"
        try:
            chat = await bot.get_chat(username)
            await bot.get_chat_member(message.chat.id, chat.id)
        except TelegramAPIError:
            return None
        return chat.id

    return None


async def _is_user_in_chat(message: Message, user_id: int) -> bool:
    """Return whether the user is currently a member of the chat."""

    bot = message.bot
    try:
        member = await bot.get_chat_member(message.chat.id, user_id)
    except TelegramAPIError:
        return False
    return member.status not in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}


@router.message(Command(CommandEnum.ADMIN), IsOwner())
async def handle_admin_command(
    message: Message,
    state: FSMContext,
    grant_admin: GrantAdminUseCase,
    list_admins: ListAdminsUseCase,
) -> None:
    """Open admin management or grant admin rights from a replied message."""

    await state.clear()

    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
        target_user_label = _format_user_label(
            user_id=target_user_id,
            username=message.reply_to_message.from_user.username,
            full_name=message.reply_to_message.from_user.full_name,
        )
        target_user_ref = _format_user_reference(
            user_id=target_user_id, label=target_user_label
        )
        if not await _is_user_in_chat(message, target_user_id):
            logger.debug(
                "Admin grant by reply rejected because user is not in chat chat_id=%s owner_id=%s target_user_id=%s",
                message.chat.id,
                message.from_user.id,
                target_user_id,
            )
            await message.reply(_("admins_user_not_in_chat"))
            return
        try:
            await grant_admin(message.chat.id, target_user_id)
        except AdminAlreadyExistsError:
            await message.reply(
                _("admins_user_already_admin").format(user=target_user_ref)
            )
            return

        logger.info(
            "Granting chat admin by reply chat_id=%s owner_id=%s target_user_id=%s",
            message.chat.id,
            message.from_user.id,
            target_user_id,
        )
        await message.reply(_("admins_user_granted").format(user=target_user_ref))
        return

    text = await _render_admins_text(message, list_admins)
    bot_message = await message.reply(
        text, reply_markup=CommonKeyboard.manage(namespace=NAMESPACE)
    )
    await state.update_data(
        {InteractionContextKeys.INTERACTION_IDS: bot_message.message_id}
    )


@router.callback_query(
    ManageCallback.filter((F.namespace == NAMESPACE) & (F.action == ManageEnum.ADD)),
    IsInteractionOwner(),
)
async def handle_admin_add_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Start the flow for adding a chat admin by user reference."""

    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        _("admins_reply_panel"),
    )
    prompt = await callback.message.answer(
        _("admins_reply_target"),
        reply_markup=ForceReply(selective=True),
    )
    await state.update_data(
        {
            InteractionContextKeys.INTERACTION_IDS: [
                callback.message.message_id,
                prompt.message_id,
            ]
        }
    )
    await state.set_state(AdminManage.waiting_target)


@router.message(AdminManage.waiting_target, IsInteractionOwner(), IsOwner())
async def handle_admin_add_input(
    message: Message, state: FSMContext, grant_admin: GrantAdminUseCase
) -> None:
    """Grant admin access to the resolved target user."""

    target_user_id = await _resolve_target_user_id(message)
    if target_user_id is None:
        logger.debug(
            "Admin grant rejected because user could not be resolved chat_id=%s owner_id=%s",
            message.chat.id,
            message.from_user.id,
        )
        await message.reply(_("admins_user_unresolved"))
        return
    target_user_label = await _resolve_user_label(message, target_user_id)
    target_user_ref = _format_user_reference(
        user_id=target_user_id, label=target_user_label
    )

    try:
        await grant_admin(message.chat.id, target_user_id)
    except AdminAlreadyExistsError:
        await message.reply(_("admins_user_already_admin").format(user=target_user_ref))
        return

    logger.info(
        "Granting chat admin from admin flow chat_id=%s owner_id=%s target_user_id=%s",
        message.chat.id,
        message.from_user.id,
        target_user_id,
    )
    await state.clear()
    await message.reply(_("admins_user_granted").format(user=target_user_ref))


@router.callback_query(
    ManageCallback.filter((F.namespace == NAMESPACE) & (F.action == ManageEnum.DELETE)),
    IsInteractionOwner(),
)
async def handle_admin_delete_callback(
    callback: CallbackQuery, state: FSMContext, list_admins: ListAdminsUseCase
) -> None:
    """Show the list of chat admins available for removal."""

    await callback.answer()
    await state.clear()
    admin_ids = await list_admins(callback.message.chat.id)
    if not admin_ids:
        await callback.message.edit_text(_("admins_delete_empty"))
        return

    await state.update_data(
        {InteractionContextKeys.INTERACTION_IDS: callback.message.message_id}
    )
    admin_labels = await _resolve_admin_labels(callback.message, admin_ids)
    await callback.message.edit_text(
        _("admins_select_remove"),
        reply_markup=AdminKeyboard.admins(
            action=ManageEnum.DELETE, admins=admin_labels
        ),
    )


@router.chat_member()
async def handle_chat_member_update(
    event: ChatMemberUpdated,
    list_admins: ListAdminsUseCase,
    revoke_admin: RevokeAdminUseCase,
) -> None:
    """Remove chat admin access automatically when a member leaves the chat."""

    user_id = event.new_chat_member.user.id
    if event.new_chat_member.status not in {
        ChatMemberStatus.LEFT,
        ChatMemberStatus.KICKED,
    }:
        return

    admin_ids = await list_admins(event.chat.id)
    if user_id not in admin_ids:
        logger.debug(
            "Chat member left but was not a chat admin chat_id=%s target_user_id=%s status=%s",
            event.chat.id,
            user_id,
            event.new_chat_member.status,
        )
        return

    await revoke_admin(event.chat.id, user_id)
    logger.info(
        "Chat admin removed after member left chat_id=%s target_user_id=%s status=%s",
        event.chat.id,
        user_id,
        event.new_chat_member.status,
    )


@router.callback_query(
    AdminCallback.filter(F.action == ManageEnum.DELETE), IsInteractionOwner(), IsOwner()
)
async def handle_admin_delete_select(
    callback: CallbackQuery, callback_data: AdminCallback
) -> None:
    """Ask for confirmation before removing the selected chat admin."""

    await callback.answer()
    user_label = await _resolve_user_label(callback.message, callback_data.user_id)
    user_ref = _format_user_reference(user_id=callback_data.user_id, label=user_label)
    logger.debug(
        "Admin deletion confirmation opened chat_id=%s user_id=%s target_user_id=%s",
        callback.message.chat.id,
        callback.from_user.id,
        callback_data.user_id,
    )
    await callback.message.edit_text(
        _("admins_remove_confirm").format(user=user_ref),
        reply_markup=CommonKeyboard.confirm(
            namespace=DELETE_NAMESPACE, target=str(callback_data.user_id)
        ),
    )


@router.callback_query(
    ConfirmCallback.filter(
        (F.namespace == DELETE_NAMESPACE)
        & (F.decision.in_({ConfirmEnum.YES, ConfirmEnum.NO}))
    ),
    IsInteractionOwner(),
    IsOwner(),
)
async def handle_admin_delete_confirm(
    callback: CallbackQuery,
    callback_data: ConfirmCallback,
    state: FSMContext,
    revoke_admin: RevokeAdminUseCase,
    list_admins: ListAdminsUseCase,
) -> None:
    """Confirm or cancel chat admin removal."""

    await callback.answer()
    await state.update_data(
        {InteractionContextKeys.INTERACTION_IDS: callback.message.message_id}
    )

    if callback_data.decision == ConfirmEnum.YES:
        user_id = int(callback_data.target)
        user_label = await _resolve_user_label(callback.message, user_id)
        user_ref = _format_user_reference(user_id=user_id, label=user_label)
        try:
            await revoke_admin(callback.message.chat.id, user_id)
        except AdminNotFoundError:
            await callback.message.edit_text(
                _("admins_user_id_not_found").format(user_id=user_id)
            )
            return

        logger.info(
            "Revoking chat admin from admin flow chat_id=%s owner_id=%s target_user_id=%s",
            callback.message.chat.id,
            callback.from_user.id,
            user_id,
        )
        await callback.message.answer(_("admins_user_removed").format(user=user_ref))

    else:
        logger.debug(
            "Admin deletion cancelled chat_id=%s user_id=%s target_user_id=%s",
            callback.message.chat.id,
            callback.from_user.id,
            callback_data.target,
        )

    admin_ids = await list_admins(callback.message.chat.id)
    if not admin_ids:
        await callback.message.edit_text(_("admins_empty"))
        return

    admin_labels = await _resolve_admin_labels(callback.message, admin_ids)
    await callback.message.edit_text(
        _("admins_select_remove"),
        reply_markup=AdminKeyboard.admins(
            action=ManageEnum.DELETE, admins=admin_labels
        ),
    )


@router.message(Command(CommandEnum.DELETE), IsAdmin())
async def handle_delete_message(message: Message) -> None:
    """Delete the replied message when the current user has admin access."""

    if message.reply_to_message is None:
        logger.debug(
            "Delete message rejected without reply chat_id=%s user_id=%s",
            message.chat.id,
            message.from_user.id,
        )
        await message.reply(_("system_delete_use_reply"))
        return

    logger.info(
        "Deleting replied message chat_id=%s user_id=%s target_message_id=%s",
        message.chat.id,
        message.from_user.id,
        message.reply_to_message.message_id,
    )
    try:
        await message.reply_to_message.delete()
    except (
        TelegramBadRequest,
        TelegramForbiddenError,
        TelegramAPIError,
    ):
        logger.warning(
            "Delete message failed chat_id=%s user_id=%s target_message_id=%s",
            message.chat.id,
            message.from_user.id,
            message.reply_to_message.message_id,
        )
        await message.reply(_("system_delete_failed"))
        return

    try:
        await message.delete()
    except (
        TelegramBadRequest,
        TelegramForbiddenError,
        TelegramAPIError,
    ):
        logger.warning(
            "Command delete failed after target deletion chat_id=%s user_id=%s command_message_id=%s",
            message.chat.id,
            message.from_user.id,
            message.message_id,
        )
