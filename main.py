import asyncio
import sys
import logging

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from aiogram.enums import ParseMode

from app import handlers, admin
from config import token


async def main():
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    await bot.set_my_commands([
        BotCommand(command='help', description='Список команд'),
        BotCommand(command='add', description='Добавить запись'),
        BotCommand(command='create', description='Создать группу'),
        BotCommand(command='history', description='Просмотреть историю'),
        BotCommand(command='delete_group', description='Удалить группу'),
        BotCommand(command='delete_message', description='Удалить сообщение')
    ])
    dp.include_routers(handlers.router, admin.router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
