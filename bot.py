import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
import database


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


active_chats = set()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я буду собирать сообщения из чата и делать саммари в конце дня.\n\n"
        "Команды:\n"
        "/summary - показать саммари за сегодня\n"
        "/stats - статистика за день"
    )
    if message.chat.type in ['group', 'supergroup']:
        active_chats.add(message.chat.id)


@dp.message(Command("summary"))
async def cmd_summary(message: Message):
    messages = await database.get_today_messages(message.chat.id)
    
    if not messages:
        await message.answer("Сегодня пока не было сообщений")
        return
    
    summary = generate_simple_summary(messages)
    await message.answer(summary)


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    messages = await database.get_today_messages(message.chat.id)
    
    if not messages:
        await message.answer("Сегодня пока не было сообщений")
        return
    
    user_stats = {}
    for username, first_name, text, timestamp in messages:
        name = username or first_name or "Аноним"
        user_stats[name] = user_stats.get(name, 0) + 1
    
    stats_text = f"📊 Статистика за сегодня:\n\n"
    stats_text += f"Всего сообщений: {len(messages)}\n"
    stats_text += f"Участников: {len(user_stats)}\n\n"
    stats_text += "Топ активных:\n"
    
    sorted_users = sorted(user_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    for name, count in sorted_users:
        stats_text += f"• {name}: {count} сообщений\n"
    
    await message.answer(stats_text)


@dp.message(F.chat.type.in_(['group', 'supergroup']))
async def handle_group_message(message: Message):
    if message.text:
        await database.save_message(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            text=message.text,
            message_id=message.message_id
        )


def generate_simple_summary(messages):
    summary = f"📝 Саммари за {datetime.now().strftime('%d.%m.%Y')}\n\n"
    summary += f"💬 Всего сообщений: {len(messages)}\n\n"
    
    user_stats = {}
    for username, first_name, text, timestamp in messages:
        name = username or first_name or "Аноним"
        user_stats[name] = user_stats.get(name, 0) + 1
    
    summary += "👥 Активные участники:\n"
    sorted_users = sorted(user_stats.items(), key=lambda x: x[1], reverse=True)[:3]
    for name, count in sorted_users:
        summary += f"• {name} ({count})\n"
    
    summary += f"\n⏰ Первое сообщение: {messages[0][3]}\n"
    summary += f"⏰ Последнее: {messages[-1][3]}\n"
    
    return summary


async def send_daily_summary():
    for chat_id in active_chats:
        try:
            messages = await database.get_today_messages(chat_id)
            if messages:
                summary = generate_simple_summary(messages)
                await bot.send_message(chat_id, summary)
        except Exception as e:
            logger.error(f"Error sending summary to {chat_id}: {e}")


async def main():
    await database.init_db()
    
    scheduler = AsyncIOScheduler()
    hour, minute = map(int, config.SUMMARY_TIME.split(':'))
    scheduler.add_job(send_daily_summary, 'cron', hour=hour, minute=minute)
    scheduler.start()
    
    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())


