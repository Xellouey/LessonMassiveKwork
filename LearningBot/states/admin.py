"""
Состояния для административных действий (FSM)
"""
from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """Общие административные состояния"""
    
    # Главное меню админа
    in_admin_menu = State()


class CategoryManagementStates(StatesGroup):
    """Состояния для управления категориями"""
    
    # Создание категории
    creating_category = State()
    entering_category_name = State()
    
    # Редактирование категории
    editing_category = State()
    editing_name = State()
    
    # Удаление категории
    deleting_category = State()
    confirming_category_deletion = State()


class LessonManagementStates(StatesGroup):
    """Состояния для управления уроками"""
    
    # Создание урока
    creating_lesson = State()
    entering_lesson_title = State()
    entering_lesson_description = State()
    entering_lesson_price = State()
    uploading_lesson_content = State()
    setting_lesson_category = State()
    
    # Редактирование урока
    editing_lesson = State()
    selecting_lesson_to_edit = State()
    editing_lesson_title = State()
    editing_lesson_description = State()
    editing_lesson_price = State()
    editing_lesson_content = State()
    editing_lesson_category = State()
    editing_lesson_media = State()  # Новое состояние для редактирования медиа
    
    # Удаление урока
    deleting_lesson = State()
    confirming_lesson_deletion = State()


class BroadcastStates(StatesGroup):
    """Состояния для массовых рассылок"""
    
    # Создание рассылки
    creating_broadcast = State()
    entering_broadcast_text = State()
    uploading_broadcast_media = State()
    confirming_broadcast = State()
    
    # Выбор аудитории
    selecting_audience = State()


class TextEditingStates(StatesGroup):
    """Состояния для редактирования текстов интерфейса"""
    
    # Выбор категории текстов
    selecting_text_category = State()
    
    # Редактирование текстов
    editing_text = State()
    selecting_text_to_edit = State()
    entering_new_text_ru = State()
    entering_new_text_en = State()


class MediaManagementStates(StatesGroup):
    """Состояния для управления медиа"""
    
    # Просмотр медиа
    browsing_media = State()
    viewing_media_details = State()
    
    # Загрузка медиа
    uploading_media = State()
    selecting_media_type = State()
    uploading_file = State()
    
    # Редактирование медиа
    editing_media = State()
    replacing_media_file = State()
    
    # Поиск медиа
    searching_media = State()


class UserManagementStates(StatesGroup):
    """Состояния для управления пользователями"""
    
    # Просмотр пользователей
    viewing_users = State()
    searching_user = State()
    
    # Управление конкретным пользователем
    managing_user = State()
    blocking_user = State()
    unblocking_user = State()


class StatisticsStates(StatesGroup):
    """Состояния для просмотра статистики"""
    
    # Выбор периода статистики
    selecting_stats_period = State()
    
    # Просмотр различных отчетов
    viewing_general_stats = State()
    viewing_sales_stats = State()
    viewing_user_stats = State()


class SupportManagementStates(StatesGroup):
    """Состояния для управления поддержкой"""
    
    # Просмотр тикетов
    viewing_support_tickets = State()
    viewing_ticket_details = State()
    
    # Ответ на тикет
    responding_to_support = State()
    entering_support_response = State()
    
    # Управление тикетом
    managing_ticket = State()
    assigning_ticket = State()
    changing_ticket_status = State()
    closing_ticket = State()
    
    # Создание внутренних заметок
    adding_internal_note = State()


class WithdrawalStates(StatesGroup):
    """Состояния для управления выводом средств"""
    
    # Главное меню вывода средств
    in_withdrawal_menu = State()
    
    # Создание запроса на вывод
    creating_withdrawal = State()
    entering_withdrawal_amount = State()
    entering_wallet_address = State()
    entering_withdrawal_notes = State()
    confirming_withdrawal = State()
    
    # Просмотр запросов
    viewing_withdrawals = State()
    viewing_withdrawal_details = State()
    
    # Управление запросами (для суперадминов)
    managing_withdrawal = State()
    processing_withdrawal = State()
    entering_transaction_id = State()
    entering_failure_reason = State()
    
    # Отмена запроса
    cancelling_withdrawal = State()
    confirming_cancellation = State()