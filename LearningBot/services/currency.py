"""
Сервис для конвертации валют и работы с Telegram Stars
"""
import logging
from typing import Optional
import aiohttp
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


class CurrencyService:
    """Сервис для конвертации валют и работы с ценами"""
    
    # Примерный курс Telegram Stars к USD (1 звезда ≈ $0.013)
    # В реальности нужно получать актуальный курс из Telegram API
    STARS_TO_USD_RATE = 0.013
    
    @classmethod
    def usd_to_stars(cls, usd_amount: float) -> int:
        """
        Конвертация долларов в звезды
        """
        try:
            stars = int(usd_amount / cls.STARS_TO_USD_RATE)
            # Минимум 1 звезда для платных уроков
            return max(1, stars)
        except (ValueError, ZeroDivisionError):
            logger.error(f"Ошибка конвертации USD в звезды: {usd_amount}")
            return 1
    
    @classmethod
    def stars_to_usd(cls, stars_amount: int) -> float:
        """
        Конвертация звезд в доллары
        """
        try:
            usd = stars_amount * cls.STARS_TO_USD_RATE
            # Округляем до 2 знаков после запятой
            return round(usd, 2)
        except (ValueError, TypeError):
            logger.error(f"Ошибка конвертации звезд в USD: {stars_amount}")
            return 0.0
    
    @classmethod
    def format_usd_price(cls, usd_amount: float) -> str:
        """
        Форматирование цены в долларах для отображения
        """
        try:
            if usd_amount == 0:
                return "Free"
            
            # Округляем до 2 знаков
            formatted_amount = round(usd_amount, 2)
            
            # Если цена целая, показываем без копеек
            if formatted_amount == int(formatted_amount):
                return f"${int(formatted_amount)}"
            else:
                return f"${formatted_amount:.2f}"
        except (ValueError, TypeError):
            logger.error(f"Ошибка форматирования USD цены: {usd_amount}")
            return "$0"
    
    @classmethod
    def sync_lesson_prices(cls, lessons: list) -> list:
        """
        Синхронизация цен уроков - обновление price_usd на основе price_stars
        или price_stars на основе price_usd в зависимости от того, что было изменено
        """
        try:
            for lesson in lessons:
                if hasattr(lesson, 'price_usd') and hasattr(lesson, 'price_stars'):
                    # Если цена в USD не установлена, вычисляем из звезд
                    if lesson.price_usd == 0 and lesson.price_stars > 0:
                        lesson.price_usd = cls.stars_to_usd(lesson.price_stars)
                    # Если цена в звездах не соответствует USD, пересчитываем
                    elif lesson.price_usd > 0:
                        expected_stars = cls.usd_to_stars(lesson.price_usd)
                        if abs(lesson.price_stars - expected_stars) > 1:  # Допуск в 1 звезду
                            lesson.price_stars = expected_stars
            
            return lessons
        except Exception as e:
            logger.error(f"Ошибка синхронизации цен уроков: {e}")
            return lessons
    
    @classmethod
    async def get_telegram_stars_rate(cls) -> Optional[float]:
        """
        Получение актуального курса Telegram Stars (если такой API существует)
        Пока возвращаем фиксированный курс
        """
        # В будущем здесь можно добавить запрос к Telegram API
        # для получения актуального курса
        return cls.STARS_TO_USD_RATE