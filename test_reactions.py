import sqlite3
from datetime import datetime


# Подключаемся к локальной базе
conn = sqlite3.connect('messages.db')
cursor = conn.cursor()


# Создаем таблицу реакций если нет
cursor.execute('''
    CREATE TABLE IF NOT EXISTS reactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id INTEGER,
        author_user_id INTEGER,
        author_username TEXT,
        reaction_emoji TEXT,
        reactor_user_id INTEGER,
        timestamp DATETIME
    )
''')


# Добавляем тестовые реакции
test_reactions = [
    (1, 111, 'username1', '👍', 222),
    (1, 111, 'username1', '👍', 333),
    (1, 111, 'username1', '😂', 444),
    (2, 222, 'username2', '😂', 111),
    (2, 222, 'username2', '😂', 333),
    (2, 222, 'username2', '😂', 444),
    (2, 222, 'username2', '❤️', 555),
    (3, 333, 'username3', '👍', 111),
    (3, 333, 'username3', '🔥', 222),
]


for msg_id, author_id, author_name, emoji, reactor_id in test_reactions:
    cursor.execute('''
        INSERT INTO reactions (message_id, author_user_id, author_username, reaction_emoji, reactor_user_id, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (msg_id, author_id, author_name, emoji, reactor_id, datetime.now()))


conn.commit()


# Тестируем статистику
print("📊 ТЕСТИРОВАНИЕ СТАТИСТИКИ ПО РЕАКЦИЯМ\n")


# Общий топ
cursor.execute('''
    SELECT author_username, COUNT(*) as reaction_count
    FROM reactions
    GROUP BY author_user_id, author_username
    ORDER BY reaction_count DESC
    LIMIT 10
''')


total_top = cursor.fetchall()


print("🏆 ТОП ПО РЕАКЦИЯМ (всего):")
for idx, (username, count) in enumerate(total_top, 1):
    print(f"{idx}. {username} - {count}")


# Топ по каждой реакции
cursor.execute('SELECT DISTINCT reaction_emoji FROM reactions')
emojis = cursor.fetchall()


for (emoji,) in emojis:
    cursor.execute('''
        SELECT author_username, COUNT(*) as count
        FROM reactions
        WHERE reaction_emoji = ?
        GROUP BY author_user_id, author_username
        ORDER BY count DESC
        LIMIT 10
    ''', (emoji,))
    
    emoji_top = cursor.fetchall()
    
    print(f"\nТоп {emoji}:")
    for idx, (username, count) in enumerate(emoji_top, 1):
        print(f"{idx}. {username} - {count}")


conn.close()


print("\n✅ Тест завершен!")



