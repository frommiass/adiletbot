import aiosqlite
from datetime import datetime
import config


async def init_db():
    async with aiosqlite.connect('messages.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                text TEXT,
                timestamp DATETIME,
                message_id INTEGER,
                has_photo BOOLEAN DEFAULT 0,
                total_reactions INTEGER DEFAULT 0,
                is_forwarded BOOLEAN DEFAULT 0,
                forwarded_at DATETIME
            )
        ''')
        await db.commit()


async def save_message(chat_id, user_id, username, first_name, text, message_id, has_photo=False):
    async with aiosqlite.connect('messages.db') as db:
        await db.execute('''
            INSERT INTO messages (chat_id, user_id, username, first_name, text, timestamp, message_id, has_photo, total_reactions, is_forwarded)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
        ''', (chat_id, user_id, username, first_name, text, datetime.now(), message_id, has_photo))
        await db.commit()


async def get_today_messages(chat_id):
    async with aiosqlite.connect('messages.db') as db:
        async with db.execute('''
            SELECT username, first_name, text, timestamp 
            FROM messages 
            WHERE chat_id = ? AND date(timestamp) = date('now')
            ORDER BY timestamp
        ''', (chat_id,)) as cursor:
            return await cursor.fetchall()


async def get_active_chats():
    """Получить список всех чатов где есть сообщения"""
    async with aiosqlite.connect('messages.db') as db:
        async with db.execute('SELECT DISTINCT chat_id FROM messages') as cursor:
            rows = await cursor.fetchall()
            return {row[0] for row in rows}


async def init_reactions_table():
    """Создать таблицу для реакций"""
    async with aiosqlite.connect('messages.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                author_user_id INTEGER,
                author_username TEXT,
                reaction_emoji TEXT,
                reactor_user_id INTEGER,
                timestamp DATETIME,
                UNIQUE(message_id, reactor_user_id, reaction_emoji)
            )
        ''')
        await db.commit()


async def save_reaction(message_id, author_user_id, author_username, reaction_emoji, reactor_user_id):
    """Сохранить реакцию (или обновить если уже есть)"""
    async with aiosqlite.connect('messages.db') as db:
        await db.execute('''
            INSERT OR REPLACE INTO reactions (message_id, author_user_id, author_username, reaction_emoji, reactor_user_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (message_id, author_user_id, author_username, reaction_emoji, reactor_user_id, datetime.now()))
        await db.commit()


async def delete_reaction(message_id, reactor_user_id, reaction_emoji):
    """Удалить реакцию когда пользователь убирает её"""
    async with aiosqlite.connect('messages.db') as db:
        await db.execute('''
            DELETE FROM reactions 
            WHERE message_id = ? AND reactor_user_id = ? AND reaction_emoji = ?
        ''', (message_id, reactor_user_id, reaction_emoji))
        await db.commit()


async def get_reaction_stats(chat_id, period_days=1):
    """Получить статистику по реакциям"""
    async with aiosqlite.connect('messages.db') as db:
        # Общий топ по всем реакциям
        async with db.execute('''
            SELECT r.author_username, COUNT(*) as reaction_count
            FROM reactions r
            JOIN messages m ON r.message_id = m.message_id
            WHERE m.chat_id = ? 
            AND datetime(r.timestamp) >= datetime('now', '-' || ? || ' days')
            GROUP BY r.author_user_id, r.author_username
            ORDER BY reaction_count DESC
            LIMIT 10
        ''', (chat_id, period_days)) as cursor:
            total_top = await cursor.fetchall()
        
        # Топ по каждой уникальной реакции
        async with db.execute('''
            SELECT DISTINCT reaction_emoji
            FROM reactions r
            JOIN messages m ON r.message_id = m.message_id
            WHERE m.chat_id = ?
            AND datetime(r.timestamp) >= datetime('now', '-' || ? || ' days')
        ''', (chat_id, period_days)) as cursor:
            emojis = await cursor.fetchall()
        
        emoji_tops = {}
        for (emoji,) in emojis:
            async with db.execute('''
                SELECT r.author_username, COUNT(*) as count
                FROM reactions r
                JOIN messages m ON r.message_id = m.message_id
                WHERE m.chat_id = ? 
                AND r.reaction_emoji = ?
                AND datetime(r.timestamp) >= datetime('now', '-' || ? || ' days')
                GROUP BY r.author_user_id, r.author_username
                ORDER BY count DESC
                LIMIT 10
            ''', (chat_id, emoji, period_days)) as cursor:
                emoji_tops[emoji] = await cursor.fetchall()
        
        return total_top, emoji_tops


# ========================================
# ФУНКЦИИ ДЛЯ PHOTO NEWS FORWARDER
# ========================================

async def update_message_reactions(chat_id, message_id):
    """
    Пересчитать количество реакций для сообщения
    """
    async with aiosqlite.connect('messages.db') as db:
        # Считаем количество реакций
        async with db.execute('''
            SELECT COUNT(*) 
            FROM reactions 
            WHERE message_id = ?
        ''', (message_id,)) as cursor:
            row = await cursor.fetchone()
            total_reactions = row[0] if row else 0
        
        # Обновляем в messages
        await db.execute('''
            UPDATE messages 
            SET total_reactions = ? 
            WHERE chat_id = ? AND message_id = ?
        ''', (total_reactions, chat_id, message_id))
        await db.commit()


async def should_forward_message(chat_id, message_id):
    """
    Проверить нужно ли пересылать сообщение в новости
    Возвращает True если:
    - Сообщение с фото
    - Набрало достаточно реакций
    - Еще не переслано
    """
    min_reactions = getattr(config, 'PHOTO_NEWS_MIN_REACTIONS', 5)
    
    async with aiosqlite.connect('messages.db') as db:
        async with db.execute('''
            SELECT has_photo, total_reactions, is_forwarded 
            FROM messages 
            WHERE chat_id = ? AND message_id = ?
        ''', (chat_id, message_id)) as cursor:
            row = await cursor.fetchone()
        
        if not row:
            return False
        
        has_photo, total_reactions, is_forwarded = row
        
        # Проверяем условия
        return (
            has_photo == 1 and 
            total_reactions >= min_reactions and 
            is_forwarded == 0
        )


async def mark_as_forwarded(chat_id, message_id):
    """
    Отметить сообщение как переслано
    """
    async with aiosqlite.connect('messages.db') as db:
        await db.execute('''
            UPDATE messages 
            SET is_forwarded = 1, forwarded_at = ? 
            WHERE chat_id = ? AND message_id = ?
        ''', (datetime.now(), chat_id, message_id))
        await db.commit()


async def get_message_info(chat_id, message_id):
    """
    Получить информацию о сообщении
    """
    async with aiosqlite.connect('messages.db') as db:
        async with db.execute('''
            SELECT user_id, username, has_photo, total_reactions, is_forwarded 
            FROM messages 
            WHERE chat_id = ? AND message_id = ?
        ''', (chat_id, message_id)) as cursor:
            return await cursor.fetchone()
