"""Telegram handlers for group management flows."""

import logging
from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _

from enums import CommandEnum, ConfirmEnum, ManageEnum, NamespaceEnum
from errors import GroupAlreadyExistsError, GroupLimitExceededError, GroupNotFoundError
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


@router.message(Command(CommandEnum.GROUPS), IsAdmin())
async def handle_group_command(
    message: Message,
    state: FSMContext,
    list_groups: ListGroupsUseCase,
) -> None:
    """Open the group management panel for the current chat."""

    logger.debug("Handling /groups chat_id=%s user_id=%s", message.chat.id, message.from_user.id)
    await state.clear()

    groups = await list_groups(message.chat.id)

    text = _("groups_title")
    if groups:
        text += "\n".join(_("common_bullet_group_name").format(group_name=escape(group)) for group in groups)
    else:
        text += _("groups_empty")

    bot_message = await message.reply(text, reply_markup=CommonKeyboard.manage(namespace=NAMESPACE))
    logger.debug(
        "Rendered group management message chat_id=%s message_id=%s",
        message.chat.id,
        bot_message.message_id,
    )
    await state.update_data(
        {
            InteractionContextKeys.INTERACTION_IDS: bot_message.message_id,
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
    message: Message = callback.message
    logger.debug(
        "Group add flow opened chat_id=%s user_id=%s",
        message.chat.id,
        callback.from_user.id,
    )

    if await validate_group_limit(message.chat.id, settings.group_limit):
        logger.info(
            "Group limit reached chat_id=%s limit=%s",
            message.chat.id,
            settings.group_limit,
        )
        await message.edit_text(_("groups_limit_reached"))
        return

    await message.edit_reply_markup()
    await message.edit_text(_("groups_reply_new_name"))
    await state.update_data({InteractionContextKeys.INTERACTION_IDS: message.message_id})
    await state.set_state(GroupCreate.waiting_group_name)


@router.callback_query(
    ManageCallback.filter((F.namespace == NAMESPACE) & (F.action == ManageEnum.DELETE)),
    IsInteractionOwner(),
)
async def handle_delete_group_callback(callback: CallbackQuery, storage: StorageProtocol) -> None:
    """Show groups available for deletion."""

    await callback.answer()
    message: Message = callback.message
    logger.debug(
        "Group delete selection opened chat_id=%s user_id=%s",
        message.chat.id,
        callback.from_user.id,
    )

    keyboard = await GroupKeyboard.groups(
        action=ManageEnum.DELETE,
        chat_id=message.chat.id,
        storage=storage,
    )
    await message.edit_text(
        text=_("groups_choose_delete"),
        reply_markup=keyboard,
    )


@router.message(GroupCreate.waiting_group_name, IsInteractionOwner())
async def handle_add_group(message: Message, state: FSMContext, add_group: AddGroupUseCase) -> None:
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
        logger.info("Duplicate group rejected chat_id=%s group=%r", message.chat.id, group_name)
        await message.reply(_("groups_already_exists").format(group_name=escape(group_name)))
        return
    except GroupLimitExceededError:
        logger.info(
            "Group creation rejected by limit chat_id=%s group=%r",
            message.chat.id,
            group_name,
        )
        await message.reply(_("groups_limit_reached"))
        return

    logger.info(
        "Group created chat_id=%s user_id=%s group=%r",
        message.chat.id,
        message.from_user.id,
        group_name,
    )
    await state.clear()
    await message.reply(_("groups_added").format(group_name=escape(group_name)))


@router.callback_query(GroupCallback.filter(F.action == ManageEnum.DELETE), IsInteractionOwner())
async def handle_delete_group(
    callback: CallbackQuery,
    callback_data: GroupCallback,
) -> None:
    """Ask for confirmation before deleting the selected group."""

    await callback.answer()
    message: Message = callback.message
    logger.debug(
        "Group delete confirmation requested chat_id=%s user_id=%s group=%r",
        message.chat.id,
        callback.from_user.id,
        callback_data.name,
    )

    await message.edit_text(
        _("groups_delete_confirm").format(group_name=escape(callback_data.name)),
        reply_markup=CommonKeyboard.confirm(namespace=NAMESPACE, target=callback_data.name),
    )


@router.callback_query(
    ConfirmCallback.filter((F.namespace == NAMESPACE) & (F.decision == ConfirmEnum.YES)),
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
    message: Message = callback.message

    try:
        await delete_group(message.chat.id, callback_data.target)
    except GroupNotFoundError:
        logger.warning(
            "Group deletion target missing chat_id=%s group=%r",
            message.chat.id,
            callback_data.target,
        )
        await message.edit_text(_("groups_not_found"))
        await state.clear()
        return

    logger.info(
        "Group deleted chat_id=%s user_id=%s group=%r",
        message.chat.id,
        callback.from_user.id,
        callback_data.target,
    )
    await state.clear()
    await message.edit_text(_("groups_deleted").format(group_name=escape(callback_data.target)))


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
    await state.clear()
    message: Message = callback.message

    logger.debug(
        "Group deletion cancelled chat_id=%s user_id=%s group=%r",
        message.chat.id,
        callback.from_user.id,
        callback_data.target,
    )

    await message.edit_text(_("groups_delete_cancelled").format(group_name=escape(callback_data.target)))
