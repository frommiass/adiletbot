"""
Генерация и отправка саммари диалогов
"""

import logging
from datetime import datetime
from aiogram.types import Message
from aiogram.filters import Command

import config
import database
import llm

logger = logging.getLogger(__name__)

# Активные чаты (где бот работает)
active_chats = set()


async def cmd_summary(message: Message):
    """Команда /summary - показать саммари за сегодня"""
    messages = await database.get_today_messages(message.chat.id)
    
    if not messages:
        await message.answer("Сегодня пока не было сообщений")
        return
    
    summary = await generate_simple_summary(messages, message.chat.id)
    await message.answer(summary)


async def cmd_stats(message: Message):
    """Команда /stats - показать статистику за день"""
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


async def generate_simple_summary(messages, chat_id: int):
    """Генерирует саммари с помощью GigaChat"""
    summary = f"📝 Саммари за {datetime.now().strftime('%d.%m.%Y')}\n\n"
    
    # Статистика
    user_stats = {}
    for username, first_name, text, timestamp in messages:
        name = username or first_name or "Аноним"
        user_stats[name] = user_stats.get(name, 0) + 1
    
    summary += f"💬 Всего сообщений: {len(messages)}\n"
    summary += f"👥 Участников: {len(user_stats)}\n\n"
    
    # Умное саммари через GigaChat
    summary += "🤖 Что обсуждали:\n"
    smart_summary = await llm.generate_smart_summary(messages)
    summary += smart_summary + "\n\n"
    
    # Топ активных
    summary += "🔥 Топ активных:\n"
    sorted_users = sorted(user_stats.items(), key=lambda x: x[1], reverse=True)[:3]
    for name, count in sorted_users:
        summary += f"• {name} ({count})\n"
    
    # Статистика по реакциям
    try:
        total_top, emoji_tops = await database.get_reaction_stats(chat_id, period_days=1)
        if total_top:
            summary += "\n🏆 Топ по реакциям:\n"
            for name, count in total_top[:3]:
                display = name or "Аноним"
                summary += f"• {display} ({count})\n"
    except Exception as e:
        logger.warning(f"Cannot append reaction stats: {e}")

    return summary


async def send_daily_summary(bot):
    """Отправляет ежедневное саммари во все активные чаты"""
    for chat_id in active_chats:
        try:
            messages = await database.get_today_messages(chat_id)
            if messages:
                summary = await generate_simple_summary(messages, chat_id)
                await bot.send_message(chat_id, summary)
        except Exception as e:
            logger.error(f"Error sending summary to {chat_id}: {e}")


def register_summary_handlers(dp):
    """Регистрируем обработчики саммари"""
    dp.message(Command("summary"))(cmd_summary)
    dp.message(Command("stats"))(cmd_stats)
