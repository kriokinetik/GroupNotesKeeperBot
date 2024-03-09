from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ForceReply
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app import json_file, filters, exceptions, keyboards
from app.handlers import show_history_handler, edit_history_message
from app.states import AdminData
from config import JSON_FILE_NAME

router = Router()


@router.message(Command('edit'), filters.MessageAdminFilter())
async def edit_record_handler(message: Message, state: FSMContext):
    try:
        _ = (await state.get_data())["record_id"]
        await message.reply('Отправьте исправленную запись.', reply_markup=ForceReply(selective=True))
        await state.set_state(AdminData.edited_record_content)
    except KeyError:
        await message.reply('Выберите запись, которую хотите отредактировать, через /history.')


@router.message(AdminData.edited_record_content, filters.MessageAdminFilter())
async def edited_descriprion_handler(message: Message, state: FSMContext):
    data = await state.update_data(edited_record_content=message.text)
    await json_file.edit_json_record(
        JSON_FILE_NAME, message.chat.id, data["group_name"], data["record_id"], data["edited_record_content"]
    )
    await message.reply('Запись отредактирована.')
    await state.clear()


@router.message(Command('delete_message'), filters.MessageAdminFilter())
async def delete_message_handler(message: Message, state: FSMContext):
    try:
        await message.reply_to_message.delete()
        await state.clear()
    except AttributeError:
        await message.reply('Команду нужно вызывать ответом на сообщение.')


@router.message(Command('delete_record'), filters.MessageAdminFilter())
async def show_admin_history_handler(message: Message, state: FSMContext):
    await state.update_data(interaction_right=message.from_user.id)
    await show_history_handler(message, state, root=True)


@router.callback_query(F.data == 'delete record', filters.CallbackAccessFilter(), filters.CallbackAdminFilter())
async def delete_record_handler(callback: CallbackQuery):
    await callback.message.edit_text(text='Вы уверены, что хотите удалить эту запись?',
                                     reply_markup=keyboards.confirm_keyboard)


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
            await edit_history_message(callback, group_name, record_id, root=True)
        case 'cancel delete':
            await edit_history_message(callback, group_name, record_id + 1, root=True)


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
        await message.reply(
            'Пример использования:\n<pre>/delete_group название_группы</pre>'
        )
