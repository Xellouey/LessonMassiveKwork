"""
Интеграционные тесты для критических бизнес-процессов
"""
import pytest
from datetime import datetime

from services.user import UserService
from services.lesson import LessonService
from services.payment import PaymentService
from database.models import User, Lesson, Purchase


class TestLessonPurchaseFlow:
    """Интеграционные тесты полного цикла покупки урока"""

    @pytest.fixture
    async def clean_user(self, db_session):
        """Создание чистого пользователя без покупок"""
        user = User(
            user_id=555666777,
            username="clean_user",
            full_name="Чистый Пользователь",
            registration_date=datetime.utcnow(),
            is_active=True,
            language='ru',
            total_spent=0,
            last_activity=datetime.utcnow()
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.fixture
    async def premium_lesson(self, db_session):
        """Создание платного урока для тестирования"""
        lesson = Lesson(
            title="Премиум урок",
            description="Платный урок для тестирования покупки",
            price_stars=250,
            content_type="video",
            file_id="premium_video_123",
            duration=600,  # 10 минут
            is_active=True,
            is_free=False,
            category="Премиум",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            views_count=0
        )
        
        db_session.add(lesson)
        await db_session.commit()
        await db_session.refresh(lesson)
        return lesson

    @pytest.mark.asyncio
    async def test_complete_lesson_purchase_flow(self, db_session, clean_user, premium_lesson, mock_bot):
        """
        КРИТИЧНЫЙ ИНТЕГРАЦИОННЫЙ ТЕСТ: 
        Полный цикл покупки урока от проверки доступа до предоставления контента
        """
        # Инициализация сервисов
        user_service = UserService(db_session)
        lesson_service = LessonService(db_session)
        payment_service = PaymentService(db_session, mock_bot)
        
        # Настройка мока бота
        mock_bot.send_invoice.return_value = True
        
        # ЭТАП 1: Проверка изначального отсутствия доступа
        initial_access = await lesson_service.check_user_has_lesson(
            clean_user.user_id, 
            premium_lesson.id
        )
        assert initial_access is False, "Пользователь не должен иметь доступ до покупки"
        
        # ЭТАП 2: Валидация данных для покупки
        is_valid, error_msg, lesson_data = await payment_service.validate_payment_data(
            clean_user.user_id,
            premium_lesson.id
        )
        assert is_valid is True, f"Данные для покупки должны быть валидными: {error_msg}"
        assert lesson_data["price_stars"] == premium_lesson.price_stars
        
        # ЭТАП 3: Создание инвойса
        invoice_created = await payment_service.create_invoice(
            user_id=clean_user.user_id,
            lesson_id=premium_lesson.id,
            lesson_title=premium_lesson.title,
            lesson_description=premium_lesson.description,
            price_stars=premium_lesson.price_stars
        )
        assert invoice_created is True, "Инвойс должен быть создан успешно"
        
        # ЭТАП 4: Pre-checkout validation
        payload = f"lesson_{premium_lesson.id}_{clean_user.user_id}_1672531200"
        pre_checkout_valid, pre_error = await payment_service.process_pre_checkout(
            pre_checkout_query_id="integration_test_query",
            user_id=clean_user.user_id,
            total_amount=premium_lesson.price_stars,
            invoice_payload=payload
        )
        assert pre_checkout_valid is True, f"Pre-checkout должен пройти валидацию: {pre_error}"
        
        # ЭТАП 5: Обработка успешного платежа
        purchase = await payment_service.process_successful_payment(
            user_id=clean_user.user_id,
            payment_charge_id="integration_test_payment_123",
            total_amount=premium_lesson.price_stars,
            invoice_payload=payload
        )
        
        assert purchase is not None, "Покупка должна быть создана"
        assert purchase.user_id == clean_user.user_id
        assert purchase.lesson_id == premium_lesson.id
        assert purchase.status == "completed"
        assert purchase.amount_stars == premium_lesson.price_stars
        
        # ЭТАП 6: Проверка предоставления доступа
        final_access = await lesson_service.check_user_has_lesson(
            clean_user.user_id, 
            premium_lesson.id
        )
        assert final_access is True, "Пользователь должен получить доступ после покупки"
        
        # ЭТАП 7: Проверка обновления баланса пользователя
        updated_user = await user_service.get_user_by_telegram_id(clean_user.user_id)
        assert updated_user.total_spent == premium_lesson.price_stars, "Баланс пользователя должен обновиться"
        
        # ЭТАП 8: Проверка появления в списке покупок
        purchases, total_count = await lesson_service.get_user_purchases(clean_user.user_id)
        assert total_count == 1, "У пользователя должна быть одна покупка"
        assert purchases[0]['lesson'].id == premium_lesson.id
        
        # ЭТАП 9: Логирование активности
        await user_service.log_user_activity(
            clean_user.user_id,
            "lesson_purchased",
            lesson_id=premium_lesson.id,
            extra_data=f"amount:{premium_lesson.price_stars}"
        )

    @pytest.mark.asyncio
    async def test_prevent_double_purchase(self, db_session, clean_user, premium_lesson, mock_bot):
        """
        Тест защиты от двойной покупки одного урока
        """
        user_service = UserService(db_session)
        lesson_service = LessonService(db_session)
        payment_service = PaymentService(db_session, mock_bot)
        
        # Первая покупка
        payload = f"lesson_{premium_lesson.id}_{clean_user.user_id}_1672531200"
        first_purchase = await payment_service.process_successful_payment(
            user_id=clean_user.user_id,
            payment_charge_id="first_payment_123",
            total_amount=premium_lesson.price_stars,
            invoice_payload=payload
        )
        assert first_purchase is not None
        
        # Попытка второй покупки того же урока
        is_valid, error_msg, lesson_data = await payment_service.validate_payment_data(
            clean_user.user_id,
            premium_lesson.id
        )
        
        assert is_valid is False, "Повторная покупка должна быть заблокирована"
        assert error_msg == "Урок уже приобретен"

    @pytest.mark.asyncio
    async def test_free_lesson_access_without_purchase(self, db_session, clean_user, sample_free_lesson):
        """
        Тест доступа к бесплатным урокам без покупки
        """
        lesson_service = LessonService(db_session)
        
        # Проверка доступа к бесплатному уроку
        has_access = await lesson_service.check_user_has_lesson(
            clean_user.user_id,
            sample_free_lesson.id
        )
        
        assert has_access is True, "Бесплатные уроки должны быть доступны всем"
        
        # Проверка, что валидация платежа отклоняет бесплатные уроки
        user_service = UserService(db_session)
        payment_service = PaymentService(db_session, None)
        
        is_valid, error_msg, lesson_data = await payment_service.validate_payment_data(
            clean_user.user_id,
            sample_free_lesson.id
        )
        
        assert is_valid is False
        assert error_msg == "Этот урок бесплатный"

    @pytest.mark.asyncio
    async def test_lesson_views_increment_on_access(self, db_session, clean_user, premium_lesson, mock_bot):
        """
        Тест увеличения счетчика просмотров при просмотре купленного урока
        """
        user_service = UserService(db_session)
        lesson_service = LessonService(db_session)
        payment_service = PaymentService(db_session, mock_bot)
        
        # Покупка урока
        payload = f"lesson_{premium_lesson.id}_{clean_user.user_id}_1672531200"
        purchase = await payment_service.process_successful_payment(
            user_id=clean_user.user_id,
            payment_charge_id="views_test_payment",
            total_amount=premium_lesson.price_stars,
            invoice_payload=payload
        )
        assert purchase is not None
        
        initial_views = premium_lesson.views_count
        
        # Симуляция просмотра урока
        success = await lesson_service.increment_lesson_views(premium_lesson.id)
        assert success is True
        
        # Проверка увеличения счетчика
        updated_lesson = await lesson_service.get_lesson_by_id(premium_lesson.id)
        assert updated_lesson.views_count == initial_views + 1
        
        # Логирование просмотра
        await user_service.log_user_activity(
            clean_user.user_id,
            "lesson_viewed",
            lesson_id=premium_lesson.id
        )

    @pytest.mark.asyncio
    async def test_multiple_lessons_purchase(self, db_session, clean_user, premium_lesson, mock_bot):
        """
        Тест покупки нескольких уроков одним пользователем
        """
        lesson_service = LessonService(db_session)
        payment_service = PaymentService(db_session, mock_bot)
        
        # Создание второго урока
        second_lesson = Lesson(
            title="Второй урок",
            description="Второй платный урок",
            price_stars=150,
            content_type="audio",
            file_id="second_audio_456",
            is_active=True,
            is_free=False,
            category="Аудио"
        )
        
        db_session.add(second_lesson)
        await db_session.commit()
        await db_session.refresh(second_lesson)
        
        # Покупка первого урока
        payload1 = f"lesson_{premium_lesson.id}_{clean_user.user_id}_1672531200"
        purchase1 = await payment_service.process_successful_payment(
            user_id=clean_user.user_id,
            payment_charge_id="multi_payment_1",
            total_amount=premium_lesson.price_stars,
            invoice_payload=payload1
        )
        
        # Покупка второго урока
        payload2 = f"lesson_{second_lesson.id}_{clean_user.user_id}_1672531201"
        purchase2 = await payment_service.process_successful_payment(
            user_id=clean_user.user_id,
            payment_charge_id="multi_payment_2",
            total_amount=second_lesson.price_stars,
            invoice_payload=payload2
        )
        
        assert purchase1 is not None
        assert purchase2 is not None
        
        # Проверка доступа к обоим урокам
        access1 = await lesson_service.check_user_has_lesson(clean_user.user_id, premium_lesson.id)
        access2 = await lesson_service.check_user_has_lesson(clean_user.user_id, second_lesson.id)
        
        assert access1 is True
        assert access2 is True
        
        # Проверка общего количества покупок
        purchases, total_count = await lesson_service.get_user_purchases(clean_user.user_id)
        assert total_count == 2
        
        # Проверка общих трат пользователя
        user_service = UserService(db_session)
        updated_user = await user_service.get_user_by_telegram_id(clean_user.user_id)
        expected_total = premium_lesson.price_stars + second_lesson.price_stars
        assert updated_user.total_spent == expected_total