"""
Тестирование критичного компонента - PaymentService
"""
import asyncio
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Добавляем текущую директорию в path
sys.path.insert(0, '.')

from database.database import Base
from database.models import User, Lesson, Purchase
from services.user import UserService
from services.lesson import LessonService
from services.payment import PaymentService

# Тестовая БД в памяти
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async def test_payment_service():
    """Тестирование PaymentService - КРИТИЧНЫЙ КОМПОНЕНТ"""
    print("🧪 КРИТИЧНОЕ ТЕСТИРОВАНИЕ PaymentService...")
    
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
        # Создание мок-бота
        mock_bot = AsyncMock()
        payment_service = PaymentService(session, mock_bot)
        
        # Создание тестовых данных
        user = User(
            user_id=123456789,
            username="payment_user",
            full_name="Тестовый Плательщик",
            registration_date=datetime.now(timezone.utc),
            is_active=True,
            language='ru',
            total_spent=0,
            last_activity=datetime.now(timezone.utc)
        )
        
        lesson = Lesson(
            title="Платный урок",
            description="Урок для тестирования оплаты",
            price_stars=200,
            content_type="video",
            file_id="payment_test_video",
            is_active=True,
            is_free=False,
            category="Платные"
        )
        
        session.add(user)
        session.add(lesson)
        await session.commit()
        await session.refresh(user)
        await session.refresh(lesson)
        
        print("  💳 1. Тестирование валидации платежных данных...")
        
        # Валидные данные
        is_valid, error_msg, lesson_data = await payment_service.validate_payment_data(
            user.user_id, lesson.id
        )
        assert is_valid is True, f"Валидация должна пройти успешно: {error_msg}"
        assert lesson_data is not None, "Данные урока должны быть возвращены"
        assert lesson_data["price_stars"] == lesson.price_stars, "Цена должна совпадать"
        print("     ✅ Валидация корректных данных работает!")
        
        # Несуществующий урок
        is_valid, error_msg, lesson_data = await payment_service.validate_payment_data(
            user.user_id, 999999
        )
        assert is_valid is False, "Валидация должна провалиться для несуществующего урока"
        assert error_msg == "Урок не найден", "Должна быть правильная ошибка"
        print("     ✅ Валидация несуществующего урока работает!")
        
        print("  💳 2. Тестирование создания инвойса...")
        
        # Успешное создание инвойса
        mock_bot.send_invoice.return_value = True
        
        result = await payment_service.create_invoice(
            user_id=user.user_id,
            lesson_id=lesson.id,
            lesson_title=lesson.title,
            lesson_description=lesson.description,
            price_stars=lesson.price_stars
        )
        
        assert result is True, "Инвойс должен быть создан успешно"
        mock_bot.send_invoice.assert_called_once()
        
        # Проверка параметров вызова
        call_args = mock_bot.send_invoice.call_args
        assert call_args[1]['chat_id'] == user.user_id, "ID чата должен совпадать"
        assert call_args[1]['currency'] == "XTR", "Валюта должна быть Telegram Stars"
        assert len(call_args[1]['prices']) == 1, "Должна быть одна цена"
        assert call_args[1]['prices'][0].amount == lesson.price_stars, "Сумма должна совпадать"
        print("     ✅ Создание инвойса работает корректно!")
        
        print("  💳 3. Тестирование pre-checkout валидации...")
        
        # Валидный pre-checkout
        payload = f"lesson_{lesson.id}_{user.user_id}_1672531200"
        
        is_valid, error_msg = await payment_service.process_pre_checkout(
            pre_checkout_query_id="test_query_123",
            user_id=user.user_id,
            total_amount=lesson.price_stars,
            invoice_payload=payload
        )
        
        assert is_valid is True, f"Pre-checkout должен пройти успешно: {error_msg}"
        print("     ✅ Pre-checkout валидация работает!")
        
        # Невалидный payload
        is_valid, error_msg = await payment_service.process_pre_checkout(
            pre_checkout_query_id="test_query_456",
            user_id=user.user_id,
            total_amount=lesson.price_stars,
            invoice_payload="invalid_payload"
        )
        
        assert is_valid is False, "Pre-checkout с невалидным payload должен провалиться"
        print("     ✅ Pre-checkout отклоняет невалидные данные!")
        
        print("  💳 4. Тестирование обработки успешного платежа - КРИТИЧНО!")
        
        # Успешный платеж
        purchase = await payment_service.process_successful_payment(
            user_id=user.user_id,
            payment_charge_id="critical_test_payment_123",
            total_amount=lesson.price_stars,
            invoice_payload=payload
        )
        
        assert purchase is not None, "Покупка должна быть создана"
        assert purchase.user_id == user.user_id, "ID пользователя должен совпадать"
        assert purchase.lesson_id == lesson.id, "ID урока должен совпадать" 
        assert purchase.payment_charge_id == "critical_test_payment_123", "ID платежа должен совпадать"
        assert purchase.amount_stars == lesson.price_stars, "Сумма должна совпадать"
        assert purchase.status == "completed", "Статус должен быть 'completed'"
        
        print("     ✅ Обработка успешного платежа работает!")
        
        print("  💳 5. Проверка предоставления доступа после оплаты - КРИТИЧНО!")
        
        # Проверка доступа к уроку после покупки
        lesson_service = LessonService(session)
        has_access = await lesson_service.check_user_has_lesson(user.user_id, lesson.id)
        assert has_access is True, "Пользователь должен получить доступ после покупки"
        print("     ✅ Доступ предоставляется корректно!")
        
        print("  💳 6. Тестирование защиты от повторной обработки платежа...")
        
        # Попытка повторной обработки того же платежа
        duplicate_purchase = await payment_service.process_successful_payment(
            user_id=user.user_id,
            payment_charge_id="critical_test_payment_123",  # Тот же charge_id
            total_amount=lesson.price_stars,
            invoice_payload=payload
        )
        
        assert duplicate_purchase is None, "Повторная обработка должна быть заблокирована"
        print("     ✅ Защита от дублированных платежей работает!")
        
        print("  💳 7. Тестирование обновления баланса пользователя...")
        
        # Проверка обновления баланса
        user_service = UserService(session)
        updated_user = await user_service.get_user_by_telegram_id(user.user_id)
        assert updated_user.total_spent == lesson.price_stars, "Баланс пользователя должен обновиться"
        print("     ✅ Баланс пользователя обновляется корректно!")
        
        print("  💳 8. Тестирование валидации уже купленного урока...")
        
        # Попытка купить уже приобретенный урок
        is_valid, error_msg, lesson_data = await payment_service.validate_payment_data(
            user.user_id, lesson.id
        )
        
        assert is_valid is False, "Валидация уже купленного урока должна провалиться"
        assert error_msg == "Урок уже приобретен", "Должна быть правильная ошибка"
        print("     ✅ Защита от повторной покупки работает!")
    
    await engine.dispose()
    print("🎉 ВСЕ КРИТИЧНЫЕ ТЕСТЫ PaymentService ПРОЙДЕНЫ УСПЕШНО!")

async def main():
    """Запуск критичного тестирования"""
    print("💳 ЗАПУСК КРИТИЧНОГО ТЕСТИРОВАНИЯ ПЛАТЕЖНОЙ СИСТЕМЫ...\n")
    
    try:
        await test_payment_service()
        print()
        
        print("🎉💳🎉 ПЛАТЕЖНАЯ СИСТЕМА РАБОТАЕТ КОРРЕКТНО! 🎉💳🎉")
        print("✅ Валидация платежных данных")
        print("✅ Создание инвойсов")
        print("✅ Pre-checkout валидация")
        print("✅ Обработка успешных платежей")
        print("✅ Предоставление доступа к урокам")
        print("✅ Защита от дублированных платежей")
        print("✅ Обновление баланса пользователей")
        print("✅ Защита от повторных покупок")
        print()
        print("💰 Система готова к обработке реальных платежей Telegram Stars!")
        
    except Exception as e:
        print(f"❌ КРИТИЧНАЯ ОШИБКА В ПЛАТЕЖНОЙ СИСТЕМЕ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())