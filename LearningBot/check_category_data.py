#!/usr/bin/env python3
"""
Скрипт для проверки данных категорий и уроков
"""
import asyncio
from database.database import async_session
from database.models import Category, Lesson
from sqlalchemy import select


async def check_data():
    async with async_session() as session:
        # Проверяем категории
        print('=== КАТЕГОРИИ ===')
        result = await session.execute(select(Category))
        categories = result.scalars().all()
        for cat in categories:
            print(f'ID: {cat.id}, Name: "{cat.name}", Active: {cat.is_active}')
        
        print('\n=== УРОКИ ===')
        # Проверяем уроки с категориями
        result = await session.execute(select(Lesson))
        lessons = result.scalars().all()
        for lesson in lessons:
            print(f'ID: {lesson.id}, Title: "{lesson.title}"')
            print(f'  category_id: {lesson.category_id}')
            print(f'  category (old): "{lesson.category}"')
            print(f'  is_active: {lesson.is_active}')
            print()


if __name__ == "__main__":
    asyncio.run(check_data())