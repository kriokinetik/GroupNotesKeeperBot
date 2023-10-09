import asyncio
import sys
import logging

from aiogram import Dispatcher, Bot

from app import handlers
from config import token

bot = Bot(token=token)


async def main():
    dp = Dispatcher()
    dp.include_routers(handlers.router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
