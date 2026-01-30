"""
Простые команды бота: /start, /watermark, /reactions
Обработка текста и реакций
"""

import logging
from aiogram import F, Bot
from aiogram.types import Message, MessageReactionUpdated
from aiogram.filters import Command
import aiosqlite

import database
import summary  # Для active_chats
import photo_news_handler

logger = logging.getLogger(__name__)


async def cmd_start(message: Message):
    """Команда /start"""
    await message.answer(
        "Привет! Я буду собирать сообщения из чата и делать саммари в конце дня.\n\n"
        "Команды:\n"
        "/summary - показать саммари за сегодня\n"
        "/stats - статистика за день\n"
        "/reactions - топ по реакциям\n"
        "/app - открыть Mini App со статистикой\n"
        "/watermark - добавить водяной знак на фото (отправь фото после команды)"
    )
    if message.chat.type in ['group', 'supergroup']:
        summary.active_chats.add(message.chat.id)


async def cmd_watermark(message: Message):
    """Команда /watermark - инструкция по добавлению водяного знака"""
    await message.answer(
        "📸 Добавление водяного знака\n\n"
        "Просто отправь мне любое фото, и я добавлю на него повторяющийся водяной знак!\n\n"
        "Водяной знак будет по диагонали по всему изображению."
    )


async def cmd_reactions(message: Message):
    """Команда /reactions - статистика по реакциям"""
    total_top, emoji_tops = await database.get_reaction_stats(message.chat.id, period_days=1)
    
    if not total_top:
        await message.answer("📊 Реакций пока нет")
        return
    
    result = "🏆 ТОП ПО РЕАКЦИЯМ (всего):\n"
    for idx, (username, count) in enumerate(total_top, 1):
        name = username or "Аноним"
        result += f"{idx}. {name} - {count}\n"
    
    # Топы по каждой реакции
    for emoji, top in sorted(emoji_tops.items(), key=lambda x: sum(c for _, c in x[1]), reverse=True):
        result += f"\nТоп {emoji}:\n"
        for idx, (username, count) in enumerate(top, 1):
            name = username or "Аноним"
            result += f"{idx}. {name} - {count}\n"
    
    await message.answer(result)


async def handle_group_text(message: Message):
    """Сохраняем текстовые сообщения из группы"""
    # ВРЕМЕННО: логируем chat_id и thread_id для настройки
    logger.info(f"📍 chat_id={message.chat.id}, chat_title='{message.chat.title}', thread_id={message.message_thread_id}")
    
    await database.save_message(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        text=message.text,
        message_id=message.message_id,
        has_photo=False
    )


async def handle_group_photo(message: Message):
    """Сохраняем фото в БД (для Photo News Forwarder) БЕЗ водяного знака"""
    # Игнорируем сообщения от ботов (чтобы не учитывать пересланные из Photo News)
    if message.from_user.is_bot:
        logger.debug(f"Ignoring photo from bot {message.from_user.username}")
        return
    
    # Игнорируем пересланные сообщения
    if message.forward_date:
        logger.debug(f"Ignoring forwarded message")
        return
    
    caption = message.caption or ""
    logger.info(f"📸 PHOTO saved: chat={message.chat.id}, msg={message.message_id}, user={message.from_user.username}")
    
    await database.save_message(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        text=caption,
        message_id=message.message_id,
        has_photo=True  # ← ВАЖНО для Photo News!
    )


async def handle_new_member(message: Message):
    """Приветствие новых участников чата"""
    for new_member in message.new_chat_members:
        # Пропускаем ботов
        if new_member.is_bot:
            continue
        
        # Формируем имя
        first_name = new_member.first_name or ""
        last_name = new_member.last_name or ""
        username = new_member.username
        
        name_parts = []
        if first_name:
            name_parts.append(first_name)
        if last_name:
            name_parts.append(last_name)
        
        display_name = " ".join(name_parts) if name_parts else "новый участник"
        
        # Формируем приветствие
        if username:
            greeting = f"👋 Добро пожаловать, {display_name} (@{username})!"
        else:
            greeting = f"👋 Добро пожаловать, {display_name}!"
        
        await message.answer(greeting)


async def handle_group_photo(message: Message):
    """Сохраняем фото из группы (для Photo News)"""
    caption = message.caption or ""
    logger.info(f"📸 PHOTO in chat_id={message.chat.id}, message_id={message.message_id}, from={message.from_user.username}")
    
    await database.save_message(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        text=caption,
        message_id=message.message_id,
        has_photo=True  # ← ВАЖНО!
    )


async def handle_reaction(reaction: MessageReactionUpdated, bot):
    """Обрабатываем реакции на сообщения"""
    try:
        # Получаем информацию о сообщении из БД
        async with aiosqlite.connect('messages.db') as db:
            async with db.execute('''
                SELECT user_id, username 
                FROM messages 
                WHERE message_id = ? AND chat_id = ?
            ''', (reaction.message_id, reaction.chat.id)) as cursor:
                row = await cursor.fetchone()
        
        if not row:
            return  # Сообщение не найдено в БД
        
        author_user_id, author_username = row
        
        # Определяем какие реакции добавлены, какие удалены
        # Поддерживаем как обычные эмодзи (emoji), так и кастомные (custom_emoji_id)
        def get_reaction_id(r):
            """Получаем ID реакции - либо emoji, либо custom_emoji_id"""
            if hasattr(r, 'emoji') and r.emoji:
                return r.emoji
            elif hasattr(r, 'custom_emoji_id') and r.custom_emoji_id:
                return f"custom:{r.custom_emoji_id}"
            return None
        
        old_reactions = {get_reaction_id(r) for r in reaction.old_reaction if get_reaction_id(r)}
        new_reactions = {get_reaction_id(r) for r in reaction.new_reaction if get_reaction_id(r)}
        
        # Добавленные реакции
        added_reactions = new_reactions - old_reactions
        for reaction_id in added_reactions:
            await database.save_reaction(
                message_id=reaction.message_id,
                author_user_id=author_user_id,
                author_username=author_username,
                reaction_emoji=reaction_id,
                reactor_user_id=reaction.user.id
            )
        
        # Удаленные реакции
        removed_reactions = old_reactions - new_reactions
        for reaction_id in removed_reactions:
            await database.delete_reaction(
                message_id=reaction.message_id,
                reactor_user_id=reaction.user.id,
                reaction_emoji=reaction_id
            )
        
        # Проверяем нужно ли пересылать в Photo News
        await photo_news_handler.handle_reaction_for_news(reaction, bot)
                
    except Exception as e:
        logger.error(f"Error handling reaction: {e}")


def register_command_handlers(dp, bot):
    """Регистрируем обработчики команд"""
    dp.message(Command("start"))(cmd_start)
    dp.message(Command("watermark"))(cmd_watermark)
    dp.message(Command("reactions"))(cmd_reactions)
    
    # Обработка текста в группах
    dp.message(F.chat.type.in_(['group', 'supergroup']) & F.text)(handle_group_text)
    
    # Обработка ФОТО в группах (для Photo News - БЕЗ водяного знака!)
    dp.message(F.chat.type.in_(['group', 'supergroup']) & F.photo)(handle_group_photo)
    
    # Приветствие новых участников
    dp.message(F.chat.type.in_(['group', 'supergroup']) & F.new_chat_members)(handle_new_member)
    
    # Обработка реакций - правильная регистрация с передачей bot
    @dp.message_reaction()
    async def _handle_reaction(reaction: MessageReactionUpdated, bot: Bot):
        await handle_reaction(reaction, bot)