"""
Состояния для пользовательских действий (FSM)
"""
from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """Состояния для обычных пользователей"""
    
    # Поиск уроков
    waiting_for_search = State()
    
    # Просмотр урока
    viewing_lesson = State()
    
    # Процесс покупки
    in_payment_process = State()
    confirming_purchase = State()
    
    # Личный кабинет
    in_profile = State()
    viewing_purchases = State()
    
    # Поддержка
    contacting_support = State()


class PaymentStates(StatesGroup):
    """Состояния для процесса оплаты"""
    
    # Выбор урока для покупки
    selecting_lesson = State()
    
    # Подтверждение покупки
    confirming_payment = State()
    
    # Ожидание результата платежа
    waiting_payment_result = State()


class FeedbackStates(StatesGroup):
    """Состояния для обратной связи"""
    
    # Написание отзыва
    writing_review = State()
    
    # Обращение в поддержку (ДУБЛИКАТ - перенесено в UserStates)
    # contacting_support = State()