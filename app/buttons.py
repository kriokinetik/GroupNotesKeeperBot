from aiogram.types import InlineKeyboardButton

prev_record = InlineKeyboardButton(text='<', callback_data='prev record')
next_record = InlineKeyboardButton(text='>', callback_data='next record')

go_back = InlineKeyboardButton(text='Назад', callback_data='go back')

delete_record = InlineKeyboardButton(text='Удалить запись', callback_data='delete record')

confirm_button = InlineKeyboardButton(text='Удалить', callback_data='confirm delete')
cancel_button = InlineKeyboardButton(text='Отмена', callback_data='cancel delete')
