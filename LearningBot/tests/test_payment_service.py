"""
Тесты для сервиса платежей (критичная функциональность)
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from services.payment import PaymentService
from database.models import Purchase, Lesson, User


class TestPaymentService:
    """Тесты для PaymentService - самая критичная часть"""

    @pytest.mark.asyncio
    async def test_validate_payment_data_valid(self, payment_service, sample_user, sample_lesson):
        """Тест валидации корректных платежных данных"""
        is_valid, error_msg, lesson_data = await payment_service.validate_payment_data(
            sample_user.user_id,
            sample_lesson.id
        )
        
        assert is_valid is True
        assert error_msg is None
        assert lesson_data is not None
        assert lesson_data["id"] == sample_lesson.id
        assert lesson_data["title"] == sample_lesson.title
        assert lesson_data["price_stars"] == sample_lesson.price_stars

    @pytest.mark.asyncio
    async def test_validate_payment_data_nonexistent_lesson(self, payment_service, sample_user):
        """Тест валидации с несуществующим уроком"""
        is_valid, error_msg, lesson_data = await payment_service.validate_payment_data(
            sample_user.user_id,
            999999  # Несуществующий урок
        )
        
        assert is_valid is False
        assert error_msg == "Урок не найден"
        assert lesson_data is None

    @pytest.mark.asyncio
    async def test_validate_payment_data_free_lesson(self, payment_service, sample_user, sample_free_lesson):
        """Тест валидации бесплатного урока (должна вернуть ошибку)"""
        is_valid, error_msg, lesson_data = await payment_service.validate_payment_data(
            sample_user.user_id,
            sample_free_lesson.id
        )
        
        assert is_valid is False
        assert error_msg == "Этот урок бесплатный"
        assert lesson_data is None

    @pytest.mark.asyncio
    async def test_validate_payment_data_already_purchased(self, payment_service, sample_user, sample_lesson, sample_purchase):
        """Тест валидации уже купленного урока"""
        is_valid, error_msg, lesson_data = await payment_service.validate_payment_data(
            sample_user.user_id,
            sample_lesson.id
        )
        
        assert is_valid is False
        assert error_msg == "Урок уже приобретен"
        assert lesson_data is None

    @pytest.mark.asyncio
    async def test_create_invoice_success(self, payment_service, sample_user, sample_lesson):
        """Тест успешного создания инвойса"""
        # Настраиваем мок бота
        payment_service.bot.send_invoice.return_value = True
        
        result = await payment_service.create_invoice(
            user_id=sample_user.user_id,
            lesson_id=sample_lesson.id,
            lesson_title=sample_lesson.title,
            lesson_description=sample_lesson.description,
            price_stars=sample_lesson.price_stars
        )
        
        assert result is True
        
        # Проверяем, что send_invoice был вызван с правильными параметрами
        payment_service.bot.send_invoice.assert_called_once()
        call_args = payment_service.bot.send_invoice.call_args
        
        assert call_args[1]['chat_id'] == sample_user.user_id
        assert call_args[1]['title'] == sample_lesson.title
        assert call_args[1]['currency'] == "XTR"
        assert len(call_args[1]['prices']) == 1
        assert call_args[1]['prices'][0].amount == sample_lesson.price_stars

    @pytest.mark.asyncio
    async def test_create_invoice_bot_error(self, payment_service, sample_user, sample_lesson):
        """Тест создания инвойса при ошибке бота"""
        # Настраиваем мок для выброса исключения
        payment_service.bot.send_invoice.side_effect = Exception("Bot API Error")
        
        result = await payment_service.create_invoice(
            user_id=sample_user.user_id,
            lesson_id=sample_lesson.id,
            lesson_title=sample_lesson.title,
            lesson_description=sample_lesson.description,
            price_stars=sample_lesson.price_stars
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_process_pre_checkout_valid(self, payment_service, sample_user, sample_lesson):
        """Тест обработки валидного pre-checkout"""
        # Формируем валидный payload
        payload = f"lesson_{sample_lesson.id}_{sample_user.user_id}_1672531200"
        
        is_valid, error_msg = await payment_service.process_pre_checkout(
            pre_checkout_query_id="test_query_123",
            user_id=sample_user.user_id,
            total_amount=sample_lesson.price_stars,
            invoice_payload=payload
        )
        
        assert is_valid is True
        assert error_msg is None

    @pytest.mark.asyncio
    async def test_process_pre_checkout_invalid_payload(self, payment_service, sample_user, sample_lesson):
        """Тест pre-checkout с невалидным payload"""
        invalid_payload = "invalid_payload_format"
        
        is_valid, error_msg = await payment_service.process_pre_checkout(
            pre_checkout_query_id="test_query_123",
            user_id=sample_user.user_id,
            total_amount=sample_lesson.price_stars,
            invoice_payload=invalid_payload
        )
        
        assert is_valid is False
        assert error_msg == "Некорректные данные платежа"

    @pytest.mark.asyncio
    async def test_process_pre_checkout_wrong_amount(self, payment_service, sample_user, sample_lesson):
        """Тест pre-checkout с неправильной суммой"""
        payload = f"lesson_{sample_lesson.id}_{sample_user.user_id}_1672531200"
        wrong_amount = sample_lesson.price_stars + 50  # Неправильная сумма
        
        is_valid, error_msg = await payment_service.process_pre_checkout(
            pre_checkout_query_id="test_query_123",
            user_id=sample_user.user_id,
            total_amount=wrong_amount,
            invoice_payload=payload
        )
        
        assert is_valid is False
        assert f"Некорректная сумма. Ожидается {sample_lesson.price_stars} звезд" in error_msg

    @pytest.mark.asyncio
    async def test_process_successful_payment_success(self, payment_service, sample_user, sample_lesson, sample_telegram_payment):
        """Тест успешной обработки платежа - КРИТИЧНЫЙ ТЕСТ"""
        # Формируем payload для нашего урока
        payload = f"lesson_{sample_lesson.id}_{sample_user.user_id}_1672531200"
        
        purchase = await payment_service.process_successful_payment(
            user_id=sample_user.user_id,
            payment_charge_id=sample_telegram_payment["telegram_payment_charge_id"],
            total_amount=sample_lesson.price_stars,
            invoice_payload=payload
        )
        
        assert purchase is not None
        assert purchase.user_id == sample_user.user_id
        assert purchase.lesson_id == sample_lesson.id
        assert purchase.payment_charge_id == sample_telegram_payment["telegram_payment_charge_id"]
        assert purchase.amount_stars == sample_lesson.price_stars
        assert purchase.status == "completed"
        
        # Проверяем, что пользователь получил доступ
        from services.lesson import LessonService
        lesson_service = LessonService(payment_service.session)
        has_access = await lesson_service.check_user_has_lesson(sample_user.user_id, sample_lesson.id)
        assert has_access is True

    @pytest.mark.asyncio
    async def test_process_successful_payment_invalid_payload(self, payment_service, sample_user, sample_telegram_payment):
        """Тест обработки платежа с невалидным payload"""
        invalid_payload = "invalid_format"
        
        purchase = await payment_service.process_successful_payment(
            user_id=sample_user.user_id,
            payment_charge_id=sample_telegram_payment["telegram_payment_charge_id"],
            total_amount=100,
            invoice_payload=invalid_payload
        )
        
        assert purchase is None

    @pytest.mark.asyncio
    async def test_process_successful_payment_nonexistent_lesson(self, payment_service, sample_user, sample_telegram_payment):
        """Тест обработки платежа за несуществующий урок"""
        payload = f"lesson_999999_{sample_user.user_id}_1672531200"
        
        purchase = await payment_service.process_successful_payment(
            user_id=sample_user.user_id,
            payment_charge_id=sample_telegram_payment["telegram_payment_charge_id"],
            total_amount=100,
            invoice_payload=payload
        )
        
        assert purchase is None

    @pytest.mark.asyncio
    async def test_process_successful_payment_duplicate_charge_id(self, payment_service, sample_user, sample_lesson, sample_telegram_payment):
        """Тест обработки платежа с дублированным charge_id (защита от повторной обработки)"""
        payload = f"lesson_{sample_lesson.id}_{sample_user.user_id}_1672531200"
        
        # Первый платеж
        purchase1 = await payment_service.process_successful_payment(
            user_id=sample_user.user_id,
            payment_charge_id=sample_telegram_payment["telegram_payment_charge_id"],
            total_amount=sample_lesson.price_stars,
            invoice_payload=payload
        )
        
        # Второй платеж с тем же charge_id
        purchase2 = await payment_service.process_successful_payment(
            user_id=sample_user.user_id,
            payment_charge_id=sample_telegram_payment["telegram_payment_charge_id"],  # Тот же ID
            total_amount=sample_lesson.price_stars,
            invoice_payload=payload
        )
        
        assert purchase1 is not None
        assert purchase2 is None  # Второй должен быть отклонен

    @pytest.mark.asyncio
    async def test_update_user_balance_after_purchase(self, payment_service, sample_user, sample_lesson):
        """Тест обновления баланса пользователя после покупки"""
        payload = f"lesson_{sample_lesson.id}_{sample_user.user_id}_1672531200"
        initial_spent = sample_user.total_spent
        
        purchase = await payment_service.process_successful_payment(
            user_id=sample_user.user_id,
            payment_charge_id="unique_charge_123",
            total_amount=sample_lesson.price_stars,
            invoice_payload=payload
        )
        
        assert purchase is not None
        
        # Проверяем обновление баланса пользователя
        from services.user import UserService
        user_service = UserService(payment_service.session)
        updated_user = await user_service.get_user_by_telegram_id(sample_user.user_id)
        
        assert updated_user.total_spent == initial_spent + sample_lesson.price_stars

    @pytest.mark.asyncio
    async def test_get_star_balance_mock(self, payment_service):
        """Тест получения баланса звезд (с моком)"""
        # Настраиваем мок ответа
        mock_response = MagicMock()
        mock_response.star_count = 500
        payment_service.bot.get_my_star_balance.return_value = mock_response
        
        balance = await payment_service.get_star_balance()
        
        assert balance == 500

    @pytest.mark.asyncio
    async def test_get_star_balance_api_error(self, payment_service):
        """Тест получения баланса при ошибке API"""
        payment_service.bot.get_my_star_balance.side_effect = Exception("API Error")
        
        balance = await payment_service.get_star_balance()
        
        assert balance is None