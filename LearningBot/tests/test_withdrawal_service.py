"""
Тесты для сервиса вывода средств
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Admin, WithdrawalRequest
from services.withdrawal import WithdrawalService


class TestWithdrawalService:
    """Тесты для WithdrawalService"""

    @pytest.fixture
    async def withdrawal_service(self, db_session):
        """Фикстура для создания WithdrawalService"""
        return WithdrawalService(db_session)

    @pytest.fixture
    async def sample_admin(self):
        """Создание тестового администратора"""
        return Admin(
            user_id=12345,
            username="test_admin",
            permissions="all",
            is_active=True
        )

    @pytest.fixture
    async def sample_withdrawal_request(self, sample_admin):
        """Создание тестового запроса на вывод"""
        return WithdrawalRequest(
            id=1,
            admin_id=sample_admin.user_id,
            amount_stars=1000,
            wallet_address="TON_WALLET_ADDRESS",
            status="pending",
            commission_amount=50,
            net_amount=950,
            notes="Тестовый вывод"
        )

    async def test_create_withdrawal_request(self, withdrawal_service, db_session, sample_admin):
        """Тест создания запроса на вывод средств"""
        db_session.add = MagicMock()
        db_session.commit = AsyncMock()

        result = await withdrawal_service.create_withdrawal_request(
            admin_id=sample_admin.user_id,
            amount_stars=1000,
            wallet_address="TON_WALLET_ADDRESS",
            notes="Тестовый вывод"
        )

        assert result is not None
        assert result.admin_id == sample_admin.user_id
        assert result.amount_stars == 1000
        assert result.wallet_address == "TON_WALLET_ADDRESS"
        assert result.status == "pending"
        assert result.commission_amount > 0  # Комиссия должна быть рассчитана
        assert result.net_amount < result.amount_stars  # С учетом комиссии
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()

    async def test_get_withdrawal_requests_by_admin(self, withdrawal_service, db_session, sample_withdrawal_request):
        """Тест получения запросов на вывод по администратору"""
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all.return_value = [sample_withdrawal_request]
        mock_result.scalars.return_value = mock_scalars

        with patch.object(db_session, 'execute', return_value=mock_result):
            requests = await withdrawal_service.get_withdrawal_requests_by_admin(12345)

            assert len(requests) == 1
            assert requests[0].admin_id == 12345
            assert requests[0].amount_stars == 1000

    async def test_get_withdrawal_request_by_id(self, withdrawal_service, db_session, sample_withdrawal_request):
        """Тест получения запроса на вывод по ID"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_withdrawal_request

        with patch.object(db_session, 'execute', return_value=mock_result):
            request = await withdrawal_service.get_withdrawal_request_by_id(1)

            assert request is not None
            assert request.id == 1
            assert request.amount_stars == 1000

    async def test_calculate_commission(self, withdrawal_service):
        """Тест расчета комиссии"""
        # Тест базовой комиссии 5%
        commission = withdrawal_service.calculate_commission(1000)
        assert commission == 50  # 5% от 1000

        # Тест минимальной комиссии
        commission = withdrawal_service.calculate_commission(100)
        assert commission >= 10  # Минимальная комиссия

        # Тест большой суммы
        commission = withdrawal_service.calculate_commission(10000)
        expected = 10000 * 0.05  # 5%
        assert commission == expected

    async def test_validate_wallet_address(self, withdrawal_service):
        """Тест валидации адреса кошелька"""
        # Валидные адреса
        valid_addresses = [
            "EQA0i8-CdGnF_DhUHHf92R1ONH6sIA9vLZ_WLcCIhfBBXwtG",
            "UQBP4mzjGVB9q8V4V4V4V4V4V4V4V4V4V4V4V4V4V4V4V4V4",
            "0QA0i8-CdGnF_DhUHHf92R1ONH6sIA9vLZ_WLcCIhfBBXwtG"
        ]

        for address in valid_addresses:
            assert withdrawal_service.validate_wallet_address(address) is True

        # Невалидные адреса
        invalid_addresses = [
            "invalid_address",
            "",
            "TON123",
            "short",
            None
        ]

        for address in invalid_addresses:
            assert withdrawal_service.validate_wallet_address(address) is False

    async def test_update_withdrawal_status(self, withdrawal_service, db_session, sample_withdrawal_request):
        """Тест обновления статуса запроса на вывод"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_withdrawal_request
        db_session.commit = AsyncMock()

        with patch.object(db_session, 'execute', return_value=mock_result):
            result = await withdrawal_service.update_withdrawal_status(
                request_id=1,
                status="completed",
                transaction_id="TXN123456789"
            )

            assert result is not None
            assert result.status == "completed"
            assert result.transaction_id == "TXN123456789"
            assert result.processed_date is not None
            db_session.commit.assert_called_once()

    async def test_cancel_withdrawal_request(self, withdrawal_service, db_session, sample_withdrawal_request):
        """Тест отмены запроса на вывод"""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_withdrawal_request
        db_session.commit = AsyncMock()

        with patch.object(db_session, 'execute', return_value=mock_result):
            result = await withdrawal_service.cancel_withdrawal_request(
                request_id=1,
                reason="Отменено пользователем"
            )

            assert result is True
            assert sample_withdrawal_request.status == "cancelled"
            assert sample_withdrawal_request.failure_reason == "Отменено пользователем"
            db_session.commit.assert_called_once()

    async def test_get_withdrawal_statistics(self, withdrawal_service, db_session):
        """Тест получения статистики выводов"""
        # Мокируем различные запросы статистики
        total_mock = AsyncMock()
        total_mock.scalar.return_value = 5

        pending_mock = AsyncMock()
        pending_mock.scalar.return_value = 2

        completed_mock = AsyncMock()
        completed_mock.scalar.return_value = 3

        total_amount_mock = AsyncMock()
        total_amount_mock.scalar.return_value = 5000

        commission_mock = AsyncMock()
        commission_mock.scalar.return_value = 250

        with patch.object(db_session, 'execute', side_effect=[
            total_mock, pending_mock, completed_mock, total_amount_mock, commission_mock
        ]):
            stats = await withdrawal_service.get_withdrawal_statistics()

            assert stats['total_requests'] == 5
            assert stats['pending_requests'] == 2
            assert stats['completed_requests'] == 3
            assert stats['total_amount'] == 5000
            assert stats['total_commission'] == 250

    async def test_get_pending_withdrawals(self, withdrawal_service, db_session, sample_withdrawal_request):
        """Тест получения ожидающих запросов на вывод"""
        sample_withdrawal_request.status = "pending"
        
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all.return_value = [sample_withdrawal_request]
        mock_result.scalars.return_value = mock_scalars

        with patch.object(db_session, 'execute', return_value=mock_result):
            pending = await withdrawal_service.get_pending_withdrawals()

            assert len(pending) == 1
            assert pending[0].status == "pending"

    async def test_process_withdrawal_telegram_wallet(self, withdrawal_service, sample_withdrawal_request):
        """Тест обработки вывода через Telegram Wallet API"""
        # Мокируем успешный вызов API
        with patch.object(withdrawal_service, '_call_telegram_wallet_api') as mock_api:
            mock_api.return_value = {
                'success': True,
                'transaction_id': 'TXN123456789'
            }

            result = await withdrawal_service.process_withdrawal_telegram_wallet(sample_withdrawal_request)

            assert result['success'] is True
            assert result['transaction_id'] == 'TXN123456789'
            mock_api.assert_called_once()

    async def test_process_withdrawal_telegram_wallet_failure(self, withdrawal_service, sample_withdrawal_request):
        """Тест неудачной обработки вывода через Telegram Wallet API"""
        # Мокируем неудачный вызов API
        with patch.object(withdrawal_service, '_call_telegram_wallet_api') as mock_api:
            mock_api.return_value = {
                'success': False,
                'error': 'Insufficient funds'
            }

            result = await withdrawal_service.process_withdrawal_telegram_wallet(sample_withdrawal_request)

            assert result['success'] is False
            assert 'error' in result
            mock_api.assert_called_once()

    async def test_validate_admin_balance(self, withdrawal_service, db_session):
        """Тест проверки баланса администратора"""
        # Мокируем запрос статистики продаж
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 5000  # Общий доход в звездах

        with patch.object(db_session, 'execute', return_value=mock_result):
            available_balance = await withdrawal_service.validate_admin_balance(12345)

            assert available_balance == 5000

    async def test_get_withdrawal_history(self, withdrawal_service, db_session, sample_withdrawal_request):
        """Тест получения истории выводов"""
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all.return_value = [sample_withdrawal_request]
        mock_result.scalars.return_value = mock_scalars

        with patch.object(db_session, 'execute', return_value=mock_result):
            history = await withdrawal_service.get_withdrawal_history(limit=10)

            assert len(history) == 1
            assert history[0].id == sample_withdrawal_request.id

    async def test_error_handling_in_create_withdrawal(self, withdrawal_service, db_session):
        """Тест обработки ошибок при создании запроса на вывод"""
        db_session.add = MagicMock()
        db_session.commit = AsyncMock(side_effect=Exception("Database error"))
        db_session.rollback = AsyncMock()

        result = await withdrawal_service.create_withdrawal_request(
            admin_id=12345,
            amount_stars=1000,
            wallet_address="INVALID",
            notes="Test"
        )

        assert result is None
        db_session.rollback.assert_called_once()

    async def test_minimum_withdrawal_amount(self, withdrawal_service):
        """Тест минимальной суммы для вывода"""
        # Проверяем, что сумма меньше минимальной отклоняется
        assert withdrawal_service.validate_withdrawal_amount(50) is False  # Меньше минимума
        assert withdrawal_service.validate_withdrawal_amount(100) is True   # Минимальная сумма
        assert withdrawal_service.validate_withdrawal_amount(1000) is True  # Нормальная сумма

    async def test_daily_withdrawal_limit(self, withdrawal_service, db_session):
        """Тест дневного лимита выводов"""
        # Мокируем сумму выводов за сегодня
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 5000  # Уже выведено за день

        with patch.object(db_session, 'execute', return_value=mock_result):
            can_withdraw = await withdrawal_service.check_daily_limit(12345, 2000)
            
            # Если дневной лимит 10000, то 5000 + 2000 = 7000 < 10000 - можно
            assert can_withdraw is True

            # Но если пытаемся вывести 6000, то 5000 + 6000 = 11000 > 10000 - нельзя
            can_withdraw = await withdrawal_service.check_daily_limit(12345, 6000)
            assert can_withdraw is False

    async def test_withdrawal_request_validation(self, withdrawal_service):
        """Тест валидации данных запроса на вывод"""
        # Валидные данные
        valid_data = {
            'amount_stars': 1000,
            'wallet_address': 'EQA0i8-CdGnF_DhUHHf92R1ONH6sIA9vLZ_WLcCIhfBBXwtG'
        }
        assert withdrawal_service.validate_request_data(**valid_data) is True

        # Невалидные данные
        invalid_data = [
            {'amount_stars': 50, 'wallet_address': 'valid_address'},  # Мало звезд
            {'amount_stars': 1000, 'wallet_address': 'invalid'},      # Плохой адрес
            {'amount_stars': -100, 'wallet_address': 'valid_address'}, # Отрицательная сумма
        ]

        for data in invalid_data:
            assert withdrawal_service.validate_request_data(**data) is False