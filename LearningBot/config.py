"""
Конфигурация для Learning Bot
"""
import os
from typing import List
from pathlib import Path
from decouple import config
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseModel):
    """Настройки базы данных"""
    url: str = config('DATABASE_URL', default='sqlite+aiosqlite:///./learning_bot.db')
    echo: bool = config('DATABASE_ECHO', default=False, cast=bool)


class TelegramSettings(BaseModel):
    """Настройки Telegram бота"""
    bot_token: str = config('BOT_TOKEN')
    webhook_url: str = config('WEBHOOK_URL', default='')
    webhook_mode: bool = config('WEBHOOK_MODE', default=False, cast=bool)
    admin_ids: List[int] = config(
        'ADMIN_IDS', 
        default='', 
        cast=lambda v: [int(x.strip()) for x in v.split(',') if x.strip()]
    )


class RedisSettings(BaseModel):
    """Настройки Redis"""
    url: str = config('REDIS_URL', default='redis://localhost:6379/0')
    enabled: bool = config('REDIS_ENABLED', default=False, cast=bool)


class WithdrawalSettings(BaseModel):
    """Настройки системы вывода средств"""
    withdrawal_enabled: bool = config('WITHDRAWAL_ENABLED', default=True, cast=bool)
    # Реальные ограничения Telegram:
    # - 21 день удержания после получения звезд
    # - Требуется 2FA пароль для вывода
    # - Вывод только через getStarsRevenueWithdrawalUrl API
    # - Автоматическое удержание НДС по региону
    processing_timeout_hours: int = config('WITHDRAWAL_PROCESSING_TIMEOUT', default=24, cast=int)
    
    # Лимиты и комиссии
    min_withdrawal_amount: int = config('MIN_WITHDRAWAL_AMOUNT', default=1000, cast=int)
    commission_rate: float = config('COMMISSION_RATE', default=0.05, cast=float)  # 5%
    min_commission: int = config('MIN_COMMISSION', default=50, cast=int)
    daily_limit: int = config('DAILY_WITHDRAWAL_LIMIT', default=100000, cast=int)
    monthly_limit: int = config('MONTHLY_WITHDRAWAL_LIMIT', default=1000000, cast=int)
    auto_approval_threshold: int = config('AUTO_APPROVAL_THRESHOLD', default=5000, cast=int)


class AppSettings(BaseModel):
    """Общие настройки приложения"""
    debug: bool = config('DEBUG', default=True, cast=bool)
    log_level: str = config('LOG_LEVEL', default='INFO')
    secret_key: str = config('SECRET_KEY', default='your-secret-key-here')
    stars_enabled: bool = config('STARS_ENABLED', default=True, cast=bool)


class Settings(BaseSettings):
    """Основные настройки приложения"""
    
    # Пути
    base_dir: Path = Path(__file__).parent
    
    # Подкатегории настроек
    db: DatabaseSettings = DatabaseSettings()
    telegram: TelegramSettings = TelegramSettings()
    redis: RedisSettings = RedisSettings()
    app: AppSettings = AppSettings()
    withdrawal: WithdrawalSettings = WithdrawalSettings()
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # Игнорировать дополнительные поля


# Глобальный экземпляр настроек
settings = Settings()