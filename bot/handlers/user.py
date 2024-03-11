import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

import filters, keyboards
from utils import bot_utils, json_utils
from states import RecordData
from config import JSON_FILE_NAME

router = Router()


@router.message(Command('start'))
async def bot_call_handler(message: Message) -> None:
    await message.reply(
        'Привет! Я бот для управления записями по группам. С моей помощью ты можешь создавать группы и '
        'добавлять записи к каждой из них. Позже ты сможешь легко просматривать записи по каждой группе.\n\n'
        'Чтобы начать, используй команду /create для создания новой группы или /add для добавления '
        'записи к уже существующей.\n\n'
        'Для получения справки по командам: /help'
    )
    await json_utils.start_json_session(JSON_FILE_NAME, message.chat.id)


@router.message(Command('help'))
async def bot_call_handler(message: Message) -> None:
    await message.reply('Справка по командам:\n\n'
                        '/add — добавить запись.\n'
                        '/create <code>название</code> — создать указанную группу.\n'
                        '/history — просмотреть историю.\n'
                        '/delete_group <code>название</code> — удалить указанную группу.\n'
                        '/delete_message<i>*</i> — удалить сообщение.\n\n'
                        '<i>* — команды нужно вызывать ответом на сообщение.</i>\n')


@router.message(Command('add'))
async def add_record_handler(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(initial_message=message)
    if await bot_utils.check_and_reply_empty_group(message, state):
        return
    bot_message = await message.reply(text='Выберите группу.',
                                      reply_markup=await keyboards.get_group_selection_keyboard(message,
                                                                                                JSON_FILE_NAME))
    await state.update_data(interaction_right=bot_message.message_id, action='add')


@router.message(Command('history'))
async def show_history_handler(message: Message, state: FSMContext, reply_flag: bool = True):
    await state.clear()
    await state.update_data(initial_message=message)

    if await bot_utils.check_and_reply_empty_group(message, state):
        return

    bot_message = await message.answer(text='Выберите группу.',
                                       reply_to_message_id=message.message_id if reply_flag else None,
                                       reply_markup=await keyboards.get_group_selection_keyboard(message,
                                                                                                 JSON_FILE_NAME)
                                       )
    await state.update_data(interaction_right=bot_message.message_id, action='history')


@router.callback_query(F.data.startswith('group'), filters.KeyboardAccessFilter())
async def non_admin_action_handler(callback: CallbackQuery, state: FSMContext):
    await bot_utils.process_action(callback, state, admin=False)


@router.callback_query(F.data.in_({'next record', 'prev record'}), filters.KeyboardAccessFilter())
async def navigate_records_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chat_id = callback.message.chat.id
    group_name = data["group_name"]
    record_id = data.get("record_id", 0)
    record_count = await json_utils.get_record_count(JSON_FILE_NAME, chat_id, group_name)

    if record_count == 1:
        await callback.answer()
        return

    if callback.data == 'next record':
        record_id = (record_id + 1) % record_count
    else:
        record_id = (record_id - 1) % record_count
    await state.update_data(record_id=record_id)
    await bot_utils.edit_history_message(callback, state, group_name, record_id)


@router.callback_query(F.data == 'go back', filters.KeyboardAccessFilter())
async def go_back_handler(callback: CallbackQuery, state: FSMContext):
    await show_history_handler(callback.message.reply_to_message, state, reply_flag=True)
    await callback.message.delete()


@router.message(RecordData.record_content, filters.MessageAccessFilter())
async def description_handler(message: Message, state: FSMContext):
    chat_id = message.chat.id
    delta = datetime.timedelta(hours=3, minutes=0)
    record_datetime = (message.date + delta).strftime('%d.%m.%y %H:%M')
    group_name = (await state.get_data())["group_name"]
    await json_utils.add_record_to_json(JSON_FILE_NAME, chat_id, group_name, record_datetime, message.text)
    await message.reply(f'В группу "{group_name}" добавлена запись.')
    await state.clear()
