"""
Обработчики для системы вывода средств
"""
import logging
import re
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.withdrawal import WithdrawalService
from services.admin import AdminService
from keyboards.admin import (
    withdrawal_main_keyboard,
    withdrawal_confirm_keyboard,
    withdrawal_requests_keyboard,
    withdrawal_details_keyboard,
    withdrawal_cancel_confirm_keyboard,
    admin_main_menu_keyboard
)
from states.admin import WithdrawalStates
from middlewares.admin import AdminOnlyMiddleware

logger = logging.getLogger(__name__)

# Создаем роутер только для администраторов
router = Router()
router.message.middleware(AdminOnlyMiddleware())
router.callback_query.middleware(AdminOnlyMiddleware())


@router.callback_query(F.data == "withdrawal_menu")
async def show_withdrawal_menu(callback: CallbackQuery, session: AsyncSession, admin, state: FSMContext):
    """Главное меню системы вывода средств"""
    try:
        withdrawal_service = WithdrawalService(session)
        
        # Получаем баланс администратора
        available_balance = await withdrawal_service.validate_admin_balance(admin.user_id)
        
        # Получаем количество запросов
        requests = await withdrawal_service.get_withdrawal_requests_by_admin(admin.user_id)
        pending_count = len([r for r in requests if r.status == 'pending'])
        processing_count = len([r for r in requests if r.status == 'processing'])
        
        withdrawal_text = f"""
💸 <b>Система вывода средств</b>

💰 <b>Ваш баланс:</b> {available_balance:,} ⭐
📈 <b>Статус запросов:</b>
• Ожидают обработки: {pending_count}
• В процессе: {processing_count}

ℹ️ <b>Ограничения Telegram:</b>
• 21 день удержания после получения звезд
• Требуется 2FA пароль для вывода
• Автоматическое удержание НДС по региону

Выберите действие:
"""
        
        await callback.message.edit_text(
            withdrawal_text,
            reply_markup=withdrawal_main_keyboard()
        )
        await callback.answer()
        await state.set_state(WithdrawalStates.in_withdrawal_menu)
        
    except Exception as e:
        logger.error(f"Ошибка при показе меню вывода средств: {e}")
        await callback.answer("❌ Ошибка при загрузке меню.")


@router.callback_query(F.data == "withdrawal_balance")
async def show_balance_details(callback: CallbackQuery, session: AsyncSession, admin):
    """Детальная информация о балансе"""
    try:
        withdrawal_service = WithdrawalService(session)
        
        # Получаем детальную информацию о балансе
        available_balance = await withdrawal_service.validate_admin_balance(admin.user_id)
        
        balance_text = f"""
💰 <b>Детали баланса</b>

💸 <b>Доступно для вывода:</b> {available_balance:,} ⭐

💡 <b>Условия вывода:</b>
• Минимальная сумма: {withdrawal_service.min_withdrawal_amount:,} ⭐
• Комиссия: {withdrawal_service.commission_rate*100}%
• Минимальная комиссия: {withdrawal_service.min_commission} ⭐
• Дневной лимит: {withdrawal_service.daily_limit:,} ⭐

ℹ️ Средства начисляются на Telegram Wallet в формате TON.
"""
        
        await callback.message.edit_text(
            balance_text,
            reply_markup=withdrawal_main_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе деталей баланса: {e}")
        await callback.answer("❌ Ошибка при загрузке данных.")


@router.callback_query(F.data == "withdrawal_create")
async def start_withdrawal_creation(callback: CallbackQuery, session: AsyncSession, admin, state: FSMContext):
    """Начать создание запроса на вывод"""
    try:
        withdrawal_service = WithdrawalService(session)
        
        # Проверяем доступный баланс
        available_balance = await withdrawal_service.validate_admin_balance(admin.user_id)
        
        if available_balance < withdrawal_service.min_withdrawal_amount:
            await callback.message.edit_text(
                f"❌ <b>Недостаточно средств для вывода</b>\n\n"
                f"💰 Ваш баланс: {available_balance:,} ⭐\n"
                f"💸 Минимальная сумма: {withdrawal_service.min_withdrawal_amount:,} ⭐\n\n"
                f"Пополните баланс, получив больше продаж.",
                reply_markup=withdrawal_main_keyboard()
            )
            await callback.answer()
            return
        
        create_text = f"""
💸 <b>Создание запроса на вывод</b>

💰 <b>Доступно:</b> {available_balance:,} ⭐
💡 <b>Минимум:</b> {withdrawal_service.min_withdrawal_amount:,} ⭐
💡 <b>Максимум:</b> {min(available_balance, withdrawal_service.daily_limit):,} ⭐

📝 Введите сумму для вывода (в звездах):
"""
        
        await callback.message.edit_text(create_text)
        await callback.answer()
        await state.set_state(WithdrawalStates.entering_withdrawal_amount)
        await state.update_data(available_balance=available_balance)
        
    except Exception as e:
        logger.error(f"Ошибка при создании запроса на вывод: {e}")
        await callback.answer("❌ Ошибка при создании запроса.")


@router.message(WithdrawalStates.entering_withdrawal_amount)
async def process_withdrawal_amount(message: Message, session: AsyncSession, admin, state: FSMContext):
    """Обработка введенной суммы для вывода"""
    try:
        withdrawal_service = WithdrawalService(session)
        
        # Проверяем, что введено число
        try:
            amount = int(message.text.strip().replace(',', '').replace(' ', ''))
        except ValueError:
            await message.answer(
                "❌ Пожалуйста, введите корректную сумму числом.\n"
                "Например: 1000"
            )
            return
        
        # Получаем данные из состояния
        data = await state.get_data()
        available_balance = data.get('available_balance', 0)
        
        # Валидация суммы
        if amount < withdrawal_service.min_withdrawal_amount:
            await message.answer(
                f"❌ Сумма слишком мала.\n"
                f"Минимальная сумма: {withdrawal_service.min_withdrawal_amount:,} ⭐"
            )
            return
        
        if amount > available_balance:
            await message.answer(
                f"❌ Недостаточно средств.\n"
                f"Доступно: {available_balance:,} ⭐"
            )
            return
        
        # Проверяем дневной лимит
        if not await withdrawal_service.check_daily_limit(admin.user_id, amount):
            await message.answer(
                f"❌ Превышен дневной лимит.\n"
                f"Максимум в день: {withdrawal_service.daily_limit:,} ⭐"
            )
            return
        
        # Рассчитываем комиссию
        commission = withdrawal_service.calculate_commission(amount)
        net_amount = amount - commission
        
        amount_text = f"""
💸 <b>Сумма для вывода</b>

💰 <b>Сумма к выводу:</b> {amount:,} ⭐
💸 <b>Комиссия ({withdrawal_service.commission_rate*100}%):</b> {commission:,} ⭐
✅ <b>К получению:</b> {net_amount:,} ⭐

📝 Теперь введите адрес Telegram Wallet (TON):

💡 <b>Формат адреса:</b> 
• Начинается с EQ, UQ или 0Q
• Длина 48 символов
• Пример: EQA0i8-CdGnF_DhUHHf92R1ONH6sIA9vLZ_WLcCIhfBBXwtG
"""
        
        await message.answer(amount_text)
        await state.set_state(WithdrawalStates.entering_wallet_address)
        await state.update_data(
            amount=amount,
            commission=commission,
            net_amount=net_amount
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке суммы вывода: {e}")
        await message.answer("❌ Ошибка при обработке суммы.")


@router.message(WithdrawalStates.entering_wallet_address)
async def process_wallet_address(message: Message, session: AsyncSession, admin, state: FSMContext):
    """Обработка введенного адреса кошелька"""
    try:
        withdrawal_service = WithdrawalService(session)
        wallet_address = message.text.strip()
        
        # Валидация адреса кошелька
        if not withdrawal_service.validate_wallet_address(wallet_address):
            await message.answer(
                "❌ <b>Неверный формат адреса кошелька</b>\n\n"
                "💡 TON адрес должен:\n"
                "• Начинаться с EQ, UQ или 0Q\n"
                "• Иметь длину 48 символов\n"
                "• Содержать только буквы, цифры, _ и -\n\n"
                "📝 <b>Пример:</b> EQA0i8-CdGnF_DhUHHf92R1ONH6sIA9vLZ_WLcCIhfBBXwtG\n\n"
                "Попробуйте еще раз:"
            )
            return
        
        notes_text = f"""
📝 <b>Адрес кошелька добавлен</b>

💳 <b>Кошелек:</b> <code>{wallet_address}</code>

📝 Добавьте комментарий к выводу (необязательно) или нажмите /skip для пропуска:

💡 <b>Примеры комментариев:</b>
• Вывод прибыли за месяц
• Комиссия за консультации
• Доходы от курсов
"""
        
        await message.answer(notes_text)
        await state.set_state(WithdrawalStates.entering_withdrawal_notes)
        await state.update_data(wallet_address=wallet_address)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке адреса кошелька: {e}")
        await message.answer("❌ Ошибка при обработке адреса.")


@router.message(WithdrawalStates.entering_withdrawal_notes)
async def process_withdrawal_notes(message: Message, session: AsyncSession, admin, state: FSMContext):
    """Обработка комментария к выводу"""
    try:
        notes = None if message.text.strip() == "/skip" else message.text.strip()
        
        # Получаем все данные из состояния
        data = await state.get_data()
        amount = data.get('amount')
        commission = data.get('commission')
        net_amount = data.get('net_amount')
        wallet_address = data.get('wallet_address')
        
        confirm_text = f"""
✅ <b>Подтверждение запроса на вывод</b>

💰 <b>Сумма к выводу:</b> {amount:,} ⭐
💸 <b>Комиссия:</b> {commission:,} ⭐
✨ <b>К получению:</b> {net_amount:,} ⭐

💳 <b>Кошелек:</b> <code>{wallet_address}</code>
📝 <b>Комментарий:</b> {notes or "Не указан"}

⚠️ <b>Внимание:</b>
• После подтверждения запрос будет отправлен на обработку
• Средства будут переведены в течение 24 часов
• Отменить запрос можно только до начала обработки

Подтвердить создание запроса?
"""
        
        await message.answer(
            confirm_text,
            reply_markup=withdrawal_confirm_keyboard(amount, commission, net_amount)
        )
        await state.set_state(WithdrawalStates.confirming_withdrawal)
        await state.update_data(notes=notes)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке комментария: {e}")
        await message.answer("❌ Ошибка при обработке комментария.")


@router.callback_query(F.data == "withdrawal_confirm_yes", WithdrawalStates.confirming_withdrawal)
async def confirm_withdrawal_creation(callback: CallbackQuery, session: AsyncSession, admin, state: FSMContext):
    """Подтверждение создания запроса на вывод"""
    try:
        withdrawal_service = WithdrawalService(session)
        
        # Получаем данные из состояния
        data = await state.get_data()
        
        # Создаем запрос на вывод
        withdrawal_request = await withdrawal_service.create_withdrawal_request(
            admin_id=admin.user_id,
            amount_stars=data.get('amount'),
            wallet_address=data.get('wallet_address'),
            notes=data.get('notes')
        )
        
        if withdrawal_request:
            success_text = f"""
✅ <b>Запрос на вывод создан</b>

🆔 <b>ID запроса:</b> #{withdrawal_request.id}
💰 <b>Сумма:</b> {withdrawal_request.amount_stars:,} ⭐
💸 <b>Комиссия:</b> {withdrawal_request.commission_amount:,} ⭐
✨ <b>К получению:</b> {withdrawal_request.net_amount:,} ⭐
⏰ <b>Дата создания:</b> {withdrawal_request.request_date.strftime('%d.%m.%Y %H:%M')}

📋 <b>Статус:</b> Ожидает обработки

💡 Запрос будет обработан в течение 24 часов.
Вы получите уведомление о статусе обработки.
"""
            
            await callback.message.edit_text(
                success_text,
                reply_markup=withdrawal_main_keyboard()
            )
        else:
            await callback.message.edit_text(
                "❌ <b>Ошибка при создании запроса</b>\n\n"
                "Попробуйте еще раз или обратитесь к администратору.",
                reply_markup=withdrawal_main_keyboard()
            )
        
        await callback.answer()
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при подтверждении запроса на вывод: {e}")
        await callback.answer("❌ Ошибка при создании запроса.")


@router.callback_query(F.data == "withdrawal_confirm_no")
async def cancel_withdrawal_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания запроса на вывод"""
    try:
        await callback.message.edit_text(
            "❌ <b>Создание запроса отменено</b>\n\n"
            "Вы можете создать новый запрос в любое время.",
            reply_markup=withdrawal_main_keyboard()
        )
        await callback.answer()
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при отмене создания запроса: {e}")
        await callback.answer("❌ Ошибка при отмене.")


@router.callback_query(F.data == "withdrawal_my_requests")
async def show_my_withdrawal_requests(callback: CallbackQuery, session: AsyncSession, admin, state: FSMContext):
    """Показать запросы на вывод администратора"""
    try:
        withdrawal_service = WithdrawalService(session)
        
        # Получаем запросы администратора
        requests = await withdrawal_service.get_withdrawal_requests_by_admin(admin.user_id)
        
        if not requests:
            await callback.message.edit_text(
                "📝 <b>История запросов на вывод</b>\n\n"
                "У вас пока нет запросов на вывод средств.\n\n"
                "💡 Создайте первый запрос, чтобы начать получать прибыль!",
                reply_markup=withdrawal_main_keyboard()
            )
            await callback.answer()
            return
        
        # Формируем список запросов
        requests_text = "📋 <b>Ваши запросы на вывод</b>\n\n"
        
        for request in requests[:10]:  # Показываем последние 10
            status_emoji = {
                'pending': '⏳',
                'processing': '🔄',
                'completed': '✅',
                'failed': '❌',
                'cancelled': '🚫'
            }.get(request.status, '❓')
            
            requests_text += f"""
{status_emoji} <b>#{request.id}</b> • {request.amount_stars:,} ⭐
📅 {request.request_date.strftime('%d.%m.%Y %H:%M')}
💳 {request.wallet_address[:10]}...{request.wallet_address[-10:]}
───────────────────────────
"""
        
        if len(requests) > 10:
            requests_text += f"\n... и еще {len(requests) - 10} запросов"
        
        await callback.message.edit_text(
            requests_text,
            reply_markup=withdrawal_requests_keyboard()
        )
        await callback.answer()
        await state.set_state(WithdrawalStates.viewing_withdrawals)
        
    except Exception as e:
        logger.error(f"Ошибка при показе запросов на вывод: {e}")
        await callback.answer("❌ Ошибка при загрузке запросов.")


# Базовые обработчики для просмотра деталей и отмены
@router.callback_query(F.data.startswith("withdrawal_details:"))
async def show_withdrawal_details(callback: CallbackQuery, session: AsyncSession, admin):
    """Показать детали конкретного запроса на вывод"""
    try:
        withdrawal_service = WithdrawalService(session)
        request_id = int(callback.data.split(":")[1])
        
        withdrawal_request = await withdrawal_service.get_withdrawal_request_by_id(request_id)
        
        if not withdrawal_request or withdrawal_request.admin_id != admin.user_id:
            await callback.answer("❌ Запрос не найден.")
            return
        
        status_info = {
            'pending': ('⏳', 'Ожидает обработки'),
            'processing': ('🔄', 'В обработке'),
            'completed': ('✅', 'Завершен'),
            'failed': ('❌', 'Отклонен'),
            'cancelled': ('🚫', 'Отменен')
        }
        
        status_emoji, status_text = status_info.get(withdrawal_request.status, ('❓', 'Неизвестно'))
        
        details_text = f"""
{status_emoji} <b>Запрос #{withdrawal_request.id}</b>

💰 <b>Сумма запроса:</b> {withdrawal_request.amount_stars:,} ⭐
💸 <b>Комиссия:</b> {withdrawal_request.commission_amount:,} ⭐
✨ <b>К получению:</b> {withdrawal_request.net_amount:,} ⭐

💳 <b>Кошелек:</b> <code>{withdrawal_request.wallet_address}</code>
📝 <b>Комментарий:</b> {withdrawal_request.notes or "Не указан"}

📋 <b>Статус:</b> {status_text}
📅 <b>Создан:</b> {withdrawal_request.request_date.strftime('%d.%m.%Y %H:%M')}
"""
        
        if withdrawal_request.processed_date:
            details_text += f"✅ <b>Обработан:</b> {withdrawal_request.processed_date.strftime('%d.%m.%Y %H:%M')}\n"
        
        if withdrawal_request.transaction_id:
            details_text += f"🆔 <b>ID транзакции:</b> <code>{withdrawal_request.transaction_id}</code>\n"
        
        if withdrawal_request.failure_reason:
            details_text += f"❌ <b>Причина отказа:</b> {withdrawal_request.failure_reason}\n"
        
        can_cancel = withdrawal_request.status == 'pending'
        
        await callback.message.edit_text(
            details_text,
            reply_markup=withdrawal_details_keyboard(request_id, withdrawal_request.status, can_cancel)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе деталей запроса: {e}")
        await callback.answer("❌ Ошибка при загрузке деталей.")


@router.callback_query(F.data.startswith("withdrawal_cancel:"))
async def show_cancel_confirmation(callback: CallbackQuery, session: AsyncSession, admin):
    """Показать подтверждение отмены запроса"""
    try:
        withdrawal_service = WithdrawalService(session)
        request_id = int(callback.data.split(":")[1])
        
        withdrawal_request = await withdrawal_service.get_withdrawal_request_by_id(request_id)
        
        if not withdrawal_request or withdrawal_request.admin_id != admin.user_id:
            await callback.answer("❌ Запрос не найден.")
            return
        
        if withdrawal_request.status != 'pending':
            await callback.answer("❌ Можно отменить только ожидающие запросы.")
            return
        
        cancel_text = f"""
🚫 <b>Отмена запроса на вывод</b>

🆔 <b>Запрос:</b> #{withdrawal_request.id}
💰 <b>Сумма:</b> {withdrawal_request.amount_stars:,} ⭐
💳 <b>Кошелек:</b> {withdrawal_request.wallet_address[:10]}...{withdrawal_request.wallet_address[-10:]}

❓ <b>Вы уверены, что хотите отменить этот запрос?</b>

⚠️ После отмены вам потребуется создать новый запрос для вывода средств.
"""
        
        await callback.message.edit_text(
            cancel_text,
            reply_markup=withdrawal_cancel_confirm_keyboard(request_id)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе подтверждения отмены: {e}")
        await callback.answer("❌ Ошибка при обработке.")


@router.callback_query(F.data.startswith("withdrawal_cancel_confirm:"))
async def confirm_withdrawal_cancellation(callback: CallbackQuery, session: AsyncSession, admin):
    """Подтверждение отмены запроса на вывод"""
    try:
        withdrawal_service = WithdrawalService(session)
        request_id = int(callback.data.split(":")[1])
        
        withdrawal_request = await withdrawal_service.get_withdrawal_request_by_id(request_id)
        
        if not withdrawal_request or withdrawal_request.admin_id != admin.user_id:
            await callback.answer("❌ Запрос не найден.")
            return
        
        if withdrawal_request.status != 'pending':
            await callback.answer("❌ Можно отменить только ожидающие запросы.")
            return
        
        # Отменяем запрос
        success = await withdrawal_service.cancel_withdrawal_request(
            request_id, 
            admin.user_id,
            "Отменено пользователем"
        )
        
        if success:
            success_text = f"""
✅ <b>Запрос #{request_id} отменен</b>

💰 Сумма {withdrawal_request.amount_stars:,} ⭐ возвращена на ваш баланс.

Вы можете создать новый запрос на вывод в любое время.
"""
            
            await callback.message.edit_text(
                success_text,
                reply_markup=withdrawal_main_keyboard()
            )
        else:
            await callback.message.edit_text(
                "❌ <b>Ошибка при отмене запроса</b>\n\n"
                "Попробуйте еще раз или обратитесь к администратору.",
                reply_markup=withdrawal_main_keyboard()
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при подтверждении отмены запроса: {e}")
        await callback.answer("❌ Ошибка при отмене запроса.")


@router.callback_query(F.data == "withdrawal_statistics")
async def show_withdrawal_statistics(callback: CallbackQuery, session: AsyncSession, admin):
    """Показать статистику по выводам"""
    try:
        withdrawal_service = WithdrawalService(session)
        
        # Получаем статистику
        requests = await withdrawal_service.get_withdrawal_requests_by_admin(admin.user_id)
        
        if not requests:
            stats_text = """
📊 <b>Статистика выводов</b>

У вас пока нет запросов на вывод средств.

💡 Создайте первый запрос, чтобы начать получать прибыль!
"""
        else:
            # Подсчитываем статистику
            total_requests = len(requests)
            total_amount = sum(r.amount_stars for r in requests)
            total_commission = sum(r.commission_amount for r in requests)
            total_net = sum(r.net_amount for r in requests)
            
            completed = [r for r in requests if r.status == 'completed']
            pending = [r for r in requests if r.status == 'pending']
            processing = [r for r in requests if r.status == 'processing']
            failed = [r for r in requests if r.status == 'failed']
            cancelled = [r for r in requests if r.status == 'cancelled']
            
            completed_amount = sum(r.net_amount for r in completed)
            
            stats_text = f"""
📊 <b>Статистика выводов</b>

📊 <b>Общая статистика:</b>
• Всего запросов: {total_requests}
• Общая сумма: {total_amount:,} ⭐
• Комиссия: {total_commission:,} ⭐
• К получению: {total_net:,} ⭐

📊 <b>По статусам:</b>
✅ Завершено: {len(completed)} • {completed_amount:,} ⭐
⏳ Ожидает: {len(pending)}
🔄 Обрабатывается: {len(processing)}
❌ Отклонено: {len(failed)}
🙅 Отменено: {len(cancelled)}
"""
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=withdrawal_main_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе статистики выводов: {e}")
        await callback.answer("❌ Ошибка при загрузке статистики.")