from aiogram.types import InlineKeyboardButton

prev_record = InlineKeyboardButton(text='<', callback_data='prev_record')
next_record = InlineKeyboardButton(text='>', callback_data='next_record')
go_back = InlineKeyboardButton(text='Назад', callback_data='go_back')
