import datetime
import os

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ForceReply
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app import keyboards, json_file, filters
from app.states import ShameData

router = Router()


@router.message(Command('start', 'help'))
async def bot_call_handler(message: Message):
    await message.reply(text='/add@ShameCounter_Bot — добавить запись\n'
                             '/history@ShameCounter_Bot — просмотреть историю')


@router.message(Command('add'))
async def add_record_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    if data:
        await state.clear()
    await state.update_data(start_message=message)
    if json_file.json_load('shame.json') == {}:
        await message.reply(text='Группы и записи отсутствуют.')
        await state.clear()
        return
    bot_message = await message.reply(text='Выберите группу.',
                                      reply_markup=keyboards.get_group_selection_keyboard('shame.json'))
    await state.update_data(message_access=bot_message.message_id, action='add')


@router.message(Command('history'))
async def show_history_handler(message: Message, state: FSMContext, reply_flag: bool = True):
    data = await state.get_data()
    if data:
        await state.clear()
    await state.update_data(start_message=message)
    if json_file.json_load('shame.json') == {}:
        await message.reply(text='Группы и записи отсутствуют.')
        await state.clear()
        return
    if reply_flag:
        bot_message = await message.reply(text='Выберите группу.',
                                          reply_markup=keyboards.get_group_selection_keyboard('shame.json'))
    else:
        bot_message = await message.answer(text='Выберите группу.',
                                           reply_to_message_id=message.reply_to_message.message_id,
                                           reply_markup=keyboards.get_group_selection_keyboard('shame.json'))
    await state.update_data(message_access=bot_message.message_id, action='history')


async def request_a_record(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bot_message = await callback.bot.send_message(chat_id=callback.message.chat.id,
                                                  text=f'Группа "{data["group_name"]}".\n\n'
                                                       f'Опишите ситуацию.',
                                                  reply_to_message_id=data['start_message'].message_id,
                                                  reply_markup=ForceReply(selective=True)
                                                  )
    await state.update_data(message_access=bot_message.message_id)
    await callback.message.delete()
    await state.set_state(ShameData.description)


async def show_history(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if os.path.exists('shame.json'):
        number_of_records = json_file.get_the_record_number('shame.json', data['group_name'])
        if number_of_records != 0:
            await state.update_data(shame_id=0)
            data = await state.get_data()
            shame_data = json_file.get_the_shame_data('shame.json', data['group_name'], data['shame_id'])
            await callback.message.edit_text(text=f'Группа "{data["group_name"]}".\n\n'
                                                  f'{shame_data}',
                                             reply_markup=keyboards.check_history)
        else:
            await callback.message.edit_text(text=f'Группа "{data["group_name"]}".\n\n'
                                                  f'Записи отсутствуют.',
                                             reply_markup=keyboards.go_back_keyboard)


@router.callback_query(F.data.startswith('group'), filters.CallbackAccess())
async def action_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.update_data(group_name=callback.data[6:])
    if data['action'] == 'add':
        await request_a_record(callback, state)
    elif data['action'] == 'history':
        await show_history(callback, state)


@router.callback_query(F.data == 'next_record', filters.CallbackAccess())
async def next_record_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_id = json_file.get_the_record_number('shame.json', data['group_name']) - 1
    if data['shame_id'] == last_id:
        next_id = 0
        data = await state.update_data(shame_id=next_id)
    else:
        next_id = data['shame_id'] + 1
        data = await state.update_data(shame_id=next_id)
    shame_data = json_file.get_the_shame_data('shame.json', data['group_name'], data['shame_id'])
    await callback.message.edit_text(text=f'Группа "{data["group_name"]}".\n\n'
                                          f'{shame_data}',
                                     reply_markup=keyboards.check_history)


@router.callback_query(F.data == 'prev_record', filters.CallbackAccess())
async def prev_record_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data['shame_id'] == 0:
        next_id = json_file.get_the_record_number('shame.json', data['group_name']) - 1
        data = await state.update_data(shame_id=next_id)
    else:
        next_id = data['shame_id'] - 1
        data = await state.update_data(shame_id=next_id)
    shame_data = json_file.get_the_shame_data('shame.json', data['group_name'], data['shame_id'])
    await callback.message.edit_text(text=f'Группа "{data["group_name"]}".\n\n'
                                          f'{shame_data}',
                                     reply_markup=keyboards.check_history)


@router.callback_query(F.data == 'go_back', filters.CallbackAccess())
async def go_back_handler(callback: CallbackQuery, state: FSMContext):
    await show_history_handler(callback.message, state, reply_flag=False)
    await callback.message.delete()


@router.message(ShameData.description, filters.MessageAccess())
async def description_handler(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    delta = datetime.timedelta(hours=3, minutes=0)
    data = await state.update_data(message_datetime=(message.date + delta).strftime('%d.%m.%y %H:%M'))
    json_file.add_record_to_json('shame.json', data['group_name'], data['message_datetime'], data['description'])
    await message.reply(text=f'В группу "{data["group_name"]}" добавлена запись.')
    await state.clear()
