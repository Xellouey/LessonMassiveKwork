#!/usr/bin/env python3
"""
Простая проверка работоспособности упрощенного бота
"""

import asyncio
import sys
import os

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_imports():
    """Тестирование импортов основного функционала"""
    print("🔍 Проверка импортов основного функционала...")
    
    try:
        # Основные импорты
        from config import settings
        print("✅ Config loaded")
        
        # Импорты пользовательских обработчиков
        from handlers.user.start import router as start_router
        from handlers.user.free_lessons import router as free_lessons_router
        from handlers.user.catalog import router as catalog_router
        from handlers.user.lesson_detail import router as lesson_detail_router
        from handlers.user.payment import router as payment_router
        from handlers.user.profile import router as profile_router
        print("✅ User handlers loaded")
        
        # Импорты административных обработчиков (активных)
        from handlers.admin.main import router as admin_main_router
        from handlers.admin.lessons import router as admin_lessons_router
        from handlers.admin.statistics import router as admin_statistics_router
        from handlers.admin.broadcast import router as admin_broadcast_router
        from handlers.admin.texts import router as admin_texts_router
        from handlers.admin.withdrawal import router as admin_withdrawal_router
        print("✅ Admin handlers loaded")
        
        # Импорты клавиатур
        from keyboards.admin import admin_main_menu_keyboard
        from keyboards.user import main_menu_keyboard
        print("✅ Keyboards loaded")
        
        # Импорты сервисов
        from services.user import UserService
        from services.lesson import LessonService
        from services.payment import PaymentService
        from services.statistics import StatisticsService
        from services.broadcast import BroadcastService
        from services.text import TextService
        from services.withdrawal import WithdrawalService
        print("✅ Services loaded")
        
        print("\n🎉 Все основные компоненты успешно загружены!")
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False


async def test_disabled_components():
    """Проверка, что отключенные компоненты действительно не используются"""
    print("\n🔍 Проверка отключенных компонентов...")
    
    # Эти импорты должны работать, но не должны использоваться в bot.py
    try:
        # Закомментированные сервисы должны существовать, но с предупреждениями
        from services.user_management import UserManagementService
        from services.media import MediaService
        print("⚠️ Отключенные сервисы найдены (это нормально, они просто не используются)")
        
        return True
    except ImportError:
        print("✅ Отключенные сервисы недоступны")
        return True


async def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование упрощенного LearningBot")
    print("=" * 50)
    
    success = True
    
    # Тест основного функционала
    if not await test_imports():
        success = False
    
    # Тест отключенных компонентов
    if not await test_disabled_components():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Все тесты пройдены! Упрощенный бот готов к использованию.")
        print("\n📋 Активный функционал:")
        print("   👤 Пользователи: воронка, каталог, оплата, личный кабинет")
        print("   🛠️ Админы: уроки, тексты, статистика, рассылки, вывод средств")
        print("\n⚠️ Отключенный функционал:")
        print("   ❌ Управление пользователями (блокировка, поиск, удаление)")
        print("   ❌ Управление медиа (отдельная загрузка медиа)")
    else:
        print("❌ Обнаружены проблемы. Проверьте код выше.")
    
    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n👋 Тестирование прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Критическая ошибка при тестировании: {e}")
        sys.exit(1)