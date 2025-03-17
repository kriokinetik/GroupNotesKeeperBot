from aiogram import Router, Bot
from aiogram.types import ChatMemberUpdated
from aiogram.filters import JOIN_TRANSITION, ChatMemberUpdatedFilter

from utils import json_utils
from config import JSON_FILE_NAME

router = Router()


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def on_user_join(event: ChatMemberUpdated, bot: Bot):
    await json_utils.start_json_session(JSON_FILE_NAME, event.chat.id)
    await bot.send_message(
        chat_id=event.chat.id,
        text='Привет! Я бот для управления записями по группам. С моей помощью ты можешь создавать группы и '
             'добавлять записи к каждой из них. Позже ты сможешь легко просматривать записи по каждой группе.\n\n'
             'Чтобы начать, используй команду /create для создания новой группы или /add для добавления '
             'записи к уже существующей.\n\n'
             'Для получения справки по командам: /help'
    )
