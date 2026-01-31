BOT_TOKEN = "8303282836:AAEvaKh6tk4ffcTDB20JOk1Y3_x_TpclD0s"
SUMMARY_TIME = "23:15"

# GigaChat API
GIGACHAT_CLIENT_ID = "019a3604-4772-7b85-a197-54598cd4a191"
GIGACHAT_CLIENT_SECRET = "MDE5YTM2MDQtNDc3Mi03Yjg1LWExOTctNTQ1OThjZDRhMTkxOjI1NzA1M2UzLTEyNTItNDU3Yy1hZjQwLThiMDljZGQ2NWUzMg=="
GIGACHAT_SCOPE = "GIGACHAT_API_PERS"  # обычно "GIGACHAT_API_PERS" или "GIGACHAT_API_CORP"

# Mini App URL (если используешь)
WEBAPP_URL = "https://your-domain.com"  # Замени на свой домен или IP

# ========================================
# НАСТРОЙКИ ВОДЯНОГО ЗНАКА
# ========================================

# Режим водяного знака: 'text' или 'png'
WATERMARK_MODE = 'png'  # ← ИЗМЕНИ НА 'png' ЧТОБЫ ИСПОЛЬЗОВАТЬ ЛОГОТИП

# Общие настройки (для обоих режимов)
WATERMARK_ANGLE = 0  # Угол поворота (градусы)
WATERMARK_SPACING_X = 500  # Расстояние между водяными знаками по горизонтали
WATERMARK_SPACING_Y = 200  # Расстояние между водяными знаками по вертикали

# --- Настройки для ТЕКСТОВОГО водяного знака (WATERMARK_MODE = 'text') ---
WATERMARK_TEXT = "Чат соседей ПП 5"  # Текст водяного знака
WATERMARK_FONT_SIZE = 36  # Размер шрифта
WATERMARK_OPACITY = 50  # Прозрачность текста (0-255, чем больше тем ярче)

# --- Настройки для PNG логотипа (WATERMARK_MODE = 'png') ---
WATERMARK_PNG_PATH = "/opt/adiletbot/logo.png"  # Путь к PNG файлу с логотипом
WATERMARK_PNG_WIDTH = 150  # Ширина логотипа в пикселях (высота подстроится автоматически)
WATERMARK_PNG_OPACITY = 100  # Прозрачность логотипа (0-100 процентов)

# Дополнительный логотип в правом нижнем углу (опционально)
WATERMARK_CORNER_PNG_PATH = "/opt/adiletbot/qrcode.png"  # Путь к угловому логотипу (или None чтобы отключить)
WATERMARK_CORNER_PNG_WIDTH = 200  # Ширина углового логотипа
WATERMARK_CORNER_PNG_OPACITY = 80  # Прозрачность углового логотипа (0-100)

# ========================================
# НАСТРОЙКИ ПЕРЕСЫЛКИ ПОПУЛЯРНЫХ ФОТО
# ========================================

# Включить/выключить функцию
PHOTO_NEWS_ENABLED = False

# ID чата "Фото Новости" куда пересылать популярные фото
# Для топиков: используй ID основного чата
PHOTO_NEWS_TARGET_CHAT_ID = -1002528773051  # ← УКАЖИ ID ЧАТА (например: -1002528773051)

# ID топика "Фото Новости" (если пересылаем в топик)
# Если None - пересылает в основной чат
PHOTO_NEWS_TARGET_THREAD_ID = 93966 # ← УКАЖИ ID ТОПИКА (например: 123)

# Минимальное количество реакций для пересылки
PHOTO_NEWS_MIN_REACTIONS = 3

# Список чатов-источников (пустой список = берём из всех чатов)
# Если хочешь брать только из определённых чатов, укажи их ID
PHOTO_NEWS_SOURCE_CHATS = []  # Например: [-1001111111, -1002222222]
