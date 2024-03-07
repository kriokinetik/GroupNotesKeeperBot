from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app import buttons, json_file


def get_group_selection_keyboard(file_name: str) -> InlineKeyboardMarkup:
    groups = json_file.get_the_groups(file_name)
    buttons = []
    for name in groups:
        buttons.append([InlineKeyboardButton(text=name, callback_data=f'group_{name}')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


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
