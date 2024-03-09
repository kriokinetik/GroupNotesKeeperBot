from aiogram import Router
from aiogram.types import Message, ForceReply
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app import json_file, filters, exceptions
from app.states import AdminData
from config import JSON_FILE_NAME

router = Router()


@router.message(Command('edit'), filters.AdminFilter())
async def edit_record_handler(message: Message, state: FSMContext):
    try:
        _ = (await state.get_data())["record_id"]
        await message.reply('Отправьте исправленную запись.', reply_markup=ForceReply(selective=True))
        await state.set_state(AdminData.edited_record_content)
    except KeyError:
        await message.reply('Выберите запись, которую хотите отредактировать, через /history.')


@router.message(AdminData.edited_record_content, filters.AdminFilter())
async def edited_descriprion_handler(message: Message, state: FSMContext):
    data = await state.update_data(edited_record_content=message.text)
    await json_file.edit_json_record(
        JSON_FILE_NAME, message.chat.id, data["group_name"], data["record_id"], data["edited_record_content"]
    )
    await message.reply('Запись отредактирована.')
    await state.clear()


@router.message(Command('delete_message'), filters.AdminFilter())
async def delete_message_handler(message: Message, state: FSMContext):
    try:
        await message.reply_to_message.delete()
        await state.clear()
    except AttributeError:
        await message.reply('Команду нужно вызывать ответом на сообщение.')


@router.message(Command('delete_record'), filters.AdminFilter())
async def delete_record_handler(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        await json_file.delete_record(JSON_FILE_NAME, message.chat.id, data["group_name"], data["record_id"])
        await message.reply('Запись удалена.')
    except KeyError:
        await message.reply('Выберите запись, которую хотите удалить, через /history.')


@router.message(Command('create'), filters.AdminFilter())
async def add_group_handler(message: Message):
    try:
        group_name = message.text.split(' ', 1)[1]
        await json_file.add_group_to_json(JSON_FILE_NAME, message.chat.id, group_name)
        await message.reply('Группа добавлена.')
    except (exceptions.GroupAlreadyExistsError, exceptions.GroupLimitExceededError) as error:
        await message.reply(str(error))
    except IndexError:
        await message.reply('Пример использования:\n<pre>/create название_группы</pre>')


@router.message(Command('delete_group'), filters.AdminFilter())
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
