"""
Основной файл Learning Bot - точка входа
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.database import init_db, close_db
from middlewares.auth import AuthMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.throttling import ThrottlingMiddleware


async def create_bot() -> Bot:
    """Создание экземпляра бота"""
    return Bot(
        token=settings.telegram.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True
        )
    )


async def create_dispatcher() -> Dispatcher:
    """Создание и настройка диспетчера"""
    # Создание хранилища состояний (в дальнейшем можно заменить на Redis)
    storage = MemoryStorage()
    
    # Создание диспетчера
    dp = Dispatcher(storage=storage)
    
    # Подключение middleware (порядок важен!)
    # 1. DatabaseMiddleware - должен быть первым для предоставления сессии БД
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    
    # 2. AuthMiddleware - создание/получение пользователя
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    
    # 3. AdminMiddleware - проверка прав администратора (требует сессию БД)
    from middlewares.admin import AdminMiddleware
    dp.message.middleware(AdminMiddleware())
    dp.callback_query.middleware(AdminMiddleware())
    
    # 4. ThrottlingMiddleware - ограничение частоты запросов
    dp.message.middleware(ThrottlingMiddleware())
    
    # Регистрация роутеров
    from handlers.user.start import router as start_router
    from handlers.user.free_lessons import router as free_lessons_router
    from handlers.user.catalog import router as catalog_router
    from handlers.user.lesson_detail import router as lesson_detail_router
    from handlers.user.payment import router as payment_router
    from handlers.user.profile import router as profile_router
    
    # Административные роутеры - основной функционал
    from handlers.admin.main import router as admin_main_router
    from handlers.admin.lessons import router as admin_lessons_router
    from handlers.admin.categories import router as admin_categories_router
    from handlers.admin.statistics import router as admin_statistics_router
    from handlers.admin.support import router as admin_support_router
    # from handlers.admin.users import router as admin_users_router  # ❌ Закомментировано - сложное управление пользователями не нужно для MVP
    from handlers.admin.broadcast import router as admin_broadcast_router
    from handlers.admin.texts import router as admin_texts_router
    # from handlers.admin.media import router as admin_media_router  # ❌ Закомментировано - отдельное управление медиа слишком сложно для MVP
    from handlers.admin.withdrawal import router as admin_withdrawal_router
    
    # Подключение административных роутеров (ПЕРВЫМИ - они имеют приоритет)
    dp.include_router(admin_main_router)
    dp.include_router(admin_lessons_router)
    dp.include_router(admin_categories_router)
    dp.include_router(admin_statistics_router)
    dp.include_router(admin_support_router)
    # dp.include_router(admin_users_router)  # ❌ Закомментировано - сложное управление пользователями не нужно для MVP
    dp.include_router(admin_broadcast_router)
    dp.include_router(admin_texts_router)
    # dp.include_router(admin_media_router)  # ❌ Закомментировано - отдельное управление медиа слишком сложно для MVP
    dp.include_router(admin_withdrawal_router)
    
    # Подключение пользовательских роутеров (после админских)
    dp.include_router(start_router)
    dp.include_router(free_lessons_router)
    dp.include_router(catalog_router)
    dp.include_router(lesson_detail_router)
    dp.include_router(payment_router)
    dp.include_router(profile_router)
    
    return dp


async def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=getattr(logging, settings.app.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )
    
    # Настройка логгеров для aiogram
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)  # Отключить debug логи aiosqlite


async def on_startup():
    """Действия при запуске бота"""
    logging.info("🚀 Запуск Learning Bot...")
    
    # Инициализация базы данных
    try:
        await init_db()
        logging.info("✅ База данных инициализирована")
    except Exception as e:
        logging.error(f"❌ Ошибка инициализации базы данных: {e}")
        raise
    
    # Дополнительные действия при запуске
    logging.info("✅ Бот запущен и готов к работе!")


async def on_shutdown():
    """Действия при остановке бота"""
    logging.info("🛑 Остановка Learning Bot...")
    
    # Закрытие соединения с базой данных
    await close_db()
    logging.info("✅ Соединение с базой данных закрыто")
    
    logging.info("✅ Бот остановлен")


async def main():
    """Главная функция"""
    # Настройка логирования
    await setup_logging()
    
    try:
        # Создание бота и диспетчера
        bot = await create_bot()
        dp = await create_dispatcher()
        
        # Регистрация событий
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        # Удаление webhook (для polling режима)
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запуск polling
        logging.info("🔄 Запуск в режиме polling...")
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logging.info("👋 Получен сигнал остановки")
    except Exception as e:
        logging.error(f"💥 Критическая ошибка: {e}")
        raise
    finally:
        await on_shutdown()


if __name__ == "__main__":
    # Проверка наличия токена
    if not settings.telegram.bot_token:
        logging.error("❌ BOT_TOKEN не установлен в переменных окружения!")
        sys.exit(1)
    
    # Запуск бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("👋 Получен сигнал остановки от пользователя")
    except Exception as e:
        logging.error(f"💥 Неожиданная ошибка при запуске: {e}")
        sys.exit(1)