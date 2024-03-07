from aiogram import Router
from aiogram.types import Message, ForceReply
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app import json_file, filters, exceptions
from app.states import AdminData

router = Router()


@router.message(Command('edit'), filters.MessageAccess(), filters.Admin())
async def edit_record_handler(message: Message, state: FSMContext):
    await message.reply(text='Отправьте исправленную запись.',
                        reply_markup=ForceReply(selective=True))
    await state.set_state(AdminData.edited_description)


@router.message(AdminData.edited_description, filters.Admin())
async def edited_descriprion_handler(message: Message, state: FSMContext):
    data = await state.update_data(edited_description=message.text)
    json_file.edit_json_record('shame.json', data['group_name'], data['shame_id'], data['edited_description'])
    await message.reply(text='Запись отредактирована.')
    await state.clear()


@router.message(Command('delete_message'), filters.Admin())
async def delete_message_handler(message: Message, state: FSMContext):
    await message.reply_to_message.delete()
    await state.clear()


@router.message(Command('delete_record'), filters.Admin())
async def delete_record_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    json_file.delete_the_record('shame.json', data['group_name'], data['shame_id'])
    await message.reply(text='Запись удалена.')


@router.message(Command('add_group'), filters.Admin())
async def add_group_handler(message: Message):
    group_name = message.text.split(' ', 1)[1]
    try:
        json_file.add_group_to_json('shame.json', group_name)
        await message.reply(text='Группа добавлена.')
    except (exceptions.GroupAlreadyExistsError, exceptions.GroupLimitExceededError) as error:
        await message.reply(text=str(error))


@router.message(Command('delete_group'), filters.Admin())
async def delete_group_handler(message: Message):
    group_name = message.text.split(' ', 1)[1]
    try:
        json_file.delete_group_from_json('shame.json', group_name)
        await message.reply(text='Группа удалена.')
    except exceptions.GroupNotFoundError as error:
        await message.reply(text=str(error))
