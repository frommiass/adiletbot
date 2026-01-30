from gigachat import GigaChat
import config
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Создаем пул потоков для синхронных операций
executor = ThreadPoolExecutor(max_workers=2)

def _call_gigachat_sync(chat_text, message_count):
    """Синхронный вызов GigaChat (запускается в отдельном потоке)"""
    
    prompt = f"""Проанализируй переписку из соседского чата за день и создай краткое саммари.

Переписка ({message_count} сообщений):
{chat_text}

Сделай структурированное саммари:
1. Главные темы обсуждения (2-3 темы)
2. Важные вопросы или проблемы
3. Договоренности или решения (если были)
4. 😂 СМЕШИНКИ ДНЯ: Найди 1-2 самых смешных сообщения (с автором)
5. Общая атмосфера

Формат: кратко, эмодзи. Максимум 600 символов."""

    with GigaChat(
        credentials=config.GIGACHAT_CLIENT_SECRET,
        scope=config.GIGACHAT_SCOPE,
        verify_ssl_certs=False
    ) as giga:
        response = giga.chat(prompt)
        return response.choices[0].message.content


async def generate_smart_summary(messages):
    """Генерирует умное саммари через GigaChat (АСИНХРОННО)"""
    
    # Формируем текст переписки
    chat_text = ""
    for username, first_name, text, timestamp in messages:
        name = username or first_name or "Аноним"
        if text:  # Пропускаем None
            chat_text += f"{name}: {text}\n"
    
    # Ограничиваем длину
    if len(chat_text) > 6000:
        chat_text = "...\n" + chat_text[-6000:]
    
    try:
        # Запускаем синхронный GigaChat в отдельном потоке
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            _call_gigachat_sync,
            chat_text,
            len(messages)
        )
        return result
        
    except Exception as e:
        print(f"❌ ОШИБКА GIGACHAT: {e}")
        return generate_fallback_summary(messages)


def generate_fallback_summary(messages):
    """Простое саммари без LLM"""
    user_stats = {}
    for username, first_name, text, timestamp in messages:
        name = username or first_name or "Аноним"
        user_stats[name] = user_stats.get(name, 0) + 1
    
    summary = "📌 Основные обсуждения:\n\n"
    sorted_users = sorted(user_stats.items(), key=lambda x: x[1], reverse=True)[:3]
    for name, count in sorted_users:
        summary += f"💬 {name}: {count} сообщений\n"
    
    summary += "\n⚠️ GigaChat временно недоступен."
    return summary