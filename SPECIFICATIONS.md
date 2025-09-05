# Спецификация проекта: Образовательный Telegram-бот с оплатой через Stars

## Обзор проекта

Разработка Telegram-бота для продажи образовательных курсов с интегрированной системой оплаты через Telegram Stars. Бот предоставляет полный функционал для пользователей (каталог, покупка, личный кабинет) и администраторов (управление контентом, статистика, рассылки).

## Технологический стек

- **Backend**: Python 3.9+
- **Framework**: aiogram 3.x (асинхронный фреймворк для Telegram Bot API)
- **База данных**: PostgreSQL / SQLite
- **ORM**: SQLAlchemy 2.x
- **Миграции**: Alembic
- **Оплата**: Telegram Stars API
- **Кэширование**: Redis (опционально)
- **Деплой**: Docker + Docker Compose

## Архитектура проекта

```
LearningBot/
├── bot.py                     # Точка входа
├── config.py                  # Конфигурация
├── requirements.txt           # Зависимости
├── alembic.ini               # Настройки миграций
├── .env                      # Переменные окружения
├── database/
│   ├── __init__.py
│   ├── models.py             # SQLAlchemy модели
│   ├── database.py           # Подключение к БД
│   └── migrations/           # Миграции БД
├── handlers/
│   ├── __init__.py
│   ├── user/                 # Пользовательские хендлеры
│   │   ├── __init__.py
│   │   ├── start.py         # /start и регистрация
│   │   ├── catalog.py       # Каталог курсов
│   │   ├── payment.py       # Система оплаты
│   │   └── profile.py       # Личный кабинет
│   └── admin/               # Административные хендлеры
│       ├── __init__.py
│       ├── auth.py          # Авторизация админов
│       ├── content.py       # Управление контентом
│       ├── texts.py         # Редактирование текстов
│       ├── stats.py         # Статистика
│       └── broadcast.py     # Рассылки
├── keyboards/
│   ├── __init__.py
│   ├── user.py              # Клавиатуры для пользователей
│   └── admin.py             # Клавиатуры для админов
├── middlewares/
│   ├── __init__.py
│   ├── auth.py              # Авторизация
│   ├── throttling.py        # Защита от спама
│   └── database.py          # Middleware для БД
├── services/
│   ├── __init__.py
│   ├── payment.py           # Бизнес-логика оплаты
│   ├── content.py           # Управление контентом
│   ├── broadcast.py         # Сервис рассылок
│   └── analytics.py         # Аналитика
├── utils/
│   ├── __init__.py
│   ├── texts.py             # Управление текстами
│   ├── helpers.py           # Вспомогательные функции
│   └── decorators.py        # Декораторы
├── states/
│   ├── __init__.py
│   ├── user.py              # Состояния пользователей
│   └── admin.py             # Состояния админов
└── tests/                   # Unit тесты
    ├── __init__.py
    ├── test_handlers/
    ├── test_services/
    └── test_models/
```

## Схема базы данных

### Модели данных (SQLAlchemy)

#### 1. User - Пользователи
```python
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)  # Telegram user_id
    username = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    registration_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    language = Column(String(5), default='ru')
    total_spent = Column(Integer, default=0)  # В звездах
    last_activity = Column(DateTime, default=datetime.utcnow)
```

#### 2. Lesson - Уроки/Курсы
```python
class Lesson(Base):
    __tablename__ = 'lessons'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    price_stars = Column(Integer, nullable=False)  # Цена в звездах
    content_type = Column(String(50), nullable=False)  # video, photo, document, etc.
    file_id = Column(String(255), nullable=True)  # Telegram file_id
    duration = Column(Integer, nullable=True)  # Длительность в секундах
    is_active = Column(Boolean, default=True)
    is_free = Column(Boolean, default=False)  # Бесплатный лид-магнит
    category = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    views_count = Column(Integer, default=0)
```

#### 3. Purchase - Покупки
```python
class Purchase(Base):
    __tablename__ = 'purchases'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    lesson_id = Column(Integer, ForeignKey('lessons.id'), nullable=False)
    payment_charge_id = Column(String(255), nullable=False)  # Telegram payment ID
    purchase_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default='completed')  # completed, refunded
    refunded_at = Column(DateTime, nullable=True)
    amount_stars = Column(Integer, nullable=False)
```

#### 4. TextSetting - Настраиваемые тексты
```python
class TextSetting(Base):
    __tablename__ = 'text_settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value_ru = Column(Text, nullable=False)
    value_en = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # messages, buttons, descriptions
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

#### 5. Admin - Администраторы
```python
class Admin(Base):
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255), nullable=True)
    permissions = Column(String(255), default='all')  # JSON строка с правами
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
```

#### 6. Broadcast - Рассылки
```python
class Broadcast(Base):
    __tablename__ = 'broadcasts'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(BigInteger, ForeignKey('admins.user_id'), nullable=False)
    text = Column(Text, nullable=False)
    media_type = Column(String(50), nullable=True)  # photo, video, document
    file_id = Column(String(255), nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    total_users = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    status = Column(String(50), default='pending')  # pending, sending, completed, failed
```

#### 7. Statistics - Статистика
```python
class Statistics(Base):
    __tablename__ = 'statistics'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, nullable=False)
    new_users = Column(Integer, default=0)
    purchases_count = Column(Integer, default=0)
    revenue_stars = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    refunds_count = Column(Integer, default=0)
```

#### 8. UserActivity - Активность пользователей
```python
class UserActivity(Base):
    __tablename__ = 'user_activity'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    action = Column(String(100), nullable=False)  # start, view_catalog, purchase, etc.
    lesson_id = Column(Integer, ForeignKey('lessons.id'), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(Text, nullable=True)  # JSON дополнительных данных
```

## Функциональные требования

### Пользовательский функционал

#### 1. Воронка и приветствие
- **Команда /start**: Регистрация нового пользователя или приветствие существующего
- **Лид-магнит**: Бесплатный урок сразу после регистрации
- **Приветственное сообщение**: Настраиваемый текст с описанием бота
- **Основное меню**: Каталог уроков, Мои покупки, Помощь

#### 2. Каталог уроков
- **Просмотр всех уроков**: Список доступных курсов с пагинацией
- **Фильтрация**: По категориям, цене, популярности
- **Поиск**: По названию или описанию урока
- **Детальная карточка**: Название, описание, цена в звездах, превью

#### 3. Система оплаты
- **Создание инвойса**: Через Telegram Stars API (`sendInvoice`)
- **Обработка платежей**: Валидация через `answerPreCheckoutQuery`
- **Подтверждение оплаты**: Автоматическое предоставление доступа к уроку
- **История платежей**: Список всех транзакций пользователя

#### 4. Личный кабинет
- **Мои уроки**: Список всех купленных курсов
- **Просмотр урока**: Воспроизведение купленного контента
- **Статистика**: Количество купленных уроков, потраченные звезды
- **Настройки**: Смена языка интерфейса

### Административный функционал

#### 1. Авторизация и доступ
- **Система ролей**: Суперадмин, администратор контента, модератор
- **Авторизация**: По Telegram user_id из списка админов
- **Права доступа**: Гибкая система прав для разных ролей

#### 2. Управление контентом
- **CRUD уроков**: Создание, редактирование, удаление курсов
- **Загрузка медиа**: Поддержка видео, фото, документов, аудио
- **Настройка цен**: Установка цены в звездах для каждого урока
- **Управление категориями**: Создание и редактирование категорий
- **Превью контента**: Возможность просмотра урока перед публикацией

#### 3. Редактор текстов
- **Интерфейсные тексты**: Редактирование всех сообщений бота
- **Кнопки и меню**: Настройка названий кнопок
- **Мультиязычность**: Перевод текстов на разные языки
- **Предпросмотр**: Просмотр изменений перед сохранением

#### 4. Статистика и аналитика
- **Общая статистика**: Пользователи, продажи, доход по периодам
- **Аналитика продаж**: ТОП уроков, конверсии, средний чек
- **Пользовательская активность**: Активные пользователи, новые регистрации
- **Финансовые отчеты**: Доходы в звездах, успешные транзакции

#### 5. Система рассылок
- **Массовые рассылки**: Отправка сообщений всем пользователям
- **Сегментация**: Рассылка по группам (купившие, новые, активные)
- **Медиа поддержка**: Рассылка с фото, видео, документами
- **Статистика доставки**: Количество успешно доставленных сообщений

#### 6. Управление пользователями
- **Список пользователей**: Просмотр всех зарегистрированных
- **Профиль пользователя**: Детальная информация о покупках и активности
- **Блокировка/разблокировка**: Управление доступом пользователей
- **Поиск пользователей**: По username, имени или ID

#### 7. Финансовый функционал
- **Баланс бота**: Просмотр текущего баланса звезд (`getMyStarBalance`)
- **История транзакций**: Все входящие платежи (`getStarTransactions`)
- **Возвраты**: Система рефандов через `refundStarPayment`
- **Вывод средств**: Функционал для вывода через Telegram Wallet

## Технические требования

### API интеграции

#### Telegram Stars API методы:
```python
# Основные методы для работы с платежами
await bot.send_invoice(
    chat_id=user_id,
    title="Название урока",
    description="Описание урока",
    payload=f"lesson_{lesson_id}",
    provider_token="",  # Пустой для Stars
    currency="XTR",  # Telegram Stars
    prices=[LabeledPrice(label="Урок", amount=price_stars)]
)

await bot.answer_pre_checkout_query(
    pre_checkout_query_id=query.id,
    ok=True
)

# Получение баланса и транзакций
balance = await bot.get_my_star_balance()
transactions = await bot.get_star_transactions(limit=100)

# Возврат платежа
await bot.refund_star_payment(
    user_id=user_id,
    telegram_payment_charge_id=charge_id
)
```

### Middleware и безопасность

#### 1. Аутентификация админов
```python
class AdminAuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if event.from_user.id in ADMIN_IDS:
            data['is_admin'] = True
            return await handler(event, data)
        return await event.answer("Доступ запрещен")
```

#### 2. Throttling (защита от спама)
```python
class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit=1):
        self.rate_limit = rate_limit
        
    async def __call__(self, handler, event, data):
        # Проверка частоты запросов
        pass
```

### Состояния (FSM)

#### Пользовательские состояния
```python
class UserStates(StatesGroup):
    waiting_for_search = State()
    viewing_lesson = State()
    in_payment_process = State()
```

#### Административные состояния
```python
class AdminStates(StatesGroup):
    # Управление уроками
    creating_lesson = State()
    editing_lesson_title = State()
    editing_lesson_description = State()
    editing_lesson_price = State()
    uploading_lesson_content = State()
    
    # Рассылки
    creating_broadcast = State()
    uploading_broadcast_media = State()
    
    # Редактирование текстов
    editing_text = State()
```

## Этапы разработки и временные оценки

### Этап 1: Инфраструктура (13 часов)
1. **Настройка окружения** (2ч) - virtualenv, requirements.txt
2. **Структура проекта** (1ч) - создание папок и базовых файлов
3. **База данных** (3ч) - SQLAlchemy настройка, подключение
4. **Модели БД** (4ч) - создание всех моделей
5. **Миграции** (2ч) - Alembic настройка
6. **Базовый бот** (1ч) - основной файл и конфигурация

### Этап 2: Пользовательский функционал (24 часа)
1. **Регистрация и /start** (2ч) - базовые хендлеры
2. **Лид-магнит** (3ч) - бесплатный урок при регистрации
3. **Каталог уроков** (4ч) - список с пагинацией
4. **Карточка урока** (2ч) - детальная информация
5. **Система оплаты** (6ч) - интеграция с Telegram Stars
6. **Обработка платежей** (2ч) - успешные транзакции
7. **Личный кабинет** (3ч) - "Мои уроки"
8. **Просмотр контента** (2ч) - воспроизведение купленных уроков

### Этап 3: Административная панель (25 часов)
1. **Авторизация админов** (3ч) - middleware и права доступа
2. **CRUD уроков** (6ч) - создание, редактирование, удаление
3. **Медиа управление** (3ч) - загрузка и обработка файлов
4. **Редактор текстов** (4ч) - настройка интерфейсных сообщений
5. **Статистика** (4ч) - базовая аналитика
6. **Рассылки** (5ч) - массовые сообщения с медиа

### Этап 4: Продвинутые функции (18 часов)
1. **Вывод средств** (4ч) - интеграция с Telegram Wallet
2. **Рефанды** (3ч) - система возврата платежей
3. **Детальная аналитика** (4ч) - расширенная статистика
4. **Мультиязычность** (5ч) - поддержка нескольких языков
5. **Уведомления** (2ч) - система напоминаний

### Этап 5: Тестирование и деплой (15 часов)
1. **Unit тесты** (5ч) - тестирование основной логики
2. **Тестирование платежей** (3ч) - проверка в тестовом режиме
3. **Логирование** (2ч) - настройка мониторинга
4. **Docker** (3ч) - контейнеризация
5. **Документация** (2ч) - инструкции по установке

**Общее время: 95 часов**

## Риски и митигация

### Технические риски
1. **Ограничения Telegram Stars API** 
   - Митигация: Изучение документации, тестирование в sandbox
2. **Проблемы с медиа хранением**
   - Митигация: Использование file_id Telegram, облачное хранилище как бекап
3. **Высокая нагрузка**
   - Митигация: Реализация rate limiting, оптимизация БД запросов

### Бизнес риски
1. **Изменения в политике Telegram Stars**
   - Митигация: Отслеживание обновлений API, альтернативные методы оплаты
2. **Конкуренция**
   - Митигация: Уникальные функции, качественный UX

## Метрики успеха

### Технические метрики
- Время отклика бота < 2 секунды
- Успешность платежей > 98%
- Uptime > 99.5%
- Покрытие тестами > 80%

### Бизнес метрики  
- Конверсия из просмотра в покупку > 5%
- Средний чек > 50 звезд
- Retention rate (месячный) > 30%
- NPS (Net Promoter Score) > 8

## Развертывание и поддержка

### Docker конфигурация
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "bot.py"]
```

### Environment переменные
```env
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql://user:pass@localhost/dbname
ADMIN_IDS=123456789,987654321
WEBHOOK_URL=https://your-domain.com/webhook
DEBUG=False
```

### Мониторинг
- Логирование всех операций с платежами
- Метрики производительности (время ответа, количество запросов)
- Алерты при ошибках или падении системы
- Еженедельные отчеты по продажам и активности

## Заключение

Данная спецификация покрывает полный цикл разработки образовательного Telegram-бота с современной архитектурой, интеграцией с Telegram Stars для оплаты и полноценной административной панелью. Проект рассчитан на команду из 2-3 разработчиков и займет примерно 2-3 месяца активной разработки.

Архитектура позволяет легко масштабировать функционал, добавлять новые типы контента и интеграции. Использование современных технологий (aiogram 3.x, SQLAlchemy 2.x) гарантирует стабильность и производительность решения.