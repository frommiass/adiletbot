"""
Главный файл бота - запуск и регистрация handlers
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
import database
import summary
import commands
# import photo_handler  # ОТКЛЮЧЕНО
import miniapp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём бота
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


async def main():
    """Главная функция - инициализация и запуск бота"""
    
    # Инициализация базы данных
    await database.init_db()
    await database.init_reactions_table()
    
    # Восстанавливаем список активных чатов после перезапуска
    summary.active_chats.update(await database.get_active_chats())
    logger.info(f"Restored {len(summary.active_chats)} active chats")
    
    # Настраиваем планировщик для ежедневного саммари
    scheduler = AsyncIOScheduler()
    hour, minute = map(int, config.SUMMARY_TIME.split(':'))
    scheduler.add_job(
        lambda: summary.send_daily_summary(bot),
        'cron',
        hour=hour,
        minute=minute
    )
    scheduler.start()
    
    # Регистрируем все handlers
    commands.register_command_handlers(dp, bot)
    summary.register_summary_handlers(dp)
    # photo_handler.register_photo_handlers(dp, bot)  # ОТКЛЮЧЕНО: удаление фото и логотип
    miniapp.register_miniapp_handlers(dp)
    
    # Photo News Forwarder интегрирован в commands.handle_reaction
    if getattr(config, 'PHOTO_NEWS_ENABLED', False):
        logger.info("Photo News Forwarder enabled")
    
    logger.info("Bot started")
    
    # Запускаем polling
    await dp.start_polling(bot, allowed_updates=["message", "message_reaction"])


if __name__ == '__main__':
    asyncio.run(main())