"""
Сервис управления текстами интерфейса
"""
import logging
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TextSetting

logger = logging.getLogger(__name__)


class TextService:
    """Сервис для управления настройками текстов интерфейса"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_text_settings(self) -> List[TextSetting]:
        """Получить все настройки текстов"""
        try:
            query = select(TextSetting).order_by(TextSetting.category, TextSetting.key)
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка при получении всех настроек текстов: {e}")
            return []

    async def get_text_settings_by_category(self, category: str) -> List[TextSetting]:
        """Получить настройки текстов по категории"""
        try:
            query = select(TextSetting).where(
                TextSetting.category == category
            ).order_by(TextSetting.key)
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка при получении настроек категории {category}: {e}")
            return []

    async def get_text_setting_by_key(self, key: str) -> Optional[TextSetting]:
        """Получить настройку по ключу"""
        try:
            query = select(TextSetting).where(TextSetting.key == key)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка при получении настройки по ключу {key}: {e}")
            return None

    async def create_text_setting(
        self,
        key: str,
        value_ru: str,
        category: str,
        value_en: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[TextSetting]:
        """Создать новую настройку текста"""
        try:
            # Валидация ключа
            if not self.validate_key_format(key):
                logger.error(f"Невалидный формат ключа: {key}")
                return None

            # Проверяем, что такой ключ не существует
            existing = await self.get_text_setting_by_key(key)
            if existing:
                logger.error(f"Настройка с ключом {key} уже существует")
                return None

            text_setting = TextSetting(
                key=key,
                value_ru=value_ru,
                value_en=value_en,
                category=category,
                description=description,
                updated_at=datetime.now(timezone.utc)
            )

            self.session.add(text_setting)
            await self.session.commit()
            await self.session.refresh(text_setting)

            logger.info(f"Создана новая настройка текста: {key}")
            return text_setting

        except Exception as e:
            logger.error(f"Ошибка при создании настройки текста {key}: {e}")
            await self.session.rollback()
            return None

    async def update_text_setting(
        self,
        key: str,
        value_ru: Optional[str] = None,
        value_en: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[TextSetting]:
        """Обновить настройку текста"""
        try:
            text_setting = await self.get_text_setting_by_key(key)
            if not text_setting:
                logger.error(f"Настройка с ключом {key} не найдена")
                return None

            # Обновляем только переданные поля
            if value_ru is not None:
                text_setting.value_ru = value_ru
            if value_en is not None:
                text_setting.value_en = value_en
            if description is not None:
                text_setting.description = description

            text_setting.updated_at = datetime.now(timezone.utc)

            await self.session.commit()
            logger.info(f"Обновлена настройка текста: {key}")
            return text_setting

        except Exception as e:
            logger.error(f"Ошибка при обновлении настройки текста {key}: {e}")
            await self.session.rollback()
            return None

    async def delete_text_setting(self, key: str) -> bool:
        """Удалить настройку текста"""
        try:
            text_setting = await self.get_text_setting_by_key(key)
            if not text_setting:
                logger.error(f"Настройка с ключом {key} не найдена")
                return False

            await self.session.delete(text_setting)
            await self.session.commit()

            logger.info(f"Удалена настройка текста: {key}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при удалении настройки текста {key}: {e}")
            await self.session.rollback()
            return False

    async def get_text_value(self, key: str, language: str = "ru") -> Optional[str]:
        """Получить значение текста по ключу и языку"""
        try:
            text_setting = await self.get_text_setting_by_key(key)
            if not text_setting:
                return None

            if language == "en" and text_setting.value_en:
                return text_setting.value_en
            
            # Fallback на русский язык
            return text_setting.value_ru

        except Exception as e:
            logger.error(f"Ошибка при получении значения текста {key}: {e}")
            return None

    async def get_categories_list(self) -> List[str]:
        """Получить список всех категорий"""
        try:
            query = select(TextSetting.category).distinct().order_by(TextSetting.category)
            result = await self.session.execute(query)
            categories = [row[0] for row in result.fetchall()]
            return categories
        except Exception as e:
            logger.error(f"Ошибка при получении списка категорий: {e}")
            return []

    async def bulk_update_texts(self, updates: List[Dict[str, Any]]) -> int:
        """Массовое обновление текстов"""
        success_count = 0
        
        try:
            for update in updates:
                key = update.get('key')
                if not key:
                    continue

                result = await self.update_text_setting(
                    key=key,
                    value_ru=update.get('value_ru'),
                    value_en=update.get('value_en'),
                    description=update.get('description')
                )

                if result:
                    success_count += 1

            logger.info(f"Массовое обновление завершено: {success_count} из {len(updates)}")
            return success_count

        except Exception as e:
            logger.error(f"Ошибка при массовом обновлении текстов: {e}")
            return success_count

    async def search_text_settings(self, search_term: str) -> List[TextSetting]:
        """Поиск настроек текстов по ключу, значению или описанию"""
        try:
            search_pattern = f"%{search_term.lower()}%"
            
            query = select(TextSetting).where(
                (func.lower(TextSetting.key).like(search_pattern)) |
                (func.lower(TextSetting.value_ru).like(search_pattern)) |
                (func.lower(TextSetting.value_en).like(search_pattern)) |
                (func.lower(TextSetting.description).like(search_pattern))
            ).order_by(TextSetting.category, TextSetting.key)
            
            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Ошибка при поиске настроек текстов: {e}")
            return []

    async def get_text_statistics(self) -> Dict[str, Any]:
        """Получить статистику по текстам"""
        try:
            all_texts = await self.get_all_text_settings()
            
            # Базовая статистика
            total_texts = len(all_texts)
            texts_with_translation = len([t for t in all_texts if t.value_en])
            
            # Распределение по категориям
            category_distribution = {}
            for text in all_texts:
                category_distribution[text.category] = category_distribution.get(text.category, 0) + 1
            
            return {
                'total_texts': total_texts,
                'texts_with_translation': texts_with_translation,
                'categories_count': len(category_distribution),
                'category_distribution': category_distribution,
                'translation_percentage': (texts_with_translation / total_texts * 100) if total_texts > 0 else 0
            }

        except Exception as e:
            logger.error(f"Ошибка при получении статистики текстов: {e}")
            return {}

    def validate_key_format(self, key: str) -> bool:
        """Валидация формата ключа"""
        if not key or not isinstance(key, str):
            return False
        
        # Ключ должен содержать только латинские буквы, цифры и подчеркивания
        # Должен начинаться с буквы
        pattern = r'^[a-zA-Z][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, key))

    async def export_texts_for_translation(self) -> List[Dict[str, Any]]:
        """Экспорт текстов для перевода"""
        try:
            all_texts = await self.get_all_text_settings()
            
            export_data = []
            for text in all_texts:
                export_data.append({
                    'key': text.key,
                    'category': text.category,
                    'value_ru': text.value_ru,
                    'value_en': text.value_en,
                    'description': text.description,
                    'updated_at': text.updated_at.isoformat() if text.updated_at else None
                })
            
            return export_data

        except Exception as e:
            logger.error(f"Ошибка при экспорте текстов: {e}")
            return []

    async def import_texts_from_translation(self, import_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Импорт переведенных текстов"""
        try:
            stats = {'updated': 0, 'created': 0, 'errors': 0}
            
            for data in import_data:
                key = data.get('key')
                if not key:
                    stats['errors'] += 1
                    continue

                existing = await self.get_text_setting_by_key(key)
                
                if existing:
                    # Обновляем существующий
                    result = await self.update_text_setting(
                        key=key,
                        value_ru=data.get('value_ru'),
                        value_en=data.get('value_en'),
                        description=data.get('description')
                    )
                    if result:
                        stats['updated'] += 1
                    else:
                        stats['errors'] += 1
                else:
                    # Создаем новый
                    result = await self.create_text_setting(
                        key=key,
                        value_ru=data.get('value_ru', ''),
                        category=data.get('category', 'imported'),
                        value_en=data.get('value_en'),
                        description=data.get('description')
                    )
                    if result:
                        stats['created'] += 1
                    else:
                        stats['errors'] += 1

            logger.info(f"Импорт завершен: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Ошибка при импорте текстов: {e}")
            return {'updated': 0, 'created': 0, 'errors': len(import_data)}

    async def initialize_default_texts(self) -> bool:
        """Инициализация текстов по умолчанию"""
        try:
            default_texts = [
                {
                    'key': 'welcome_message',
                    'value_ru': '🤖 Добро пожаловать в мир искусственного интеллекта!\n\nОсвойте нейронные сети, машинное обучение и создавайте собственные AI-продукты!',
                    'value_en': '🤖 Welcome to the world of artificial intelligence!\n\nMaster neural networks, machine learning, and create your own AI products!',
                    'category': 'messages',
                    'description': 'Приветственное сообщение при команде /start'
                },
                {
                    'key': 'button_catalog',
                    'value_ru': '🧠 Каталог AI-курсов',
                    'value_en': '🧠 AI Courses Catalog',
                    'category': 'buttons',
                    'description': 'Кнопка каталога курсов по ИИ'
                },
                {
                    'key': 'button_profile',
                    'value_ru': '👨‍💻 Мой AI-профиль',
                    'value_en': '👨‍💻 My AI Profile',
                    'category': 'buttons',
                    'description': 'Кнопка профиля пользователя'
                },
                {
                    'key': 'error_payment_failed',
                    'value_ru': '❌ Ошибка при оплате курса. Попробуйте еще раз.',
                    'value_en': '❌ Course payment error. Please try again.',
                    'category': 'errors',
                    'description': 'Сообщение об ошибке платежа'
                },
                {
                    'key': 'success_purchase',
                    'value_ru': '✨ Курс успешно приобретен! Теперь вы можете изучать современные технологии ИИ!',
                    'value_en': '✨ Course successfully purchased! Now you can learn modern AI technologies!',
                    'category': 'success',
                    'description': 'Сообщение об успешной покупке'
                }
            ]

            created_count = 0
            for text_data in default_texts:
                # Проверяем, что текст не существует
                existing = await self.get_text_setting_by_key(text_data['key'])
                if not existing:
                    result = await self.create_text_setting(**text_data)
                    if result:
                        created_count += 1

            logger.info(f"Инициализировано {created_count} текстов по умолчанию")
            return True

        except Exception as e:
            logger.error(f"Ошибка при инициализации текстов по умолчанию: {e}")
            return False