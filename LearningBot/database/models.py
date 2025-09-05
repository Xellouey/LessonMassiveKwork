"""
Модели базы данных для Learning Bot
"""
from datetime import datetime, timezone, date
from typing import Optional, List
from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime, 
    ForeignKey, Integer, String, Text, Numeric
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database.database import Base


class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)  # Telegram user_id
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    language: Mapped[str] = mapped_column(String(5), default='ru')
    total_spent: Mapped[int] = mapped_column(Integer, default=0)  # В звездах
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Связи
    purchases: Mapped[List["Purchase"]] = relationship("Purchase", back_populates="user")
    # activities: Mapped[List["UserActivity"]] = relationship("UserActivity", back_populates="user")  # ❌ Закомментировано для MVP
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, user_id={self.user_id}, username={self.username})>"


class Category(Base):
    """Модель категории уроков"""
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Связи
    lessons: Mapped[List["Lesson"]] = relationship("Lesson", back_populates="category_rel")
    
    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name})>"


class Lesson(Base):
    """Модель урока/курса"""
    __tablename__ = 'lessons'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price_stars: Mapped[int] = mapped_column(Integer, nullable=False)  # Цена в звездах
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)  # video, photo, document, etc.
    file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Telegram file_id
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Длительность в секундах
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_free: Mapped[bool] = mapped_column(Boolean, default=False)  # Бесплатный лид-магнит
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('categories.id'), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Временно оставляем для миграции
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Связи
    category_rel: Mapped[Optional["Category"]] = relationship("Category", back_populates="lessons")
    purchases: Mapped[List["Purchase"]] = relationship("Purchase", back_populates="lesson")
    # activities: Mapped[List["UserActivity"]] = relationship("UserActivity", back_populates="lesson")  # ❌ Закомментировано для MVP
    
    @property
    def category_name(self) -> Optional[str]:
        """Получить название категории (приоритет: category_rel.name, затем category)"""
        if self.category_rel:
            return self.category_rel.name
        return self.category
    
    def __repr__(self) -> str:
        return f"<Lesson(id={self.id}, title={self.title}, price={self.price_stars})>"


class Purchase(Base):
    """Модель покупки"""
    __tablename__ = 'purchases'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey('lessons.id'), nullable=False)
    payment_charge_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Telegram payment ID
    purchase_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(50), default='completed')  # completed, refunded
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    amount_stars: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Связи
    user: Mapped["User"] = relationship("User", back_populates="purchases")
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="purchases")
    
    def __repr__(self) -> str:
        return f"<Purchase(id={self.id}, user_id={self.user_id}, lesson_id={self.lesson_id})>"


class TextSetting(Base):
    """Модель настраиваемых текстов"""
    __tablename__ = 'text_settings'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value_ru: Mapped[str] = mapped_column(Text, nullable=False)
    value_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # messages, buttons, descriptions
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self) -> str:
        return f"<TextSetting(key={self.key}, category={self.category})>"


class Admin(Base):
    """Модель администратора"""
    __tablename__ = 'admins'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    permissions: Mapped[str] = mapped_column(String(255), default='all')  # JSON строка с правами
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Связи
    broadcasts: Mapped[List["Broadcast"]] = relationship("Broadcast", back_populates="admin")
    
    def __repr__(self) -> str:
        return f"<Admin(id={self.id}, user_id={self.user_id}, username={self.username})>"


class Broadcast(Base):
    """Модель рассылки"""
    __tablename__ = 'broadcasts'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('admins.user_id'), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # photo, video, document
    file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    total_users: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default='pending')  # pending, sending, completed, failed
    
    # Связи
    admin: Mapped["Admin"] = relationship("Admin", back_populates="broadcasts")
    # deliveries: Mapped[List["BroadcastDelivery"]] = relationship("BroadcastDelivery", back_populates="broadcast")  # ❌ Закомментировано для MVP
    
    def __repr__(self) -> str:
        return f"<Broadcast(id={self.id}, admin_id={self.admin_id}, status={self.status})>"


# ❌ ЗАКОММЕНТИРОВАНО ДЛЯ MVP - ДЕТАЛЬНЫЙ ТРЕКИНГ РАССЫЛОК НЕ НУЖЕН
# class BroadcastDelivery(Base):
#     """Модель доставки рассылки конкретному пользователю"""
#     __tablename__ = 'broadcast_deliveries'
#     
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     broadcast_id: Mapped[int] = mapped_column(Integer, ForeignKey('broadcasts.id'), nullable=False)
#     user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.user_id'), nullable=False)
#     status: Mapped[str] = mapped_column(String(50), default='pending')  # pending, sent, failed, blocked
#     sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
#     error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
#     delivery_attempts: Mapped[int] = mapped_column(Integer, default=0)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
#     
#     # Связи
#     broadcast: Mapped["Broadcast"] = relationship("Broadcast", back_populates="deliveries")
#     user: Mapped["User"] = relationship("User")
#     
#     def __repr__(self) -> str:
#         return f"<BroadcastDelivery(id={self.id}, broadcast_id={self.broadcast_id}, user_id={self.user_id}, status={self.status})>"


# ❌ ЗАКОММЕНТИРОВАНО ДЛЯ MVP - ЕЖЕДНЕВНАЯ СТАТИСТИКА СЛИШКОМ СЛОЖНА
# class Statistics(Base):
#     """Модель статистики"""
#     __tablename__ = 'statistics'
#     
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
#     new_users: Mapped[int] = mapped_column(Integer, default=0)
#     purchases_count: Mapped[int] = mapped_column(Integer, default=0)
#     revenue_stars: Mapped[int] = mapped_column(Integer, default=0)
#     active_users: Mapped[int] = mapped_column(Integer, default=0)
#     refunds_count: Mapped[int] = mapped_column(Integer, default=0)
#     
#     def __repr__(self) -> str:
#         return f"<Statistics(date={self.date}, new_users={self.new_users}, revenue={self.revenue_stars})>"


# ❌ ЗАКОММЕНТИРОВАНО ДЛЯ MVP - ДЕТАЛЬНАЯ АНАЛИТИКА НЕ НУЖНА
# class UserActivity(Base):
#     """Модель активности пользователей"""
#     __tablename__ = 'user_activity'
#     
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.user_id'), nullable=False)
#     action: Mapped[str] = mapped_column(String(100), nullable=False)  # start, view_catalog, purchase, etc.
#     lesson_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('lessons.id'), nullable=True)
#     timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
#     extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON дополнительных данных
#     
#     # Связи
#     user: Mapped["User"] = relationship("User", back_populates="activities")
#     lesson: Mapped[Optional["Lesson"]] = relationship("Lesson", back_populates="activities")
#     
#     def __repr__(self) -> str:
#         return f"<UserActivity(id={self.id}, user_id={self.user_id}, action={self.action})>"


class SupportTicket(Base):
    """Модель для обращений в поддержку"""
    __tablename__ = 'support_tickets'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    ticket_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(255), default="Support Request")
    initial_message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open, in_progress, closed
    priority: Mapped[str] = mapped_column(String(10), default="normal")  # low, normal, high, urgent
    assigned_admin_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('admins.user_id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=lambda: datetime.now(timezone.utc))
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Связи
    user: Mapped["User"] = relationship("User")
    assigned_admin: Mapped[Optional["Admin"]] = relationship("Admin")
    responses: Mapped[List["SupportResponse"]] = relationship("SupportResponse", back_populates="ticket")
    
    def __repr__(self) -> str:
        return f"<SupportTicket(id={self.id}, ticket_number={self.ticket_number}, status={self.status})>"


class SupportResponse(Base):
    """Модель для ответов в тикетах поддержки"""
    __tablename__ = 'support_responses'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey('support_tickets.id'), nullable=False)
    sender_type: Mapped[str] = mapped_column(String(10), nullable=False)  # user, admin
    sender_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Telegram user_id
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)  # Internal admin notes
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Связи
    ticket: Mapped["SupportTicket"] = relationship("SupportTicket", back_populates="responses")
    
    def __repr__(self) -> str:
        return f"<SupportResponse(id={self.id}, ticket_id={self.ticket_id}, sender_type={self.sender_type})>"


class WithdrawalRequest(Base):
    """Модель запросов на вывод средств"""
    __tablename__ = 'withdrawal_requests'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('admins.user_id'), nullable=False)
    amount_stars: Mapped[int] = mapped_column(Integer, nullable=False)  # Сумма в звездах
    wallet_address: Mapped[str] = mapped_column(String(255), nullable=False)  # Адрес Telegram Wallet
    status: Mapped[str] = mapped_column(String(50), default='pending')  # pending, processing, completed, failed, cancelled
    request_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # ID транзакции в Telegram Wallet
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Причина отказа
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Дополнительные заметки
    commission_amount: Mapped[int] = mapped_column(Integer, default=0)  # Комиссия в звездах
    net_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # Сумма к выплате (с учетом комиссии)
    
    # Связи
    admin: Mapped["Admin"] = relationship("Admin")
    
    def __repr__(self) -> str:
        return f"<WithdrawalRequest(id={self.id}, admin_id={self.admin_id}, amount={self.amount_stars}, status={self.status})>"