import aiosqlite
from datetime import datetime


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
                message_id INTEGER
            )
        ''')
        await db.commit()


async def save_message(chat_id, user_id, username, first_name, text, message_id):
    async with aiosqlite.connect('messages.db') as db:
        await db.execute('''
            INSERT INTO messages (chat_id, user_id, username, first_name, text, timestamp, message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (chat_id, user_id, username, first_name, text, datetime.now(), message_id))
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


