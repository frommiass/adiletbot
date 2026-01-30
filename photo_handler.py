"""
Автоматическая пересылка популярных фото в чат "Фото Новости"
Логика: набрало 5+ лайков → скопировали с подписью автора → забыли
"""

import logging
from aiogram.types import MessageReactionUpdated
import aiosqlite

import config
import database

logger = logging.getLogger(__name__)


async def handle_reaction_for_news(reaction: MessageReactionUpdated, bot):
    """
    Обрабатываем реакцию и проверяем нужно ли пересылать в новости
    """
    # Проверка что фича включена
    if not getattr(config, 'PHOTO_NEWS_ENABLED', False):
        logger.debug("Photo News disabled")
        return
    
    # Проверка что есть целевой чат
    target_chat_id = getattr(config, 'PHOTO_NEWS_TARGET_CHAT_ID', None)
    if not target_chat_id:
        logger.debug("No target chat configured")
        return
    
    # Проверка что это нужный чат (если указан список)
    source_chats = getattr(config, 'PHOTO_NEWS_SOURCE_CHATS', [])
    if source_chats and reaction.chat.id not in source_chats:
        logger.debug(f"Chat {reaction.chat.id} not in source list")
        return
    
    try:
        logger.info(f"🔔 Reaction on message {reaction.message_id} in chat {reaction.chat.id}")
        
        # 1. Пересчитываем количество реакций для этого сообщения
        await database.update_message_reactions(reaction.chat.id, reaction.message_id)
        
        # 2. Проверяем нужно ли пересылать
        should_forward = await database.should_forward_message(reaction.chat.id, reaction.message_id)
        
        logger.info(f"📊 Should forward: {should_forward}")
        
        if should_forward:
            # 3. Копируем сообщение с подписью автора
            await copy_photo_with_author(
                bot=bot,
                chat_id=reaction.chat.id,
                message_id=reaction.message_id,
                target_chat_id=target_chat_id
            )
            
            logger.info(f"✅ Posted message {reaction.message_id} from {reaction.chat.id} to {target_chat_id}")
            
    except Exception as e:
        logger.error(f"Error in handle_reaction_for_news: {e}", exc_info=True)


async def copy_photo_with_author(bot, chat_id: int, message_id: int, target_chat_id: int):
    """
    Копируем популярное фото в целевой топик с подписью автора
    """
    try:
        # Получаем информацию об авторе из БД
        message_info = await database.get_message_info(chat_id, message_id)
        if not message_info:
            logger.error(f"Message {message_id} not found in DB")
            return
        
        user_id, username, has_photo, total_reactions, is_forwarded = message_info
        
        # Получаем thread_id из конфига
        target_thread_id = getattr(config, 'PHOTO_NEWS_TARGET_THREAD_ID', None)
        
        # Получаем оригинальное сообщение
        original_message = await bot.forward_message(
            chat_id=bot.id,  # Пересылаем себе временно
            from_chat_id=chat_id,
            message_id=message_id
        )
        
        # Формируем подпись автора
        # Получаем имя из БД
        async with aiosqlite.connect('messages.db') as db:
            async with db.execute('''
                SELECT first_name, username, text 
                FROM messages 
                WHERE message_id = ? AND chat_id = ?
            ''', (message_id, chat_id)) as cursor:
                row = await cursor.fetchone()
        
        if row:
            first_name, username, original_caption = row
            
            # Формируем имя автора
            author_name = first_name or "Неизвестный автор"
            
            # Формируем подпись
            if username:
                author_caption = f"Автор: {author_name}\n@{username}"
            else:
                author_caption = f"Автор: {author_name}"
            
            # Добавляем оригинальную подпись если была
            if original_caption:
                final_caption = f"{original_caption}\n\n{author_caption}"
            else:
                final_caption = author_caption
            
            # Отправляем фото с подписью автора
            if original_message.photo:
                await bot.send_photo(
                    chat_id=target_chat_id,
                    photo=original_message.photo[-1].file_id,
                    caption=final_caption,
                    message_thread_id=target_thread_id
                )
            
            logger.info(f"✅ Posted photo to thread {target_thread_id} with author caption")
        
        # Удаляем временное сообщение
        await bot.delete_message(chat_id=bot.id, message_id=original_message.message_id)
        
        # Отмечаем в БД что сообщение переслано
        await database.mark_as_forwarded(chat_id, message_id)
        
    except Exception as e:
        logger.error(f"❌ Error posting photo {message_id}: {e}", exc_info=True)