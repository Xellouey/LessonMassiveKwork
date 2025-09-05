"""
Тест запуска бота - проверяем инициализацию
"""
import asyncio
import sys
sys.path.insert(0, '.')

from config import settings
from bot import create_bot, create_dispatcher, on_startup

async def test_bot_startup():
    """Тестирование инициализации бота"""
    print("🤖 Тестирование запуска Learning Bot...")
    
    try:
        print(f"📋 Конфигурация:")
        print(f"   • Bot Token: {settings.telegram.bot_token[:20]}...")
        print(f"   • Database: {settings.db.url}")
        print(f"   • Debug Mode: {settings.app.debug}")
        print(f"   • Admin IDs: {settings.telegram.admin_ids}")
        
        print("\n🔨 Создание бота и диспетчера...")
        bot = await create_bot()
        dp = await create_dispatcher()
        
        print("✅ Бот успешно создан!")
        print(f"   • Bot ID: {bot.id if hasattr(bot, 'id') else 'Unknown'}")
        
        print("\n🗄️ Проверка базы данных...")
        await on_startup()
        
        print("✅ База данных готова!")
        
        # Проверяем получение информации о боте
        print("\n📊 Получение информации о боте...")
        me = await bot.get_me()
        print(f"✅ Информация о боте получена:")
        print(f"   • Username: @{me.username}")
        print(f"   • Name: {me.first_name}")
        print(f"   • ID: {me.id}")
        
        print("\n🎉 ВСЁ ГОТОВО! Бот полностью настроен и может быть запущен!")
        
        await bot.session.close()
        
    except Exception as e:
        print(f"❌ Ошибка при инициализации: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 ПРОВЕРКА ГОТОВНОСТИ БОТА К ЗАПУСКУ...")
    print()
    
    success = asyncio.run(test_bot_startup())
    
    if success:
        print()
        print("🎊 ГОТОВО! Бот готов к запуску!")
        print("🔄 Для запуска используйте: python bot.py")
    else:
        print()
        print("❌ Есть проблемы с конфигурацией. Проверьте настройки.")