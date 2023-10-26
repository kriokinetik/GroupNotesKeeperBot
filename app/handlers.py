import datetime
import os

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ForceReply
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app import keyboards, json_file, filters
from app.states import ShameData

router = Router()


@router.message(Command('start', 'shame'))
async def bot_call_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    if data:
        await state.clear()
    await state.update_data(start_message=message)
    bot_message = await message.reply(text='Выберите группу:',
                                      reply_markup=keyboards.group_selection)
    await state.update_data(message_access=bot_message.message_id)


@router.callback_query(filters.CallbackAccess(), F.data == 'home')
async def home_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_state()
    if data is not None:
        await state.set_state(state=None)
    await callback.message.edit_text(text='Выберите группу:',
                                     reply_markup=keyboards.group_selection)


@router.callback_query(filters.Admin(), F.data == 'delete_message')
async def delete_message_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()


@router.callback_query(filters.CallbackAccess(), F.data.startswith('group'))
async def pozorniki_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.update_data(group_name=callback.data[6:])
    await callback.message.edit_text(text=f'Выбрана группа: {data["group_name"]}\n'
                                          f'Выберите действие:',
                                     reply_markup=keyboards.action_selection)


@router.callback_query(filters.CallbackAccess(), F.data == 'check_history')
async def check_history_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if os.path.exists('shame.json'):
        number_of_records = json_file.get_the_record_number('shame.json', data['group_name'])
        if number_of_records != 0:
            await state.update_data(shame_id=0)
            data = await state.get_data()
            shame_data = json_file.get_the_shame_data('shame.json', data['group_name'], data['shame_id'])
            await callback.message.edit_text(text=f'Выбрана группа: {data["group_name"]}\n'
                                                  f'Выбрано действие: Просмотр истории\n\n'
                                                  f'{shame_data}',
                                             reply_markup=keyboards.check_history)
        else:
            await callback.message.edit_text(text=f'Выбрана группа: {data["group_name"]}\n'
                                                  f'Выбрано действие: Просмотр истории\n'
                                                  f'Вы ещё не записали ни одного позора',
                                             reply_markup=keyboards.go_home)
    else:
        await callback.message.edit_text(text=f'Выбрана группа: {data["group_name"]}\n'
                                              f'Выбрано действие: Просмотр истории\n'
                                              f'Вы ещё не записали ни одного позора',
                                         reply_markup=keyboards.go_home)


@router.callback_query(filters.CallbackAccess(), F.data == 'back')
async def back_history_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data['shame_id'] == 0:
        next_id = json_file.get_the_record_number('shame.json', data['group_name']) - 1
        data = await state.update_data(shame_id=next_id)
    else:
        next_id = data['shame_id'] - 1
        data = await state.update_data(shame_id=next_id)
    shame_data = json_file.get_the_shame_data('shame.json', data['group_name'], data['shame_id'])
    await callback.message.edit_text(text=f'Выбрана группа: {data["group_name"]}\n'
                                          f'Выбрано действие: Просмотр истории\n\n'
                                          f'{shame_data}',
                                     reply_markup=keyboards.check_history)


@router.callback_query(filters.CallbackAccess(), F.data == 'forward')
async def forward_history_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_id = json_file.get_the_record_number('shame.json', data['group_name']) - 1
    if data['shame_id'] == last_id:
        next_id = 0
        data = await state.update_data(shame_id=next_id)
    else:
        next_id = data['shame_id'] + 1
        data = await state.update_data(shame_id=next_id)
    shame_data = json_file.get_the_shame_data('shame.json', data['group_name'], data['shame_id'])
    await callback.message.edit_text(text=f'Выбрана группа: {data["group_name"]}\n'
                                          f'Выбрано действие: Просмотр истории\n\n'
                                          f'{shame_data}',
                                     reply_markup=keyboards.check_history)


@router.callback_query(filters.Admin(), F.data == 'delete_record')
async def delete_record_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    shame_data = json_file.get_the_shame_data('shame.json', data['group_name'], data['shame_id'])
    await callback.message.edit_text(text=f'Вы уверены, что хотите удалить запись:\n\n'
                                          f'{shame_data}',
                                     reply_markup=keyboards.action_check)


@router.callback_query(filters.Admin(), F.data == 'positive_check')
async def positive_check_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    json_file.delete_the_record('shame.json', data['group_name'], data['shame_id'])
    await check_history_handler(callback, state)


@router.callback_query(filters.Admin(), F.data == 'negative_check')
async def positive_check_handler(callback: CallbackQuery, state: FSMContext):
    await check_history_handler(callback, state)


@router.callback_query(filters.CallbackAccess(), F.data == 'add_shame')
async def add_shame_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bot_message = await callback.bot.send_message(chat_id=callback.message.chat.id,
                                                  text=f'Выбрана группа: {data["group_name"]}\n'
                                                       f'Выбрано действие: Добавить позор\n'
                                                       f'Опишите ситуацию',
                                                  reply_to_message_id=data['start_message'].message_id,
                                                  reply_markup=ForceReply(selective=True)
                                                  )
    await state.update_data(message_access=bot_message.message_id)
    await callback.message.delete()
    await state.set_state(ShameData.description)


@router.message(filters.MessageAccess(), ShameData.description)
async def description_handler(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    delta = datetime.timedelta(hours=3, minutes=0)
    data = await state.update_data(message_datetime=(message.date + delta).strftime('%d.%m.%y %H:%M'))
    json_file.add_record_to_json('shame.json', data['group_name'], data['message_datetime'], data['description'])
    count = json_file.get_the_record_number('shame.json', data['group_name'])
    await message.reply(text=f'Для {data["group_name"]} добавлен позор №{count} от {data["message_datetime"]}\n\n')
    await state.clear()
