from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from app import buttons, json_file


async def get_group_selection_keyboard(message: Message, file_name: str) -> InlineKeyboardMarkup:
    chat_id = message.chat.id
    groups = await json_file.get_groups(file_name, chat_id)
    buttons = [
        [InlineKeyboardButton(text=groups[i], callback_data=f'group_{groups[i]}'),
         InlineKeyboardButton(text=groups[i + 1], callback_data=f'group_{groups[i + 1]}')]
        for i in range(0, len(groups), 2)
        if i + 1 < len(groups)
    ]
    # Если количество групп нечетное, добавляем последнюю кнопку
    if len(groups) % 2 != 0:
        buttons.append([InlineKeyboardButton(text=groups[-1], callback_data=f'group_{groups[-1]}')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


check_history = InlineKeyboardMarkup(
    inline_keyboard=[
        [buttons.prev_record, buttons.next_record],
        [buttons.go_back]
    ]
)

go_back_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [buttons.go_back]
    ]
)
