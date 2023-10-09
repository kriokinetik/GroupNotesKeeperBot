from aiogram.types import InlineKeyboardMarkup

from app import buttons


group_selection = InlineKeyboardMarkup(
    inline_keyboard=[
        [buttons.bei2202, buttons.pozorniki],
        [buttons.delete_message]
    ]
)

action_selection = InlineKeyboardMarkup(
    inline_keyboard=[
        [buttons.add_shame, buttons.check_history],
        [buttons.home]
    ]
)

go_home = InlineKeyboardMarkup(
    inline_keyboard=[
        [buttons.home]
    ]
)

check_history = InlineKeyboardMarkup(
    inline_keyboard=[
        [buttons.back, buttons.forward],
        [buttons.home]
    ]
)
