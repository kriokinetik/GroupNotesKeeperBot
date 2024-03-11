from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import buttons
from utils import json_utils


async def get_group_selection_keyboard(message: Message, file_name: str) -> InlineKeyboardMarkup:
    chat_id = message.chat.id
    groups = await json_utils.get_groups(file_name, chat_id)

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

    if admin:
        keyboard.append([buttons.edit_record, buttons.delete_record])

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
