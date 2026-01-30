"""
Mini App интеграция
"""

import logging
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command

import config

logger = logging.getLogger(__name__)


async def cmd_app(message: Message):
    """Команда /app - показать кнопку для открытия Mini App"""
    # URL твоего сервера где крутится webapp.py
    # Замени на свой домен!
    webapp_url = getattr(config, 'WEBAPP_URL', "https://your-domain.com")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📊 Открыть статистику",
            web_app=WebAppInfo(url=f"{webapp_url}?start_param={message.chat.id}")
        )]
    ])
    
    await message.answer(
        "Нажми на кнопку, чтобы открыть интерактивную статистику чата:",
        reply_markup=keyboard
    )


def register_miniapp_handlers(dp):
    """Регистрируем обработчики Mini App"""
    dp.message(Command("app"))(cmd_app)
