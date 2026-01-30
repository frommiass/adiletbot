from PIL import Image, ImageDraw, ImageFont

# НАСТРОЙКИ - МЕНЯЙ ТУТ
WATERMARK_TEXT = "© ПРОКШИНО"
INPUT_IMAGE = "test.jpg"
OUTPUT_IMAGE = "watermarked_output.jpg"
ANGLE = 30  # Угол поворота
FONT_SIZE = 36
TEXT_OPACITY = 40  # Прозрачность (0-255, уменьшил!)
SPACING_X = 40

0  # Расстояние между текстом по горизонтали
SPACING_Y = 250  # Расстояние между текстом по вертикали

print(f"📂 Открываю {INPUT_IMAGE}...")
img = Image.open(INPUT_IMAGE).convert('RGBA')
width, height = img.size
print(f"✅ Размер фото: {width}x{height}")

# Загружаем шрифт
try:
    font = ImageFont.truetype("arial.ttf", FONT_SIZE)
    print("✅ Шрифт: Arial")
except:
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SIZE)
        print("✅ Шрифт: DejaVu")
    except:
        font = ImageFont.load_default()
        print("⚠️ Шрифт: стандартный")

# КЛЮЧЕВОЕ: создаём слой В 3 РАЗА БОЛЬШЕ чем фото!
big_width = width * 3
big_height = height * 3
print(f"📐 Создаю большой слой: {big_width}x{big_height}")

txt_layer = Image.new('RGBA', (big_width, big_height), (0, 0, 0, 0))
draw = ImageDraw.Draw(txt_layer)

print("🎨 Рисую водяной знак по всему большому слою...")

# Рисуем текст по ВСЕМУ большому слою
for y in range(0, big_height, SPACING_Y):
    for x in range(0, big_width, SPACING_X):
        draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, TEXT_OPACITY))

print(f"🔄 Поворачиваю большой слой на {ANGLE}°...")

# Поворачиваем БОЛЬШОЙ слой
txt_layer = txt_layer.rotate(ANGLE, expand=False)

print("✂️ Вырезаю нужную часть...")

# Вырезаем ЦЕНТРАЛЬНУЮ часть размером с оригинальное фото
left = (big_width - width) // 2
top = (big_height - height) // 2
txt_layer = txt_layer.crop((left, top, left + width, top + height))

print(f"✅ Вырезанный слой: {txt_layer.size}")

# Накладываем на фото
print("✨ Накладываю водяной знак на фото...")
watermarked = Image.alpha_composite(img, txt_layer)

# Сохраняем
watermarked = watermarked.convert('RGB')
watermarked.save(OUTPUT_IMAGE, quality=100)

print(f"\n✅ ГОТОВО! Файл: {OUTPUT_IMAGE}")
print(f"📊 Размер: {watermarked.size}")