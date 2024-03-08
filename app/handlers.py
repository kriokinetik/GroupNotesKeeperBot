import datetime
import os

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ForceReply
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app import keyboards, json_file, filters
from app.states import RecordData
from config import JSON_FILE_NAME

router = Router()


async def check_and_reply_empty_group(message: Message, state: FSMContext) -> bool:
    if not await json_file.check_records_existance(JSON_FILE_NAME, message.chat.id):
        await message.reply('Группы и записи отсутствуют.')
        await state.clear()
        return True
    return False


async def request_record(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    bot_message = await callback.bot.send_message(chat_id=callback.message.chat.id,
                                                  text=f'Группа "{data["group_name"]}".\n\n'
                                                       f'Опишите ситуацию.',
                                                  reply_to_message_id=data["initial_message"].message_id,
                                                  reply_markup=ForceReply(selective=True)
                                                  )
    await state.update_data(interaction_right=bot_message.message_id)
    await callback.message.delete()
    await state.set_state(RecordData.record_content)


async def edit_history_message(callback: CallbackQuery, group_name: str, record_id: int, record_count: int) -> None:
    chat_id = callback.message.chat.id
    record_data = await json_file.get_record_data(JSON_FILE_NAME, chat_id, group_name, record_id)
    record_datetime = record_data["date"]
    record_content = record_data["description"]
    await callback.message.edit_text(
        text=f'Группа "{group_name}". Запись {record_id + 1}/{record_count}\n\n'
             f'{record_datetime}\n'
             f'{record_content}',
        reply_markup=keyboards.check_history
    )


async def show_history(callback: CallbackQuery, state: FSMContext) -> None:
    group_name = (await state.get_data())["group_name"]
    chat_id = callback.message.chat.id
    if os.path.exists(JSON_FILE_NAME):
        record_count = await json_file.get_record_count(JSON_FILE_NAME, chat_id, group_name)
        if record_count == 0:
            await callback.message.edit_text(text=f'Группа "{group_name}".\n\nЗаписи отсутствуют.',
                                             reply_markup=keyboards.go_back_keyboard)
            return

        await state.update_data(record_id=0)
        await edit_history_message(callback, group_name, 0, record_count)


# Обработчики событий
@router.message(Command('start'))
async def bot_call_handler(message: Message) -> None:
    await message.reply(
        'Привет! Я бот для управления записями по группам. С моей помощью ты можешь создавать группы и '
        'добавлять записи к каждой из них. Позже ты сможешь легко просматривать записи по каждой группе.\n\n'
        'Чтобы начать, используй команду /create для создания новой группы или /add_record для '
        'добавления записи к уже существующей.\n\n'
        'Для получения справки по командам: /help'
    )
    await json_file.start_json_session(JSON_FILE_NAME, message.chat.id)


@router.message(Command('help'))
async def bot_call_handler(message: Message) -> None:
    await message.reply('Справка по командам:\n\n'
                        '/add — добавить запись.\n'
                        '/create <code>название</code> — создать указанную группу.\n'
                        '/history — просмотреть историю.\n'
                        '/edit — отредактировать <i>открытую ранее</i> запись.\n'
                        '/delete_record — удалить <i>открытую ранее</i> запись.\n'
                        '/delete_group <code>название</code> — удалить указанную группу.\n'
                        '/delete_message<i>*</i> — удалить сообщение.\n\n'
                        '<i>*</i> — команды нужно вызывать ответом на сообщение.\n')


@router.message(Command('add'))
async def add_record_handler(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(initial_message=message)
    if await check_and_reply_empty_group(message, state):
        return
    bot_message = await message.reply(text='Выберите группу.',
                                      reply_markup=await keyboards.get_group_selection_keyboard(message,
                                                                                                JSON_FILE_NAME))
    await state.update_data(interaction_right=bot_message.message_id,
                            action='add')


@router.message(Command('history'))
async def show_history_handler(message: Message, state: FSMContext, reply_flag: bool = True):
    await state.clear()
    await state.update_data(initial_message=message)
    if await check_and_reply_empty_group(message, state):
        return
    if reply_flag:
        bot_message = await message.reply(text='Выберите группу.',
                                          reply_markup=await keyboards.get_group_selection_keyboard(message,
                                                                                                    JSON_FILE_NAME))
    else:
        bot_message = await message.answer(text='Выберите группу.',
                                           reply_to_message_id=message.reply_to_message.message_id,
                                           reply_markup=await keyboards.get_group_selection_keyboard(message,
                                                                                                     JSON_FILE_NAME))
    await state.update_data(interaction_right=bot_message.message_id, action='history')


@router.callback_query(F.data.startswith('group'), filters.CallbackAccessFilter())
async def action_handler(callback: CallbackQuery, state: FSMContext):
    group_name = callback.data[6:]
    data = await state.update_data(group_name=group_name)
    if data["action"] == 'add':
        await request_record(callback, state)
    elif data["action"] == 'history':
        await show_history(callback, state)


@router.callback_query(F.data.in_({'next_record', 'prev_record'}), filters.CallbackAccessFilter())
async def navigate_records_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chat_id = callback.message.chat.id
    group_name = data["group_name"]
    record_id = data.get("record_id", 0)
    record_count = await json_file.get_record_count(JSON_FILE_NAME, chat_id, group_name)

    if record_count == 1:
        await callback.answer()
        return

    if callback.data == 'next_record':
        record_id = (record_id + 1) % record_count
    else:
        record_id = (record_id - 1) % record_count

    await state.update_data(record_id=record_id)
    await edit_history_message(callback, group_name, record_id, record_count)


@router.callback_query(F.data == 'go_back', filters.CallbackAccessFilter())
async def go_back_handler(callback: CallbackQuery, state: FSMContext):
    await show_history_handler(callback.message, state, reply_flag=False)
    await callback.message.delete()


@router.message(RecordData.record_content, filters.MessageAccessFilter())
async def description_handler(message: Message, state: FSMContext):
    chat_id = message.chat.id
    delta = datetime.timedelta(hours=3, minutes=0)
    record_datetime = (message.date + delta).strftime('%d.%m.%y %H:%M')
    group_name = (await state.get_data())["group_name"]
    await json_file.add_record_to_json(JSON_FILE_NAME, chat_id, group_name, record_datetime, message.text)
    await message.reply(f'В группу "{group_name}" добавлена запись.')
    await state.clear()
