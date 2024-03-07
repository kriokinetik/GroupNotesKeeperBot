import asyncio
import sys
import logging

from aiogram import Dispatcher, Bot
from aiogram.types import BotCommand

from app import handlers, admin
from config import token


async def main():
    bot = Bot(token=token)
    dp = Dispatcher()
    await bot.set_my_commands([
        BotCommand(command='help', description='Список команд'),
        BotCommand(command='add', description='Добавить запись'),
        BotCommand(command='history', description='Просмотреть историю'),
        BotCommand(command='edit', description='Отредактировать запись'),
        BotCommand(command='delete_record', description='Удалить запись'),
        BotCommand(command='add_group', description='Добавить группу'),
        BotCommand(command='delete_group', description='Удалить группу'),
        BotCommand(command='delete_message', description='Удалить сообщение')
    ])
    dp.include_routers(handlers.router, admin.router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
