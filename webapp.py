from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import aiosqlite
from datetime import datetime, timedelta

app = FastAPI()


@app.get("/")
async def root():
    """Главная страница Mini App"""
    return FileResponse("index.html")


@app.get("/shahmatka.html")
async def shahmatka():
    """Страница шахматки"""
    return FileResponse("shahmatka.html")


@app.get("/statistics.html")
async def statistics():
    """Страница статистики"""
    return FileResponse("statistics.html")


@app.get("/contacts.html")
async def contacts():
    """Страница контактов"""
    return FileResponse("contacts.html")


@app.get("/api/stats")
async def get_stats(period: str = "today", chat_id: str = "demo"):
    """API для получения статистики"""
    
    if chat_id == "demo":
        # Демо-данные
        return {
            "total_messages": 142,
            "total_users": 12,
            "total_reactions": 87,
            "top_users": [
                {"name": "Алексей", "count": 45},
                {"name": "Мария", "count": 38},
                {"name": "Дмитрий", "count": 21},
                {"name": "Елена", "count": 18},
                {"name": "Иван", "count": 12}
            ],
            "top_reactions": [
                {"name": "Мария", "count": 23},
                {"name": "Алексей", "count": 19},
                {"name": "Дмитрий", "count": 15}
            ],
            "emoji_stats": [
                {"emoji": "👍", "count": 34},
                {"emoji": "😂", "count": 28},
                {"emoji": "❤️", "count": 15},
                {"emoji": "🔥", "count": 10}
            ]
        }
    
    # Определяем период
    if period == "today":
        date_filter = "date(timestamp) = date('now')"
    elif period == "week":
        date_filter = "datetime(timestamp) >= datetime('now', '-7 days')"
    else:  # month
        date_filter = "datetime(timestamp) >= datetime('now', '-30 days')"
    
    try:
        chat_id_int = int(chat_id)
    except:
        chat_id_int = None
    
    if not chat_id_int:
        return {"error": "Invalid chat_id"}
    
    async with aiosqlite.connect('messages.db') as db:
        # Общая статистика
        async with db.execute(f'''
            SELECT COUNT(*) as total, COUNT(DISTINCT user_id) as users
            FROM messages
            WHERE chat_id = ? AND {date_filter}
        ''', (chat_id_int,)) as cursor:
            row = await cursor.fetchone()
            total_messages, total_users = row if row else (0, 0)
        
        # Топ активных пользователей
        async with db.execute(f'''
            SELECT 
                COALESCE(username, first_name, 'Аноним') as name,
                COUNT(*) as count
            FROM messages
            WHERE chat_id = ? AND {date_filter}
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT 10
        ''', (chat_id_int,)) as cursor:
            top_users = [{"name": row[0], "count": row[1]} for row in await cursor.fetchall()]
        
        # Статистика по реакциям
        async with db.execute(f'''
            SELECT COUNT(*) as total
            FROM reactions r
            JOIN messages m ON r.message_id = m.message_id
            WHERE m.chat_id = ? AND {date_filter.replace('timestamp', 'r.timestamp')}
        ''', (chat_id_int,)) as cursor:
            row = await cursor.fetchone()
            total_reactions = row[0] if row else 0
        
        # Топ по реакциям (кто получил больше всего)
        async with db.execute(f'''
            SELECT 
                COALESCE(r.author_username, 'Аноним') as name,
                COUNT(*) as count
            FROM reactions r
            JOIN messages m ON r.message_id = m.message_id
            WHERE m.chat_id = ? AND {date_filter.replace('timestamp', 'r.timestamp')}
            GROUP BY r.author_user_id
            ORDER BY count DESC
            LIMIT 10
        ''', (chat_id_int,)) as cursor:
            top_reactions = [{"name": row[0], "count": row[1]} for row in await cursor.fetchall()]
        
        # Популярные эмодзи
        async with db.execute(f'''
            SELECT 
                r.reaction_emoji as emoji,
                COUNT(*) as count
            FROM reactions r
            JOIN messages m ON r.message_id = m.message_id
            WHERE m.chat_id = ? AND {date_filter.replace('timestamp', 'r.timestamp')}
            GROUP BY r.reaction_emoji
            ORDER BY count DESC
            LIMIT 8
        ''', (chat_id_int,)) as cursor:
            emoji_stats = [{"emoji": row[0], "count": row[1]} for row in await cursor.fetchall()]
    
    return {
        "total_messages": total_messages,
        "total_users": total_users,
        "total_reactions": total_reactions,
        "top_users": top_users,
        "top_reactions": top_reactions,
        "emoji_stats": emoji_stats
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
