"""
Тесты для обработчиков системы вывода средств
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from aiogram.types import CallbackQuery, Message, User as TelegramUser
from aiogram.fsm.context import FSMContext

from handlers.admin.withdrawal import (
    show_withdrawal_menu,
    show_balance_details,
    start_withdrawal_creation,
    process_withdrawal_amount,
    process_wallet_address,
    process_withdrawal_notes,
    confirm_withdrawal_creation,
    cancel_withdrawal_creation,
    show_my_withdrawal_requests,
    show_withdrawal_details,
    show_cancel_confirmation,
    confirm_withdrawal_cancellation,
    show_withdrawal_statistics
)
from database.models import Admin, WithdrawalRequest
from services.withdrawal import WithdrawalService
from states.admin import WithdrawalStates


class TestWithdrawalHandlers:
    """Тесты для обработчиков системы вывода средств"""

    @pytest.fixture
    async def mock_callback_query(self):
        """Мок callback query"""
        callback = AsyncMock(spec=CallbackQuery)
        callback.data = "withdrawal_menu"
        callback.message = AsyncMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        return callback

    @pytest.fixture
    async def mock_message(self):
        """Мок сообщения"""
        message = AsyncMock(spec=Message)
        message.text = "1000"
        message.answer = AsyncMock()
        message.from_user = TelegramUser(id=12345, is_bot=False, first_name="Test")
        return message

    @pytest.fixture
    async def mock_admin(self):
        """Мок администратора"""
        return Admin(
            user_id=12345,
            username="test_admin",
            permissions="all",
            is_active=True
        )

    @pytest.fixture
    async def mock_state(self):
        """Мок состояния FSM"""
        state = AsyncMock(spec=FSMContext)
        state.set_state = AsyncMock()
        state.get_data = AsyncMock(return_value={})
        state.update_data = AsyncMock()
        state.clear = AsyncMock()
        return state

    @pytest.fixture
    async def mock_withdrawal_service(self):
        """Мок сервиса вывода средств"""
        service = AsyncMock(spec=WithdrawalService)
        service.min_withdrawal_amount = 100
        service.commission_rate = 0.05
        service.min_commission = 10
        service.daily_limit = 10000
        service.validate_admin_balance = AsyncMock(return_value=5000)
        service.get_withdrawal_requests_by_admin = AsyncMock(return_value=[])
        service.calculate_commission = MagicMock(return_value=50)
        service.validate_wallet_address = MagicMock(return_value=True)
        service.check_daily_limit = AsyncMock(return_value=True)
        service.create_withdrawal_request = AsyncMock()
        service.get_withdrawal_request_by_id = AsyncMock()
        service.cancel_withdrawal_request = AsyncMock(return_value=True)
        service.get_withdrawal_statistics_by_admin = AsyncMock(return_value={
            'total_requests': 5,
            'completed_requests': 3,
            'pending_requests': 2,
            'total_withdrawn': 10000,
            'total_commission': 500,
            'net_received': 9500,
            'average_amount': 3333
        })
        return service

    async def test_show_withdrawal_menu(self, mock_callback_query, mock_admin, mock_state, db_session):
        """Тест показа главного меню вывода средств"""
        with patch('handlers.admin.withdrawal.WithdrawalService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.validate_admin_balance.return_value = 5000
            mock_service.get_withdrawal_requests_by_admin.return_value = []
            mock_service.min_withdrawal_amount = 100
            mock_service.commission_rate = 0.05
            mock_service.min_commission = 10
            mock_service.daily_limit = 10000
            mock_service_class.return_value = mock_service

            await show_withdrawal_menu(mock_callback_query, db_session, mock_admin, mock_state)

            # Проверяем, что был вызван edit_text
            mock_callback_query.message.edit_text.assert_called_once()
            
            # Проверяем, что текст содержит информацию о балансе
            call_args = mock_callback_query.message.edit_text.call_args[0][0]
            assert "5,000 ⭐" in call_args
            assert "Система вывода средств" in call_args

            # Проверяем, что было установлено состояние
            mock_state.set_state.assert_called_once_with(WithdrawalStates.in_withdrawal_menu)

    async def test_show_balance_details(self, mock_callback_query, mock_admin, db_session):
        """Тест показа деталей баланса"""
        with patch('handlers.admin.withdrawal.WithdrawalService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.validate_admin_balance.return_value = 7500
            mock_service.min_withdrawal_amount = 100
            mock_service.commission_rate = 0.05
            mock_service.min_commission = 10
            mock_service.daily_limit = 10000
            mock_service_class.return_value = mock_service

            await show_balance_details(mock_callback_query, db_session, mock_admin)

            # Проверяем, что был вызван edit_text
            mock_callback_query.message.edit_text.assert_called_once()
            
            # Проверяем, что текст содержит детали баланса
            call_args = mock_callback_query.message.edit_text.call_args[0][0]
            assert "7,500 ⭐" in call_args
            assert "Детали баланса" in call_args

    async def test_start_withdrawal_creation_insufficient_balance(self, mock_callback_query, mock_admin, mock_state, db_session):
        """Тест создания запроса с недостаточным балансом"""
        with patch('handlers.admin.withdrawal.WithdrawalService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.validate_admin_balance.return_value = 50  # Меньше минимальной суммы
            mock_service.min_withdrawal_amount = 100
            mock_service_class.return_value = mock_service

            await start_withdrawal_creation(mock_callback_query, db_session, mock_admin, mock_state)

            # Проверяем, что показано сообщение об ошибке
            call_args = mock_callback_query.message.edit_text.call_args[0][0]
            assert "Недостаточно средств" in call_args

    async def test_start_withdrawal_creation_success(self, mock_callback_query, mock_admin, mock_state, db_session):
        """Тест успешного начала создания запроса"""
        with patch('handlers.admin.withdrawal.WithdrawalService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.validate_admin_balance.return_value = 5000
            mock_service.min_withdrawal_amount = 100
            mock_service.daily_limit = 10000
            mock_service_class.return_value = mock_service

            await start_withdrawal_creation(mock_callback_query, db_session, mock_admin, mock_state)

            # Проверяем, что установлено состояние ввода суммы
            mock_state.set_state.assert_called_once_with(WithdrawalStates.entering_withdrawal_amount)
            
            # Проверяем, что сохранен доступный баланс
            mock_state.update_data.assert_called_once_with(available_balance=5000)

    async def test_process_withdrawal_amount_invalid_input(self, mock_message, mock_admin, mock_state, db_session):
        """Тест обработки некорректной суммы"""
        mock_message.text = "invalid_number"
        
        await process_withdrawal_amount(mock_message, db_session, mock_admin, mock_state)

        # Проверяем, что показано сообщение об ошибке
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "корректную сумму" in call_args

    async def test_process_withdrawal_amount_success(self, mock_message, mock_admin, mock_state, db_session):
        """Тест успешной обработки суммы"""
        mock_message.text = "1000"
        mock_state.get_data.return_value = {'available_balance': 5000}

        with patch('handlers.admin.withdrawal.WithdrawalService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.min_withdrawal_amount = 100
            mock_service.commission_rate = 0.05
            mock_service.calculate_commission.return_value = 50
            mock_service.check_daily_limit.return_value = True
            mock_service_class.return_value = mock_service

            await process_withdrawal_amount(mock_message, db_session, mock_admin, mock_state)

            # Проверяем, что установлено состояние ввода адреса
            mock_state.set_state.assert_called_once_with(WithdrawalStates.entering_wallet_address)
            
            # Проверяем, что сохранены данные о сумме
            mock_state.update_data.assert_called_once_with(
                amount=1000,
                commission=50,
                net_amount=950
            )

    async def test_process_wallet_address_invalid(self, mock_message, mock_admin, mock_state, db_session):
        """Тест обработки некорректного адреса кошелька"""
        mock_message.text = "invalid_wallet_address"

        with patch('handlers.admin.withdrawal.WithdrawalService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.validate_wallet_address.return_value = False
            mock_service_class.return_value = mock_service

            await process_wallet_address(mock_message, db_session, mock_admin, mock_state)

            # Проверяем, что показано сообщение об ошибке
            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args[0][0]
            assert "Неверный формат" in call_args

    async def test_process_wallet_address_success(self, mock_message, mock_admin, mock_state, db_session):
        """Тест успешной обработки адреса кошелька"""
        mock_message.text = "EQA0i8-CdGnF_DhUHHf92R1ONH6sIA9vLZ_WLcCIhfBBXwtG"

        with patch('handlers.admin.withdrawal.WithdrawalService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.validate_wallet_address.return_value = True
            mock_service_class.return_value = mock_service

            await process_wallet_address(mock_message, db_session, mock_admin, mock_state)

            # Проверяем, что установлено состояние ввода комментария
            mock_state.set_state.assert_called_once_with(WithdrawalStates.entering_withdrawal_notes)
            
            # Проверяем, что сохранен адрес кошелька
            mock_state.update_data.assert_called_once_with(
                wallet_address="EQA0i8-CdGnF_DhUHHf92R1ONH6sIA9vLZ_WLcCIhfBBXwtG"
            )

    async def test_process_withdrawal_notes_with_skip(self, mock_message, mock_admin, mock_state, db_session):
        """Тест обработки комментария с пропуском"""
        mock_message.text = "/skip"
        mock_state.get_data.return_value = {
            'amount': 1000,
            'commission': 50,
            'net_amount': 950,
            'wallet_address': 'EQA0i8-CdGnF_DhUHHf92R1ONH6sIA9vLZ_WLcCIhfBBXwtG'
        }

        await process_withdrawal_notes(mock_message, db_session, mock_admin, mock_state)

        # Проверяем, что установлено состояние подтверждения
        mock_state.set_state.assert_called_once_with(WithdrawalStates.confirming_withdrawal)
        
        # Проверяем, что сохранен пустой комментарий
        mock_state.update_data.assert_called_once_with(notes=None)

    async def test_confirm_withdrawal_creation_success(self, mock_callback_query, mock_admin, mock_state, db_session):
        """Тест успешного подтверждения создания запроса"""
        mock_state.get_data.return_value = {
            'amount': 1000,
            'wallet_address': 'EQA0i8-CdGnF_DhUHHf92R1ONH6sIA9vLZ_WLcCIhfBBXwtG',
            'notes': 'Test withdrawal'
        }

        # Создаем мок запроса на вывод
        mock_withdrawal_request = WithdrawalRequest(
            id=1,
            admin_id=12345,
            amount_stars=1000,
            commission_amount=50,
            net_amount=950,
            wallet_address='EQA0i8-CdGnF_DhUHHf92R1ONH6sIA9vLZ_WLcCIhfBBXwtG',
            request_date=datetime.now(timezone.utc)
        )

        with patch('handlers.admin.withdrawal.WithdrawalService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.create_withdrawal_request.return_value = mock_withdrawal_request
            mock_service_class.return_value = mock_service

            await confirm_withdrawal_creation(mock_callback_query, db_session, mock_admin, mock_state)

            # Проверяем, что был создан запрос
            mock_service.create_withdrawal_request.assert_called_once_with(
                admin_id=12345,
                amount_stars=1000,
                wallet_address='EQA0i8-CdGnF_DhUHHf92R1ONH6sIA9vLZ_WLcCIhfBBXwtG',
                notes='Test withdrawal'
            )

            # Проверяем, что состояние было очищено
            mock_state.clear.assert_called_once()

            # Проверяем успешное сообщение
            call_args = mock_callback_query.message.edit_text.call_args[0][0]
            assert "создан" in call_args
            assert "#1" in call_args

    async def test_cancel_withdrawal_creation(self, mock_callback_query, mock_state):
        """Тест отмены создания запроса"""
        await cancel_withdrawal_creation(mock_callback_query, mock_state)

        # Проверяем, что состояние было очищено
        mock_state.clear.assert_called_once()

        # Проверяем сообщение об отмене
        call_args = mock_callback_query.message.edit_text.call_args[0][0]
        assert "отменено" in call_args

    async def test_show_my_withdrawal_requests_empty(self, mock_callback_query, mock_admin, mock_state, db_session):
        """Тест показа пустой истории запросов"""
        with patch('handlers.admin.withdrawal.WithdrawalService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_withdrawal_requests_by_admin.return_value = []
            mock_service_class.return_value = mock_service

            await show_my_withdrawal_requests(mock_callback_query, db_session, mock_admin, mock_state)

            # Проверяем сообщение о пустой истории
            call_args = mock_callback_query.message.edit_text.call_args[0][0]
            assert "пока нет запросов" in call_args

    async def test_show_withdrawal_statistics(self, mock_callback_query, mock_admin, db_session):
        """Тест показа статистики по выводам"""
        with patch('handlers.admin.withdrawal.WithdrawalService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.validate_admin_balance.return_value = 7500
            mock_service.get_withdrawal_statistics_by_admin.return_value = {
                'total_requests': 5,
                'completed_requests': 3,
                'pending_requests': 2,
                'total_withdrawn': 10000,
                'total_commission': 500,
                'net_received': 9500,
                'average_amount': 3333
            }
            mock_service_class.return_value = mock_service

            await show_withdrawal_statistics(mock_callback_query, db_session, mock_admin)

            # Проверяем, что показана статистика
            call_args = mock_callback_query.message.edit_text.call_args[0][0]
            assert "Статистика выводов" in call_args
            assert "7,500 ⭐" in call_args  # Текущий баланс
            assert "5" in call_args  # Всего запросов
            assert "10,000 ⭐" in call_args  # Всего выведено

    async def test_show_withdrawal_details_not_found(self, mock_callback_query, mock_admin, db_session):
        """Тест показа деталей несуществующего запроса"""
        mock_callback_query.data = "withdrawal_details:999"

        with patch('handlers.admin.withdrawal.WithdrawalService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_withdrawal_request_by_id.return_value = None
            mock_service_class.return_value = mock_service

            await show_withdrawal_details(mock_callback_query, db_session, mock_admin)

            # Проверяем сообщение об ошибке
            mock_callback_query.answer.assert_called_once_with("❌ Запрос не найден.")

    async def test_confirm_withdrawal_cancellation_success(self, mock_callback_query, mock_admin, db_session):
        """Тест успешной отмены запроса"""
        mock_callback_query.data = "withdrawal_cancel_confirm:1"

        with patch('handlers.admin.withdrawal.WithdrawalService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.cancel_withdrawal_request.return_value = True
            mock_service_class.return_value = mock_service

            await confirm_withdrawal_cancellation(mock_callback_query, db_session, mock_admin)

            # Проверяем, что был вызван метод отмены
            mock_service.cancel_withdrawal_request.assert_called_once_with(
                1, 
                reason="Отменено пользователем"
            )

            # Проверяем успешное сообщение
            call_args = mock_callback_query.message.edit_text.call_args[0][0]
            assert "отменен" in call_args