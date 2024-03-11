from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ForceReply
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app import json_file, filters, exceptions, keyboards, functions
from app.states import AdminData
from config import JSON_FILE_NAME

router = Router()


@router.callback_query(F.data == 'edit record', filters.CallbackAccessFilter(), filters.CallbackAdminFilter())
async def edit_record_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.reply('Ожидание отредактированной записи...', reply_markup=ForceReply(selective=True))
    await state.set_state(AdminData.edited_record_content)
    await callback.answer()


@router.message(AdminData.edited_record_content, filters.MessageAdminFilter())
async def edited_descriprion_handler(message: Message, state: FSMContext):
    if message.reply_to_message is not None and message.reply_to_message.from_user.id == message.bot.id:
        data = await state.update_data(edited_record_content=message.text)
        await json_file.edit_json_record(
            JSON_FILE_NAME, message.chat.id, data["group_name"], data["record_id"], data["edited_record_content"]
        )
        await message.reply('Запись отредактирована.')
        await state.clear()
    else:
        await message.answer('Процесс редактирования записи остановлен. Сообщение должно быть получено в виде ответа.')
        await state.set_state(state=None)


@router.message(Command('delete_message'), filters.MessageAdminFilter())
async def delete_message_handler(message: Message):
    try:
        await message.reply_to_message.delete()
    except AttributeError:
        await message.reply('Команду нужно вызывать ответом на сообщение.')


@router.callback_query(F.data == 'delete record', filters.CallbackAccessFilter(), filters.CallbackAdminFilter())
async def delete_record_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='Вы уверены, что хотите удалить эту запись?',
                                     reply_markup=keyboards.confirm_keyboard)
    await callback.answer()


@router.callback_query(
    F.data.in_({'confirm delete', 'cancel delete'}), filters.CallbackAccessFilter(), filters.CallbackAdminFilter())
async def confirm_deletion_handler(callback: CallbackQuery, state: FSMContext):
    result = callback.data
    data = await state.get_data()
    group_name = data["group_name"]
    record_id = data["record_id"]
    match result:
        case 'confirm delete':
            await json_file.delete_record(JSON_FILE_NAME, callback.message.chat.id, group_name, record_id)
            await callback.message.answer(f'Запись из группы "{group_name}" удалена.')
            await functions.edit_history_message(callback, state, group_name, record_id)
        case 'cancel delete':
            await functions.edit_history_message(callback, state, group_name, record_id)


@router.message(Command('create'), filters.MessageAdminFilter())
async def add_group_handler(message: Message):
    try:
        group_name = message.text.split(' ', 1)[1]
        await json_file.add_group_to_json(JSON_FILE_NAME, message.chat.id, group_name)
        await message.reply('Группа добавлена.')
    except (exceptions.GroupAlreadyExistsError, exceptions.GroupLimitExceededError) as error:
        await message.reply(str(error))
    except IndexError:
        await message.reply('Пример использования:\n<pre>/create название_группы</pre>')


@router.message(Command('delete_group'), filters.MessageAdminFilter())
async def delete_group_handler(message: Message):
    try:
        group_name = message.text.split(' ', 1)[1]
        await json_file.delete_group_from_json(JSON_FILE_NAME, message.chat.id, group_name)
        await message.reply('Группа удалена.')
    except exceptions.GroupNotFoundError as error:
        await message.reply(str(error))
    except IndexError:
        await message.reply('Пример использования:\n<pre>/delete_group название_группы</pre>')
