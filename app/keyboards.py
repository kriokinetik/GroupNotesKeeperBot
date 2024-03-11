from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from app import buttons, json_file


async def get_group_selection_keyboard(message: Message, file_name: str) -> InlineKeyboardMarkup:
    chat_id = message.chat.id
    groups = await json_file.get_groups(file_name, chat_id)

    keyboard = [
        [InlineKeyboardButton(text=groups[i], callback_data=f'group_{groups[i]}'),
         InlineKeyboardButton(text=groups[i + 1], callback_data=f'group_{groups[i + 1]}')]
        for i in range(0, len(groups), 2)
        if i + 1 < len(groups)
    ]

    # Если количество групп нечетное, добавляем последнюю кнопку
    if len(groups) % 2 != 0:
        keyboard.append([InlineKeyboardButton(text=groups[-1], callback_data=f'group_{groups[-1]}')])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def get_navigate_record_keyboard(admin: bool) -> InlineKeyboardMarkup:
    keyboard = [
        [buttons.prev_record, buttons.next_record],
        [buttons.go_back]
    ]

    # Если вызвана команда /delete_record, добавляем кнопку "Удалить запись"
    if admin:
        keyboard.append([buttons.delete_record, buttons.edit_record])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


go_back_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [buttons.go_back]
    ]
)

confirm_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [buttons.confirm_button],
        [buttons.cancel_button]
    ]
)
