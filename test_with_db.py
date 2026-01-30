import sqlite3
from gigachat import GigaChat
import config
from datetime import datetime


# Читаем сообщения из базы
conn = sqlite3.connect('messages.db')
cursor = conn.cursor()


# Берем сообщения за сегодня
cursor.execute('''
    SELECT username, first_name, text, timestamp 
    FROM messages 
    WHERE date(timestamp) = date('now')
    ORDER BY timestamp
''')


messages = cursor.fetchall()
conn.close()


print(f"📊 Найдено сообщений: {len(messages)}")
print("=" * 60)


# Формируем текст как в боте
chat_text = ""
for username, first_name, text, timestamp in messages:
    name = username or first_name or "Аноним"
    chat_text += f"{name}: {text}\n"
    
print("📝 Переписка которая отправляется в GigaChat:")
print("=" * 60)
print(chat_text)
print("=" * 60)
print(f"Длина: {len(chat_text)} символов")
print("=" * 60)


# Пробуем отправить в GigaChat
prompt = f"""Проанализируй переписку из соседского чата за день и создай краткое саммари.

Переписка ({len(messages)} сообщений):
{chat_text}

Сделай структурированное саммари:
1. Главные темы обсуждения (2-3 темы)
2. Важные вопросы или проблемы
3. Договоренности или решения (если были)
4. 😂 СМЕШИНКИ ДНЯ: Найди 1-2 самых смешных сообщения
5. Общая атмосфера

Формат: кратко, эмодзи. Максимум 600 символов."""


print("\n🤖 Отправляю в GigaChat...")
try:
    with GigaChat(
        credentials=config.GIGACHAT_CLIENT_SECRET,
        scope=config.GIGACHAT_SCOPE,
        verify_ssl_certs=False
    ) as giga:
        response = giga.chat(prompt)
        print("✅ УСПЕХ!")
        print("=" * 60)
        print(response.choices[0].message.content)
        
except Exception as e:
    print("❌ ОШИБКА!")
    print("=" * 60)
    print(f"Тип ошибки: {type(e)}")
    print(f"Текст ошибки: {str(e)}")




