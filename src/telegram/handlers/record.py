"""Telegram handlers for record creation, browsing, editing, and deletion."""

import logging
import re
from datetime import datetime
from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ChatMemberOwner, ForceReply, Message
from aiogram.utils.i18n import get_i18n, gettext as _

from enums import (
    CommandEnum,
    ConfirmEnum,
    ManageEnum,
    NamespaceEnum,
    RecordEnum,
    RecordFlowEnum,
)
from errors import ChatNotFoundError, RecordNotFoundError
from repositories import StorageProtocol
from telegram.callbacks import ConfirmCallback, GroupCallback, RecordCallback
from telegram.filters import IsAdmin, IsInteractionOwner
from telegram.fsm.context import InteractionContextKeys
from telegram.fsm.states import RecordCreate, RecordEdit
from telegram.keyboards import CommonKeyboard, GroupKeyboard, RecordKeyboard
from use_cases import (
    AddRecordUseCase,
    CountRecordsUseCase,
    DeleteRecordUseCase,
    EditRecordUseCase,
    GetRecordUseCase,
    ListRecordGroupsUseCase,
)

router = Router()
logger = logging.getLogger(__name__)

DELETE_NAMESPACE = NamespaceEnum.RECORDS_DELETE
CODE_LANGUAGE_RE = re.compile(r'<code\s+language="([^"]+)">')


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


def _normalize_telegram_html(value: str | None) -> str | None:
    """Normalize HTML produced from Telegram entities to Bot API compatible HTML."""

    if not value:
        return None

    # Telegram accepts <code class="language-python"> inside <pre>, but
    # aiogram may serialize this as language="language-python".
    return CODE_LANGUAGE_RE.sub(r'<code class="\1">', value)


def _format_record_datetime(value: datetime) -> str:
    """Format a record timestamp according to the current locale."""

    locale = get_i18n().current_locale

    if locale == "ru":
        month = (
            _("month_january_genitive"),
            _("month_february_genitive"),
            _("month_march_genitive"),
            _("month_april_genitive"),
            _("month_may_genitive"),
            _("month_june_genitive"),
            _("month_july_genitive"),
            _("month_august_genitive"),
            _("month_september_genitive"),
            _("month_october_genitive"),
            _("month_november_genitive"),
            _("month_december_genitive"),
        )[value.month - 1]
        return f"{value.day} {month} {value.year}, {value:%H:%M}"

    month = (
        _("month_january"),
        _("month_february"),
        _("month_march"),
        _("month_april"),
        _("month_may"),
        _("month_june"),
        _("month_july"),
        _("month_august"),
        _("month_september"),
        _("month_october"),
        _("month_november"),
        _("month_december"),
    )[value.month - 1]
    return f"{month} {value.day}, {value.year}, {value:%H:%M}"


def _extract_message_content(message: Message) -> tuple[str, str | None]:
    """Return plain and HTML-preserved message text."""

    plain_text = (message.text or "").strip()
    html_text = _normalize_telegram_html((message.html_text or "").strip() or None)
    return plain_text, html_text


def _build_record_text(
    *,
    group_name: str,
    record_index: int,
    count: int,
    created_at: datetime,
    content: str,
    creator: str | None,
) -> str:
    """Build the formatted history message body."""

    creator_line = ""
    if creator:
        creator_line = f"\n\n— <i>{escape(creator)}</i>"

    return (
        f"<b>{escape(group_name)}</b>\n"
        f"<i>{record_index}/{count} · {escape(_format_record_datetime(created_at))}</i>\n"
        f"───────────────\n"
        f"{content}"
        f"{creator_line}"
    )


async def _is_admin_viewer(
    *,
    bot: Bot,
    chat_id: int,
    chat_type: str,
    user_id: int,
    storage: StorageProtocol,
    owners: list[int],
) -> bool:
    """Return whether the current viewer may use admin record actions."""

    if chat_type == "private":
        return True

    if user_id in owners:
        return True

    try:
        chat_member = await bot.get_chat_member(chat_id, user_id)
    except TelegramAPIError:
        logger.warning(
            "Admin lookup failed at chat member check chat_id=%s user_id=%s",
            chat_id,
            user_id,
        )
        return False
    if isinstance(chat_member, ChatMemberOwner):
        return True

    try:
        admins = await storage.admin.get(chat_id)
    except ChatNotFoundError:
        return False

    return user_id in admins


async def _build_history_payload(
    *,
    bot: Bot,
    chat_id: int,
    chat_type: str,
    user_id: int,
    state: FSMContext,
    storage: StorageProtocol,
    owners: list[int],
    get_record: GetRecordUseCase,
    count_records: CountRecordsUseCase,
) -> tuple[str, bool, bool]:
    """Build record history text, admin flag, and navigation flag."""

    data = await state.get_data()
    group_name = data[InteractionContextKeys.GROUP_NAME]
    record_id = data.get(InteractionContextKeys.RECORD_ID, 0)
    is_admin = await _is_admin_viewer(
        bot=bot,
        chat_id=chat_id,
        chat_type=chat_type,
        user_id=user_id,
        storage=storage,
        owners=owners,
    )

    count = await count_records(chat_id, group_name)
    if count == 0:
        return (
            _("records_group_empty").format(group_name=escape(group_name)),
            False,
            False,
        )

    if record_id >= count:
        record_id = count - 1
        await state.update_data({InteractionContextKeys.RECORD_ID: record_id})

    record = await get_record(chat_id, group_name, record_id)
    if record is None:
        return _("records_entry_not_found"), False, False

    content = _normalize_telegram_html(record.content_html) or escape(record.content)
    text = _build_record_text(
        group_name=group_name,
        record_index=record_id + 1,
        count=count,
        created_at=record.datetime,
        content=content,
        creator=record.creator,
    )
    return text, is_admin, count > 1


async def _render_history_message(
    *,
    message: Message,
    viewer_id: int,
    state: FSMContext,
    storage: StorageProtocol,
    owners: list[int],
    get_record: GetRecordUseCase,
    count_records: CountRecordsUseCase,
) -> None:
    """Render the current history view into the given message."""

    bot = message.bot
    text, is_admin, can_navigate = await _build_history_payload(
        bot=bot,
        chat_id=message.chat.id,
        chat_type=message.chat.type,
        user_id=viewer_id,
        state=state,
        storage=storage,
        owners=owners,
        get_record=get_record,
        count_records=count_records,
    )
    try:
        await message.edit_text(
            text,
            reply_markup=RecordKeyboard.navigate(
                is_admin=is_admin,
                can_navigate=can_navigate,
            ),
        )
    except TelegramBadRequest:
        logger.warning(
            "History render failed with formatted content, falling back to plain text chat_id=%s message_id=%s",
            message.chat.id,
            message.message_id,
        )
        data = await state.get_data()
        group_name = data[InteractionContextKeys.GROUP_NAME]
        record_id = data.get(InteractionContextKeys.RECORD_ID, 0)
        record = await get_record(message.chat.id, group_name, record_id)
        if record is None:
            raise
        fallback_text = _build_record_text(
            group_name=group_name,
            record_index=record_id + 1,
            count=await count_records(message.chat.id, group_name),
            created_at=record.datetime,
            content=escape(record.content),
            creator=record.creator,
        )
        await message.edit_text(
            fallback_text,
            reply_markup=RecordKeyboard.navigate(
                is_admin=is_admin,
                can_navigate=can_navigate,
            ),
        )


async def _refresh_history_view(
    *,
    message: Message,
    viewer_id: int,
    state: FSMContext,
    storage: StorageProtocol,
    owners: list[int],
    get_record: GetRecordUseCase,
    count_records: CountRecordsUseCase,
) -> None:
    """Refresh the existing history message after state changes."""

    bot = message.bot
    text, is_admin, can_navigate = await _build_history_payload(
        bot=bot,
        chat_id=message.chat.id,
        chat_type=message.chat.type,
        user_id=viewer_id,
        state=state,
        storage=storage,
        owners=owners,
        get_record=get_record,
        count_records=count_records,
    )
    data = await state.get_data()
    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data[InteractionContextKeys.VIEW_MESSAGE_ID],
            text=text,
            reply_markup=RecordKeyboard.navigate(
                is_admin=is_admin,
                can_navigate=can_navigate,
            ),
        )
    except TelegramBadRequest:
        logger.warning(
            "History refresh failed with formatted content, falling back to plain text chat_id=%s message_id=%s",
            message.chat.id,
            data[InteractionContextKeys.VIEW_MESSAGE_ID],
        )
        group_name = data[InteractionContextKeys.GROUP_NAME]
        record_id = data.get(InteractionContextKeys.RECORD_ID, 0)
        record = await get_record(message.chat.id, group_name, record_id)
        if record is None:
            raise
        fallback_text = _build_record_text(
            group_name=group_name,
            record_index=record_id + 1,
            count=await count_records(message.chat.id, group_name),
            created_at=record.datetime,
            content=escape(record.content),
            creator=record.creator,
        )
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data[InteractionContextKeys.VIEW_MESSAGE_ID],
            text=fallback_text,
            reply_markup=RecordKeyboard.navigate(
                is_admin=is_admin,
                can_navigate=can_navigate,
            ),
        )


@router.message(Command(CommandEnum.ADD))
async def handle_add_command(
    message: Message,
    storage: StorageProtocol,
    state: FSMContext,
    list_record_groups: ListRecordGroupsUseCase,
) -> None:
    """Start the flow for adding a record to a group."""

    logger.debug(
        "Handling /add chat_id=%s user_id=%s", message.chat.id, message.from_user.id
    )
    await state.clear()

    groups = await list_record_groups(message.chat.id)
    if not groups:
        logger.debug(
            "Add entry blocked because no groups exist chat_id=%s", message.chat.id
        )
        await message.reply(_("records_create_group_first"))
        return

    bot_message = await message.reply(
        _("records_select_group"),
        reply_markup=await GroupKeyboard.groups(
            action=ManageEnum.SELECT,
            chat_id=message.chat.id,
            storage=storage,
            groups=groups,
        ),
    )
    await state.update_data(
        {
            InteractionContextKeys.INTERACTION_IDS: bot_message.message_id,
            InteractionContextKeys.ACTION: RecordFlowEnum.ADD,
            InteractionContextKeys.GROUPS: groups,
        }
    )


@router.message(Command(CommandEnum.HISTORY))
async def handle_history_command(
    message: Message,
    storage: StorageProtocol,
    state: FSMContext,
    list_record_groups: ListRecordGroupsUseCase,
) -> None:
    """Start the flow for browsing record history by group."""

    logger.debug(
        "Handling /history chat_id=%s user_id=%s", message.chat.id, message.from_user.id
    )
    await state.clear()

    groups = await list_record_groups(message.chat.id)
    if not groups:
        logger.debug("History requested without groups chat_id=%s", message.chat.id)
        await message.reply(_("records_groups_or_entries_empty"))
        return

    bot_message = await message.reply(
        _("records_select_group"),
        reply_markup=await GroupKeyboard.groups(
            action=ManageEnum.SELECT,
            chat_id=message.chat.id,
            storage=storage,
            groups=groups,
        ),
    )
    await state.update_data(
        {
            InteractionContextKeys.INTERACTION_IDS: bot_message.message_id,
            InteractionContextKeys.ACTION: RecordFlowEnum.HISTORY,
            InteractionContextKeys.GROUPS: groups,
        }
    )


@router.callback_query(
    GroupCallback.filter(F.action == ManageEnum.SELECT), IsInteractionOwner()
)
async def handle_group_selection(
    callback: CallbackQuery,
    callback_data: GroupCallback,
    state: FSMContext,
    storage: StorageProtocol,
    owners: list[int],
    get_record: GetRecordUseCase,
    count_records: CountRecordsUseCase,
) -> None:
    """Handle group selection for add and history flows."""

    await callback.answer()
    data = await state.get_data()
    action = data.get(InteractionContextKeys.ACTION, RecordFlowEnum.ADD)
    group_name = _resolve_group_name_from_snapshot(data, callback_data.index)
    if group_name is None:
        logger.warning(
            "Group selection target index is stale chat_id=%s user_id=%s index=%s",
            callback.message.chat.id,
            callback.from_user.id,
            callback_data.index,
        )
        await state.clear()
        await callback.message.edit_text(_("groups_not_found"))
        return

    logger.debug(
        "Group selected for record flow chat_id=%s user_id=%s action=%s group=%r",
        callback.message.chat.id,
        callback.from_user.id,
        action,
        group_name,
    )

    if action == RecordFlowEnum.HISTORY:
        await state.update_data(
            {
                InteractionContextKeys.GROUP_NAME: group_name,
                InteractionContextKeys.RECORD_ID: 0,
                InteractionContextKeys.VIEW_MESSAGE_ID: callback.message.message_id,
            }
        )
        await _render_history_message(
            message=callback.message,
            viewer_id=callback.from_user.id,
            state=state,
            storage=storage,
            owners=owners,
            get_record=get_record,
            count_records=count_records,
        )
        return

    await state.update_data({InteractionContextKeys.GROUP_NAME: group_name})
    await callback.message.edit_text(
        _("records_selected_group").format(group_name=escape(group_name))
    )
    prompt = await callback.message.answer(
        _("records_reply_entry_text").format(group_name=escape(group_name)),
        reply_markup=ForceReply(selective=True),
    )
    await state.update_data({InteractionContextKeys.INTERACTION_IDS: prompt.message_id})
    await state.set_state(RecordCreate.waiting_content)


@router.message(RecordCreate.waiting_content, IsInteractionOwner())
async def handle_record_content(
    message: Message, state: FSMContext, add_record: AddRecordUseCase
) -> None:
    """Persist a newly entered record and finish the creation flow."""

    data = await state.get_data()
    group_name = data[InteractionContextKeys.GROUP_NAME]
    content, content_html = _extract_message_content(message)
    if not content:
        logger.debug(
            "Rejected empty record content chat_id=%s group=%r",
            message.chat.id,
            group_name,
        )
        await message.reply(_("records_entry_text_empty"))
        return

    await add_record(
        message.chat.id,
        group_name,
        content,
        content_html,
        message.date,
        message.from_user.username,
    )
    logger.info(
        "Record created chat_id=%s user_id=%s group=%r",
        message.chat.id,
        message.from_user.id,
        group_name,
    )
    await state.clear()
    await message.reply(_("records_entry_added").format(group_name=escape(group_name)))


@router.callback_query(
    RecordCallback.filter(F.action.in_({RecordEnum.PREV, RecordEnum.NEXT})),
    IsInteractionOwner(),
)
async def handle_record_navigation(
    callback: CallbackQuery,
    callback_data: RecordCallback,
    state: FSMContext,
    storage: StorageProtocol,
    owners: list[int],
    get_record: GetRecordUseCase,
    count_records: CountRecordsUseCase,
) -> None:
    """Move backward or forward through record history."""

    await callback.answer()
    data = await state.get_data()
    group_name = data[InteractionContextKeys.GROUP_NAME]
    record_id = data.get(InteractionContextKeys.RECORD_ID, 0)
    total = await count_records(callback.message.chat.id, group_name)
    if total <= 1:
        logger.debug(
            "Record navigation ignored because total<=1 chat_id=%s group=%r",
            callback.message.chat.id,
            group_name,
        )
        return

    if callback_data.action == RecordEnum.NEXT:
        record_id = (record_id + 1) % total
    else:
        record_id = (record_id - 1) % total

    await state.update_data({InteractionContextKeys.RECORD_ID: record_id})
    logger.debug(
        "Record navigated chat_id=%s user_id=%s group=%r record_id=%s action=%s",
        callback.message.chat.id,
        callback.from_user.id,
        group_name,
        record_id,
        callback_data.action,
    )
    await _render_history_message(
        message=callback.message,
        viewer_id=callback.from_user.id,
        state=state,
        storage=storage,
        owners=owners,
        get_record=get_record,
        count_records=count_records,
    )


@router.callback_query(
    RecordCallback.filter(F.action == RecordEnum.BACK), IsInteractionOwner()
)
async def handle_history_back(
    callback: CallbackQuery, state: FSMContext, storage: StorageProtocol
) -> None:
    """Return from history view back to group selection."""

    await callback.answer()
    logger.debug(
        "History back to group selection chat_id=%s user_id=%s",
        callback.message.chat.id,
        callback.from_user.id,
    )
    await state.update_data(
        {
            InteractionContextKeys.ACTION: RecordFlowEnum.HISTORY,
            InteractionContextKeys.INTERACTION_IDS: callback.message.message_id,
        }
    )
    try:
        groups = await storage.group.get(callback.message.chat.id)
    except ChatNotFoundError:
        groups = ()

    if not groups:
        await state.clear()
        await callback.message.edit_text(_("records_groups_or_entries_empty"))
        return

    await state.update_data({InteractionContextKeys.GROUPS: groups})
    await callback.message.edit_text(
        _("records_select_group"),
        reply_markup=await GroupKeyboard.groups(
            action=ManageEnum.SELECT,
            chat_id=callback.message.chat.id,
            storage=storage,
            groups=groups,
        ),
    )


@router.callback_query(
    RecordCallback.filter(F.action == RecordEnum.EDIT), IsInteractionOwner(), IsAdmin()
)
async def handle_edit_record_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Start editing the currently selected record."""

    await callback.answer()
    logger.debug(
        "Record edit started chat_id=%s user_id=%s",
        callback.message.chat.id,
        callback.from_user.id,
    )
    prompt = await callback.message.answer(
        _("records_reply_updated_entry_text"),
        reply_markup=ForceReply(selective=True),
    )
    await state.update_data(
        {
            InteractionContextKeys.INTERACTION_IDS: prompt.message_id,
            InteractionContextKeys.VIEW_MESSAGE_ID: callback.message.message_id,
        }
    )
    await state.set_state(RecordEdit.waiting_new_content)


@router.message(RecordEdit.waiting_new_content, IsInteractionOwner(), IsAdmin())
async def handle_edit_record_submit(
    message: Message,
    state: FSMContext,
    storage: StorageProtocol,
    owners: list[int],
    edit_record: EditRecordUseCase,
    get_record: GetRecordUseCase,
    count_records: CountRecordsUseCase,
) -> None:
    """Persist edited record content and refresh the history view."""

    content, content_html = _extract_message_content(message)
    if not content:
        logger.debug(
            "Rejected empty edited record content chat_id=%s user_id=%s",
            message.chat.id,
            message.from_user.id,
        )
        await message.reply(_("records_entry_text_empty"))
        return

    data = await state.get_data()
    group_name = data[InteractionContextKeys.GROUP_NAME]
    record_id = data[InteractionContextKeys.RECORD_ID]
    view_message_id = data[InteractionContextKeys.VIEW_MESSAGE_ID]

    try:
        await edit_record(
            message.chat.id,
            group_name,
            record_id,
            content,
            content_html,
        )
    except RecordNotFoundError:
        logger.warning(
            "Record edit failed because record is missing chat_id=%s user_id=%s group=%r record_id=%s",
            message.chat.id,
            message.from_user.id,
            group_name,
            record_id,
        )
        await state.clear()
        await message.reply(_("records_entry_not_found"))
        return
    logger.info(
        "Record updated chat_id=%s user_id=%s group=%r record_id=%s",
        message.chat.id,
        message.from_user.id,
        group_name,
        record_id,
    )
    await state.update_data({InteractionContextKeys.INTERACTION_IDS: view_message_id})
    await state.set_state(None)

    await _refresh_history_view(
        message=message,
        viewer_id=message.from_user.id,
        state=state,
        storage=storage,
        owners=owners,
        get_record=get_record,
        count_records=count_records,
    )
    await message.reply(_("records_entry_updated"))


@router.callback_query(
    RecordCallback.filter(F.action == RecordEnum.DELETE),
    IsInteractionOwner(),
    IsAdmin(),
)
async def handle_delete_record_start(callback: CallbackQuery) -> None:
    """Ask for confirmation before deleting the current record."""

    await callback.answer()
    logger.debug(
        "Record deletion confirmation opened chat_id=%s user_id=%s",
        callback.message.chat.id,
        callback.from_user.id,
    )
    await callback.message.edit_text(
        _("records_delete_confirm"),
        reply_markup=CommonKeyboard.confirm(
            namespace=DELETE_NAMESPACE, target="record"
        ),
    )


@router.callback_query(
    ConfirmCallback.filter(
        (F.namespace == DELETE_NAMESPACE)
        & (F.decision.in_({ConfirmEnum.YES, ConfirmEnum.NO}))
    ),
    IsInteractionOwner(),
    IsAdmin(),
)
async def handle_delete_record_confirm(
    callback: CallbackQuery,
    callback_data: ConfirmCallback,
    state: FSMContext,
    storage: StorageProtocol,
    owners: list[int],
    delete_record: DeleteRecordUseCase,
    get_record: GetRecordUseCase,
    count_records: CountRecordsUseCase,
) -> None:
    """Confirm or cancel deletion of the current record."""

    await callback.answer()
    data = await state.get_data()
    if callback_data.decision == ConfirmEnum.YES:
        logger.info(
            "Record deletion confirmed chat_id=%s user_id=%s group=%r record_id=%s",
            callback.message.chat.id,
            callback.from_user.id,
            data[InteractionContextKeys.GROUP_NAME],
            data[InteractionContextKeys.RECORD_ID],
        )
        try:
            await delete_record(
                callback.message.chat.id,
                data[InteractionContextKeys.GROUP_NAME],
                data[InteractionContextKeys.RECORD_ID],
            )
        except RecordNotFoundError:
            logger.warning(
                "Record deletion failed because record is missing chat_id=%s user_id=%s group=%r record_id=%s",
                callback.message.chat.id,
                callback.from_user.id,
                data[InteractionContextKeys.GROUP_NAME],
                data[InteractionContextKeys.RECORD_ID],
            )
            await state.clear()
            await callback.message.edit_text(_("records_entry_not_found"))
            return
        remaining = await count_records(
            callback.message.chat.id, data[InteractionContextKeys.GROUP_NAME]
        )
        if remaining == 0:
            logger.debug(
                "Last record deleted in group chat_id=%s group=%r",
                callback.message.chat.id,
                data[InteractionContextKeys.GROUP_NAME],
            )
            await state.clear()
            await callback.message.edit_text(_("records_no_entries_left"))
            return

        next_record_id = min(data[InteractionContextKeys.RECORD_ID], remaining - 1)
        await state.update_data(
            {
                InteractionContextKeys.RECORD_ID: next_record_id,
                InteractionContextKeys.VIEW_MESSAGE_ID: callback.message.message_id,
                InteractionContextKeys.INTERACTION_IDS: callback.message.message_id,
            }
        )
    else:
        logger.debug(
            "Record deletion cancelled chat_id=%s user_id=%s",
            callback.message.chat.id,
            callback.from_user.id,
        )
        await state.update_data(
            {
                InteractionContextKeys.VIEW_MESSAGE_ID: callback.message.message_id,
                InteractionContextKeys.INTERACTION_IDS: callback.message.message_id,
            }
        )

    await _render_history_message(
        message=callback.message,
        viewer_id=callback.from_user.id,
        state=state,
        storage=storage,
        owners=owners,
        get_record=get_record,
        count_records=count_records,
    )
