"""
Простейший тест для проверки функциональности без pytest
"""
import asyncio
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Добавляем текущую директорию в path
sys.path.insert(0, '.')

from database.database import Base
from database.models import User, Lesson, Purchase
from services.user import UserService
from services.lesson import LessonService

# Тестовая БД в памяти
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async def test_user_service():
    """Тестирование UserService"""
    print("🧪 Запуск тестов UserService...")
    
    # Создание тестового движка БД
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Создание всех таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создание сессии
    async_session = async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        user_service = UserService(session)
        
        print("  ✅ 1. Тестирование получения несуществующего пользователя...")
        user = await user_service.get_user_by_telegram_id(999999999)
        assert user is None, "Несуществующий пользователь должен возвращать None"
        print("     ✅ Тест пройден!")
        
        print("  ✅ 2. Тестирование создания нового пользователя...")
        user_id = 123456789
        username = "test_user"
        full_name = "Тестовый Пользователь"
        
        created_user = await user_service.create_user(user_id, username, full_name)
        assert created_user is not None, "Пользователь должен быть создан"
        assert created_user.user_id == user_id, "ID пользователя должен совпадать"
        assert created_user.username == username, "Username должен совпадать"
        assert created_user.full_name == full_name, "Полное имя должно совпадать"
        print("     ✅ Тест пройден!")
        
        print("  ✅ 3. Тестирование получения существующего пользователя...")
        found_user = await user_service.get_user_by_telegram_id(user_id)
        assert found_user is not None, "Пользователь должен быть найден"
        assert found_user.id == created_user.id, "ID должны совпадать"
        print("     ✅ Тест пройден!")
        
        print("  ✅ 4. Тестирование обновления языка пользователя...")
        success = await user_service.update_user_language(user_id, 'en')
        assert success is True, "Обновление языка должно быть успешным"
        
        updated_user = await user_service.get_user_by_telegram_id(user_id)
        assert updated_user.language == 'en', "Язык должен быть обновлен"
        print("     ✅ Тест пройден!")
        
        print("  ✅ 5. Тестирование логирования активности пользователя...")
        success = await user_service.log_user_activity(
            user_id, 
            "test_action", 
            lesson_id=1, 
            extra_data="test_data"
        )
        assert success is True, "Логирование активности должно быть успешным"
        print("     ✅ Тест пройден!")
    
    await engine.dispose()
    print("🎉 Все тесты UserService пройдены успешно!")

async def test_lesson_service():
    """Тестирование LessonService"""
    print("🧪 Запуск тестов LessonService...")
    
    # Создание тестового движка БД
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Создание всех таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создание сессии
    async_session = async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        lesson_service = LessonService(session)
        
        print("  ✅ 1. Тестирование получения несуществующего урока...")
        lesson = await lesson_service.get_lesson_by_id(999999)
        assert lesson is None, "Несуществующий урок должен возвращать None"
        print("     ✅ Тест пройден!")
        
        print("  ✅ 2. Тестирование создания и получения урока...")
        # Создание тестового урока
        test_lesson = Lesson(
            title="Тестовый урок",
            description="Описание тестового урока",
            price_stars=100,
            content_type="video",
            file_id="test_file_123",
            duration=300,
            is_active=True,
            is_free=False,
            category="Тестирование",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            views_count=0
        )
        
        session.add(test_lesson)
        await session.commit()
        await session.refresh(test_lesson)
        
        # Получение урока по ID
        found_lesson = await lesson_service.get_lesson_by_id(test_lesson.id)
        assert found_lesson is not None, "Урок должен быть найден"
        assert found_lesson.title == test_lesson.title, "Название урока должно совпадать"
        print("     ✅ Тест пройден!")
        
        print("  ✅ 3. Тестирование увеличения счетчика просмотров...")
        initial_views = found_lesson.views_count
        
        success = await lesson_service.increment_lesson_views(test_lesson.id)
        assert success is True, "Увеличение просмотров должно быть успешным"
        
        updated_lesson = await lesson_service.get_lesson_by_id(test_lesson.id)
        assert updated_lesson.views_count == initial_views + 1, "Счетчик просмотров должен увеличиться"
        print("     ✅ Тест пройден!")
        
        print("  ✅ 4. Тестирование получения уроков с пагинацией...")
        lessons, total_count = await lesson_service.get_lessons_paginated(page=0, per_page=10)
        assert isinstance(lessons, list), "Должен возвращаться список"
        assert isinstance(total_count, int), "Общее количество должно быть числом"
        assert total_count >= 1, "Должен быть хотя бы один урок"
        print("     ✅ Тест пройден!")
    
    await engine.dispose()
    print("🎉 Все тесты LessonService пройдены успешно!")

async def test_integration():
    """Интеграционный тест: покупка урока"""
    print("🧪 Запуск интеграционного теста покупки урока...")
    
    # Создание тестового движка БД
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Создание всех таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создание сессии
    async_session = async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        user_service = UserService(session)
        lesson_service = LessonService(session)
        
        print("  ✅ 1. Создание пользователя и урока...")
        # Создание пользователя
        user = await user_service.create_user(
            user_id=555666777,
            username="integration_user",
            full_name="Интеграционный Пользователь"
        )
        assert user is not None
        
        # Создание урока
        lesson = Lesson(
            title="Платный урок",
            description="Урок для интеграционного теста",
            price_stars=150,
            content_type="video",
            file_id="integration_video",
            is_active=True,
            is_free=False,
            category="Интеграция"
        )
        
        session.add(lesson)
        await session.commit()
        await session.refresh(lesson)
        print("     ✅ Пользователь и урок созданы!")
        
        print("  ✅ 2. Проверка изначального отсутствия доступа...")
        has_access = await lesson_service.check_user_has_lesson(user.user_id, lesson.id)
        assert has_access is False, "Изначально доступа быть не должно"
        print("     ✅ Доступ изначально отсутствует!")
        
        print("  ✅ 3. Симуляция покупки урока...")
        # Создание покупки (симуляция успешного платежа)
        purchase = Purchase(
            user_id=user.user_id,
            lesson_id=lesson.id,
            payment_charge_id="integration_test_payment",
            purchase_date=datetime.utcnow(),
            status="completed",
            amount_stars=lesson.price_stars
        )
        
        session.add(purchase)
        await session.commit()
        await session.refresh(purchase)
        print("     ✅ Покупка создана!")
        
        print("  ✅ 4. Проверка получения доступа после покупки...")
        has_access_after = await lesson_service.check_user_has_lesson(user.user_id, lesson.id)
        assert has_access_after is True, "После покупки доступ должен появиться"
        print("     ✅ Доступ получен после покупки!")
        
        print("  ✅ 5. Проверка списка покупок пользователя...")
        purchases, total_count = await lesson_service.get_user_purchases(user.user_id)
        assert total_count == 1, "У пользователя должна быть одна покупка"
        assert purchases[0]['lesson'].id == lesson.id, "В покупках должен быть наш урок"
        print("     ✅ Список покупок корректный!")
    
    await engine.dispose()
    print("🎉 Интеграционный тест пройден успешно!")

"""
Simple validation test for main menu changes
"""
import sys
sys.path.append('.')

def test_main_menu():
    try:
        from keyboards.user import main_menu_keyboard
        
        kb = main_menu_keyboard()
        kb_str = str(kb.inline_keyboard)
        
        print("Testing main menu keyboard...")
        print("Buttons found:", kb_str)
        
        # Test for profile button
        if "Мой профиль" in kb_str and "profile" in kb_str:
            print("✅ Profile button found")
        else:
            print("❌ Profile button not found")
        
        # Test settings button is removed
        if "Настройки" not in kb_str:
            print("✅ Settings button removed")
        else:
            print("❌ Settings button still present")
            
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

async def main():
    """Запуск всех тестов"""
    print("🚀 Запуск тестирования Learning Bot...\n")
    
    try:
        await test_user_service()
        print()
        
        await test_lesson_service()
        print()
        
        await test_integration()
        print()
        
        print("🎉🎉🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! 🎉🎉🎉")
        print("✅ UserService работает корректно")
        print("✅ LessonService работает корректно") 
        print("✅ Интеграционные процессы работают корректно")
        print("✅ База данных функционирует правильно")
        print("✅ Модели созданы без ошибок")
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
