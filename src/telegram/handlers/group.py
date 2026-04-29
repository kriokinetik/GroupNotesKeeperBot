"""Telegram handlers for group management flows."""

import logging
from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _

from enums import CommandEnum, ConfirmEnum, ManageEnum, NamespaceEnum
from errors import (
    ChatNotFoundError,
    GroupAlreadyExistsError,
    GroupLimitExceededError,
    GroupNameTooLongError,
    GroupNotFoundError,
)
from repositories import StorageProtocol
from settings import settings
from telegram.callbacks import ConfirmCallback, GroupCallback, ManageCallback
from telegram.filters import IsAdmin, IsInteractionOwner
from telegram.fsm.context import InteractionContextKeys
from telegram.fsm.states import GroupCreate
from telegram.keyboards import CommonKeyboard, GroupKeyboard
from use_cases import (
    AddGroupUseCase,
    DeleteGroupUseCase,
    ListGroupsUseCase,
    ValidateGroupLimitUseCase,
)

router = Router()
logger = logging.getLogger(__name__)

NAMESPACE = NamespaceEnum.GROUPS


def _resolve_group_name_from_snapshot(data: dict, index: int) -> str | None:
    """Resolve a group index from the group list snapshot stored in FSM."""

    raw_groups = data.get(InteractionContextKeys.GROUPS)
    if not isinstance(raw_groups, (list, tuple)):
        return None

    if not 0 <= index < len(raw_groups):
        return None

    group_name = raw_groups[index]
    if not isinstance(group_name, str) or not group_name:
        return None
    return group_name


@router.message(Command(CommandEnum.GROUPS), IsAdmin())
async def handle_group_command(
    message: Message,
    state: FSMContext,
    list_groups: ListGroupsUseCase,
) -> None:
    """Open the group management panel for the current chat."""

    logger.debug(
        "Handling /groups chat_id=%s user_id=%s", message.chat.id, message.from_user.id
    )
    await state.clear()

    groups = await list_groups(message.chat.id)

    text = _("groups_title")
    if groups:
        text += "\n".join(
            _("common_bullet_group_name").format(group_name=escape(group))
            for group in groups
        )
    else:
        text += _("groups_empty")

    bot_message = await message.reply(
        text, reply_markup=CommonKeyboard.manage(namespace=NAMESPACE)
    )
    logger.debug(
        "Rendered group management message chat_id=%s message_id=%s",
        message.chat.id,
        bot_message.message_id,
    )
    await state.update_data(
        {
            InteractionContextKeys.INTERACTION_IDS: bot_message.message_id,
            InteractionContextKeys.GROUPS: groups,
        }
    )


@router.callback_query(
    ManageCallback.filter((F.namespace == NAMESPACE) & (F.action == ManageEnum.ADD)),
    IsInteractionOwner(),
)
async def handle_add_group_callback(
    callback: CallbackQuery,
    state: FSMContext,
    validate_group_limit: ValidateGroupLimitUseCase,
) -> None:
    """Start the group creation flow."""

    await callback.answer()
    logger.debug(
        "Group add flow opened chat_id=%s user_id=%s",
        callback.message.chat.id,
        callback.from_user.id,
    )

    if await validate_group_limit(callback.message.chat.id, settings.group_limit):
        logger.info(
            "Group limit reached chat_id=%s limit=%s",
            callback.message.chat.id,
            settings.group_limit,
        )
        await callback.message.edit_text(_("groups_limit_reached"))
        return

    await callback.message.edit_reply_markup()
    await callback.message.edit_text(_("groups_reply_new_name"))
    await state.update_data(
        {InteractionContextKeys.INTERACTION_IDS: callback.message.message_id}
    )
    await state.set_state(GroupCreate.waiting_group_name)


@router.callback_query(
    ManageCallback.filter((F.namespace == NAMESPACE) & (F.action == ManageEnum.DELETE)),
    IsInteractionOwner(),
)
async def handle_delete_group_callback(
    callback: CallbackQuery, state: FSMContext, storage: StorageProtocol
) -> None:
    """Show groups available for deletion."""

    await callback.answer()
    logger.debug(
        "Group delete selection opened chat_id=%s user_id=%s",
        callback.message.chat.id,
        callback.from_user.id,
    )

    try:
        groups = await storage.group.get(callback.message.chat.id)
    except ChatNotFoundError:
        groups = ()

    if not groups:
        await callback.message.edit_text(_("groups_empty"))
        return

    await state.update_data(
        {
            InteractionContextKeys.INTERACTION_IDS: callback.message.message_id,
            InteractionContextKeys.GROUPS: groups,
        }
    )
    keyboard = await GroupKeyboard.groups(
        action=ManageEnum.DELETE,
        chat_id=callback.message.chat.id,
        storage=storage,
        groups=groups,
    )
    await callback.message.edit_text(
        text=_("groups_choose_delete"),
        reply_markup=keyboard,
    )


@router.message(GroupCreate.waiting_group_name, IsInteractionOwner())
async def handle_add_group(
    message: Message, state: FSMContext, add_group: AddGroupUseCase
) -> None:
    """Create a group from the replied user input."""

    group_name = (message.text or "").strip()
    if not group_name:
        logger.debug(
            "Rejected empty group name chat_id=%s user_id=%s",
            message.chat.id,
            message.from_user.id,
        )
        await message.reply(_("groups_name_empty"))
        return

    try:
        await add_group(message.chat.id, group_name, settings.group_limit)
    except GroupAlreadyExistsError:
        logger.info(
            "Duplicate group rejected chat_id=%s group=%r", message.chat.id, group_name
        )
        await message.reply(
            _("groups_already_exists").format(group_name=escape(group_name))
        )
        return
    except GroupLimitExceededError:
        logger.info(
            "Group creation rejected by limit chat_id=%s group=%r",
            message.chat.id,
            group_name,
        )
        await message.reply(_("groups_limit_reached"))
        return
    except GroupNameTooLongError as error:
        logger.info(
            "Group creation rejected by name length chat_id=%s group=%r limit=%s",
            message.chat.id,
            group_name,
            error.limit,
        )
        await message.reply(_("groups_name_too_long").format(limit=error.limit))
        return

    logger.info(
        "Group created chat_id=%s user_id=%s group=%r",
        message.chat.id,
        message.from_user.id,
        group_name,
    )
    await state.clear()
    await message.reply(_("groups_added").format(group_name=escape(group_name)))


@router.callback_query(
    GroupCallback.filter(F.action == ManageEnum.DELETE), IsInteractionOwner()
)
async def handle_delete_group(
    callback: CallbackQuery,
    callback_data: GroupCallback,
    state: FSMContext,
    storage: StorageProtocol,
) -> None:
    """Ask for confirmation before deleting the selected group."""

    await callback.answer()
    data = await state.get_data()
    group_name = _resolve_group_name_from_snapshot(data, callback_data.index)
    if group_name is None:
        logger.warning(
            "Group deletion target index is stale chat_id=%s user_id=%s index=%s",
            callback.message.chat.id,
            callback.from_user.id,
            callback_data.index,
        )
        await state.clear()
        await callback.message.edit_text(_("groups_not_found"))
        return

    await state.update_data({InteractionContextKeys.GROUP_NAME: group_name})
    logger.debug(
        "Group delete confirmation requested chat_id=%s user_id=%s group=%r",
        callback.message.chat.id,
        callback.from_user.id,
        group_name,
    )

    await callback.message.edit_text(
        _("groups_delete_confirm").format(group_name=escape(group_name)),
        reply_markup=CommonKeyboard.confirm(namespace=NAMESPACE, target="group"),
    )


@router.callback_query(
    ConfirmCallback.filter(
        (F.namespace == NAMESPACE) & (F.decision == ConfirmEnum.YES)
    ),
    IsInteractionOwner(),
)
async def handle_confirm_delete_yes(
    callback: CallbackQuery,
    callback_data: ConfirmCallback,
    state: FSMContext,
    delete_group: DeleteGroupUseCase,
) -> None:
    """Delete the selected group after confirmation."""

    await callback.answer()
    data = await state.get_data()
    group_name = data.get(InteractionContextKeys.GROUP_NAME)
    if not isinstance(group_name, str) or not group_name:
        logger.warning(
            "Group deletion confirmation missing target chat_id=%s user_id=%s",
            callback.message.chat.id,
            callback.from_user.id,
        )
        await state.clear()
        await callback.message.edit_text(_("groups_not_found"))
        return

    try:
        await delete_group(callback.message.chat.id, group_name)
    except GroupNotFoundError:
        logger.warning(
            "Group deletion target missing chat_id=%s group=%r",
            callback.message.chat.id,
            group_name,
        )
        await callback.message.edit_text(_("groups_not_found"))
        await state.clear()
        return

    logger.info(
        "Group deleted chat_id=%s user_id=%s group=%r",
        callback.message.chat.id,
        callback.from_user.id,
        group_name,
    )
    await state.clear()
    await callback.message.edit_text(
        _("groups_deleted").format(group_name=escape(group_name))
    )


@router.callback_query(
    ConfirmCallback.filter((F.namespace == NAMESPACE) & (F.decision == ConfirmEnum.NO)),
    IsInteractionOwner(),
)
async def handle_confirm_delete_no(
    callback: CallbackQuery,
    callback_data: ConfirmCallback,
    state: FSMContext,
) -> None:
    """Cancel group deletion and inform the user."""

    await callback.answer()
    data = await state.get_data()
    group_name = data.get(InteractionContextKeys.GROUP_NAME)
    await state.clear()
    if not isinstance(group_name, str) or not group_name:
        logger.warning(
            "Group deletion cancellation missing target chat_id=%s user_id=%s",
            callback.message.chat.id,
            callback.from_user.id,
        )
        await callback.message.edit_text(_("groups_not_found"))
        return

    logger.debug(
        "Group deletion cancelled chat_id=%s user_id=%s group=%r",
        callback.message.chat.id,
        callback.from_user.id,
        group_name,
    )

    await callback.message.edit_text(
        _("groups_delete_cancelled").format(group_name=escape(group_name))
    )
