import datetime
import os

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ForceReply
from aiogram.fsm.context import FSMContext

from main import bot
from app import keyboards, json_file
from app.states import ShameData

router = Router()


@router.message(F.text.in_({'/start', '/shame'}))
async def bot_call_handler(message: Message, state: FSMContext):
    await state.update_data(message_id=message.message_id)
    await message.reply(text='Выберите группу:',
                        reply_markup=keyboards.group_selection)


@router.callback_query(F.data == 'home')
async def home_handler(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_state()
    if state_data is not None:
        await state.set_state(state=None)
    await callback.message.edit_text(text='Выберите группу:',
                                     reply_markup=keyboards.group_selection)


@router.callback_query(F.data == 'delete_message')
async def delete_message_handler(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_state()
    if state_data is not None:
        await state.set_state(state=None)
    await callback.message.delete()


@router.callback_query(F.data.startswith('group'))
async def pozorniki_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.update_data(group_name=callback.data[6:])
    await callback.message.edit_text(text=f'Выбрана группа: {data["group_name"]}\n'
                                          f'Выберите действие:',
                                     reply_markup=keyboards.action_selection)


@router.callback_query(F.data == 'check_history')
async def check_history_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if os.path.exists('shame.json'):
        await state.update_data(shame_id=0)
        data = await state.get_data()
        shame_data = json_file.get_the_shame_data('shame.json', data['group_name'], data['shame_id'])
        await callback.message.edit_text(text=f'Выбрана группа: {data["group_name"]}\n'
                                              f'Выбрано действие: история\n\n'
                                              f'{shame_data}',
                                         reply_markup=keyboards.check_history)
    else:
        await callback.message.edit_text(text=f'Выбрана группа: {data["group_name"]}\n'
                                              f'Выбрано действие: история\n'
                                              f'Вы ещё не записали ни одного позора',
                                         reply_markup=keyboards.go_home)


@router.callback_query(F.data == 'back')
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
                                          f'Выбрано действие: история\n\n'
                                          f'{shame_data}',
                                     reply_markup=keyboards.check_history)


@router.callback_query(F.data == 'forward')
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
                                          f'Выбрано действие: история\n\n'
                                          f'{shame_data}',
                                     reply_markup=keyboards.check_history)


@router.callback_query(F.data == 'add_shame')
async def add_shame_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await bot.send_message(chat_id=callback.message.chat.id,
                           text=f'Выбрана группа: {data["group_name"]}\n'
                                f'Выбрано действие: +позор\n'
                                f'Опишите ситуацию',
                           reply_to_message_id=data['message_id'],
                           reply_markup=ForceReply(selective=True)
                           )
    await callback.message.delete()
    await state.set_state(ShameData.description)


@router.message(ShameData.description)
async def description_handler(message: Message, state: FSMContext):
    if message.reply_to_message is not None:
        await state.update_data(description=message.text)
        delta = datetime.timedelta(hours=3, minutes=0)
        data = await state.update_data(message_datetime=(message.date + delta).strftime('%d.%m.%y %H:%M'))
        json_file.add_record_to_json('shame.json', data['group_name'], data['message_datetime'], data['description'])
        count = json_file.get_the_record_number('shame.json', data['group_name'])
        await message.reply(text=f'Для {data["group_name"]} добавлен позор №{count} от {data["message_datetime"]}\n\n')
        await state.set_state(state=None)
