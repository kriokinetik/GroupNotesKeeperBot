from aiogram.types import Message, CallbackQuery, ForceReply
from aiogram.fsm.context import FSMContext

from bot import keyboards
from bot.utils import json_utils
from bot.states import RecordData
from bot.config import JSON_FILE_NAME


async def check_and_reply_empty_group(message: Message, state: FSMContext) -> bool:
    if not await json_utils.check_records_existance(JSON_FILE_NAME, message.chat.id):
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


async def check_for_record(callback: CallbackQuery, group_name: str) -> None:
    await callback.message.edit_text(text=f'Группа "{group_name}".\n\n'
                                          f'Записи отсутствуют.',
                                     reply_markup=keyboards.go_back_keyboard)


async def show_history(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    group_name = data["group_name"]
    chat_id = callback.message.chat.id
    record_count = await json_utils.get_record_count(JSON_FILE_NAME, chat_id, group_name)

    if record_count == 0:
        await check_for_record(callback, group_name)
        return
    await state.update_data(record_id=0)
    await edit_history_message(callback, state, group_name, 0)


async def edit_history_message(callback: CallbackQuery, state: FSMContext, group_name: str, record_id: int) -> None:
    chat_id = callback.message.chat.id
    record_count = await json_utils.get_record_count(JSON_FILE_NAME, chat_id, group_name)
    if record_count == 0:
        await check_for_record(callback, group_name)
        return

    record_id = record_id if record_id < record_count else record_id - 1
    record_data = await json_utils.get_record_data(JSON_FILE_NAME, chat_id, group_name, record_id)
    record_datetime = record_data["datetime"]
    record_content = record_data["content"]
    admin = (await state.get_data())["admin"]

    await callback.message.edit_text(
        text=f'<b>Группа "{group_name}"</b>\n'
             f'<i>{record_datetime}, {record_id + 1}/{record_count}</i>'
             f'<blockquote>{record_content}</blockquote>',
        reply_markup=await keyboards.get_navigate_record_keyboard(admin=admin)
    )


async def process_action(callback: CallbackQuery, state: FSMContext, admin: bool) -> None:
    group_name = callback.data[6:]
    data = await state.update_data(group_name=group_name, admin=admin)
    match data["action"]:
        case 'add':
            await request_record(callback, state)
        case 'history':
            await show_history(callback, state)
