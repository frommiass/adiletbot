"""
Модуль для наложения водяных знаков на изображения
Поддерживает текстовые метки и PNG логотипы
"""

from PIL import Image, ImageDraw, ImageFont
import logging
import config

logger = logging.getLogger(__name__)


async def apply_watermark(input_path: str, user_id) -> str:
    """
    Применяет водяной знак к изображению
    
    Args:
        input_path: Путь к исходному изображению
        user_id: ID пользователя (для уникальных имен файлов)
        
    Returns:
        Путь к обработанному изображению
    """
    mode = getattr(config, 'WATERMARK_MODE', 'text')
    
    if mode == 'png':
        return await apply_png_watermark(input_path, user_id)
    else:
        return await apply_text_watermark(input_path, user_id)


async def apply_text_watermark(input_path: str, user_id) -> str:
    """Накладывает текстовый водяной знак"""
    
    # Открываем изображение
    img = Image.open(input_path).convert('RGBA')
    width, height = img.size
    
    # Настройки из config
    text = getattr(config, 'WATERMARK_TEXT', "© Водяной Знак")
    angle = getattr(config, 'WATERMARK_ANGLE', 30)
    opacity = getattr(config, 'WATERMARK_OPACITY', 60)
    spacing_x = getattr(config, 'WATERMARK_SPACING_X', 300)
    spacing_y = getattr(config, 'WATERMARK_SPACING_Y', 150)
    font_size = getattr(config, 'WATERMARK_FONT_SIZE', 36)
    
    # Загружаем шрифт
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()
    
    # Создаём большой слой (в 3 раза больше фото)
    big_width = width * 3
    big_height = height * 3
    txt_layer = Image.new('RGBA', (big_width, big_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)
    
    # Рисуем текст по всему большому слою
    for y in range(0, big_height, spacing_y):
        for x in range(0, big_width, spacing_x):
            draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))
    
    # Поворачиваем большой слой
    txt_layer = txt_layer.rotate(angle, expand=False)
    
    # Вырезаем центральную часть размером с оригинальное фото
    left = (big_width - width) // 2
    top = (big_height - height) // 2
    txt_layer = txt_layer.crop((left, top, left + width, top + height))
    
    # Накладываем водяной знак
    watermarked = Image.alpha_composite(img, txt_layer)
    
    # Конвертируем в RGB (Telegram не поддерживает прозрачность)
    # Создаём белый фон
    rgb_image = Image.new('RGB', watermarked.size, (255, 255, 255))
    rgb_image.paste(watermarked, mask=watermarked.split()[3])  # Используем альфа-канал как маску
    
    # Сохраняем как PNG для максимального качества
    output_path = f"/tmp/watermarked_{user_id}.png"
    rgb_image.save(output_path, format='PNG', optimize=False)
    
    logger.info(f"Applied text watermark: {output_path}")
    return output_path


async def apply_png_watermark(input_path: str, user_id) -> str:
    """Накладывает PNG логотип как водяной знак"""
    
    # Открываем изображение
    img = Image.open(input_path).convert('RGBA')
    width, height = img.size
    
    # Настройки из config
    png_path = getattr(config, 'WATERMARK_PNG_PATH', 'logo.png')
    corner_png_path = getattr(config, 'WATERMARK_CORNER_PNG_PATH', None)  # Новый параметр
    angle = getattr(config, 'WATERMARK_ANGLE', 30)
    opacity_percent = getattr(config, 'WATERMARK_PNG_OPACITY', 50)  # 0-100 процентов
    spacing_x = getattr(config, 'WATERMARK_SPACING_X', 300)
    spacing_y = getattr(config, 'WATERMARK_SPACING_Y', 200)
    logo_width = getattr(config, 'WATERMARK_PNG_WIDTH', 150)
    corner_logo_width = getattr(config, 'WATERMARK_CORNER_PNG_WIDTH', 200)  # Размер углового логотипа
    corner_opacity = getattr(config, 'WATERMARK_CORNER_PNG_OPACITY', 80)  # Прозрачность углового
    
    try:
        # Загружаем PNG логотип
        logo = Image.open(png_path).convert('RGBA')
        
        # Масштабируем логотип
        logo_aspect = logo.height / logo.width
        logo_height = int(logo_width * logo_aspect)
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        # Применяем прозрачность к логотипу
        logo_with_opacity = Image.new('RGBA', logo.size, (0, 0, 0, 0))
        
        # Копируем логотип с новой прозрачностью
        alpha = logo.split()[3]  # Получаем альфа-канал
        alpha = alpha.point(lambda p: int(p * opacity_percent / 100))  # Уменьшаем прозрачность
        logo_copy = logo.copy()
        logo_copy.putalpha(alpha)
        
        # Создаём большой слой
        big_width = width * 3
        big_height = height * 3
        big_layer = Image.new('RGBA', (big_width, big_height), (0, 0, 0, 0))
        
        # Размещаем логотипы по всему большому слою в шахматном порядке
        row = 0
        for y in range(0, big_height, spacing_y):
            col = 0
            for x in range(0, big_width, spacing_x):
                # Шахматный порядок: чередуем позиции
                if (row + col) % 2 == 0:
                    big_layer.paste(logo_copy, (x, y), logo_copy)
                col += 1
            row += 1
        
        # Поворачиваем большой слой
        big_layer = big_layer.rotate(angle, expand=False)
        
        # Вырезаем центральную часть
        left = (big_width - width) // 2
        top = (big_height - height) // 2
        final_layer = big_layer.crop((left, top, left + width, top + height))
        
        # Накладываем на фото
        watermarked = Image.alpha_composite(img, final_layer)
        
        # ДОБАВЛЯЕМ УГЛОВОЙ ЛОГОТИП (если указан)
        if corner_png_path:
            try:
                corner_logo = Image.open(corner_png_path).convert('RGBA')
                
                # Масштабируем угловой логотип
                corner_aspect = corner_logo.height / corner_logo.width
                corner_height = int(corner_logo_width * corner_aspect)
                corner_logo = corner_logo.resize((corner_logo_width, corner_height), Image.Resampling.LANCZOS)
                
                # Применяем прозрачность
                corner_alpha = corner_logo.split()[3]
                corner_alpha = corner_alpha.point(lambda p: int(p * corner_opacity / 100))
                corner_logo.putalpha(corner_alpha)
                
                # Позиция в правом нижнем углу (с отступом 20px)
                margin = 20
                corner_x = width - corner_logo_width - margin
                corner_y = height - corner_height - margin
                
                # Накладываем угловой логотип
                watermarked.paste(corner_logo, (corner_x, corner_y), corner_logo)
                
                logger.info(f"Added corner logo to bottom-right")
            except Exception as e:
                logger.warning(f"Could not add corner logo: {e}")
        
        # Конвертируем в RGB (Telegram не поддерживает прозрачность)
        # Создаём белый фон
        rgb_image = Image.new('RGB', watermarked.size, (255, 255, 255))
        rgb_image.paste(watermarked, mask=watermarked.split()[3])  # Используем альфа-канал как маску
        
        # Сохраняем как PNG для максимального качества
        output_path = f"/tmp/watermarked_{user_id}.png"
        rgb_image.save(output_path, format='PNG', optimize=False)
        
        logger.info(f"Applied PNG watermark: {output_path}")
        return output_path
        
    except FileNotFoundError:
        logger.error(f"PNG file not found: {png_path}")
        logger.info("Falling back to text watermark")
        return await apply_text_watermark(input_path, user_id)
    except Exception as e:
        logger.error(f"Error applying PNG watermark: {e}")
        logger.info("Falling back to text watermark")
        return await apply_text_watermark(input_path, user_id)