"""
Test UI flow for lesson functionality - simulating real user interactions
"""
import asyncio
import sys
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import AsyncMock, MagicMock

# Add current directory to path
sys.path.insert(0, '.')

from database.database import Base
from database.models import User, Lesson, Purchase, Admin
from services.user import UserService
from services.lesson import LessonService

# Import handlers
from handlers.user.catalog import show_catalog, show_lessons_by_category
from handlers.user.lesson_detail import show_lesson_detail
from handlers.user.start import cmd_start

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

def create_mock_callback(user_id=897676474, data="catalog"):
    """Create a mock callback query"""
    callback = AsyncMock()
    callback.from_user.id = user_id
    callback.data = data
    callback.answer = AsyncMock()
    
    # Mock message
    message = AsyncMock()
    message.edit_text = AsyncMock()
    message.answer = AsyncMock()
    callback.message = message
    
    return callback

def create_mock_message(user_id=897676474, text="/start"):
    """Create a mock message"""
    message = AsyncMock()
    message.from_user.id = user_id
    message.text = text
    message.answer = AsyncMock()
    
    # Mock user
    user = MagicMock()
    user.id = user_id
    user.username = "dmitriy_mityuk"
    user.full_name = "Дмитрий Митюк"
    user.language_code = "ru"
    message.from_user = user
    
    return message

async def test_ui_lesson_flow():
    """Test the complete UI lesson flow"""
    print("🧪 Testing UI lesson flow...")
    
    # Create test database engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        # Create test user
        user = User(
            user_id=897676474,
            username="dmitriy_mityuk",
            full_name="Дмитрий Митюк",
            language="ru",
            registration_date=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
            is_active=True
        )
        session.add(user)
        
        # Create test admin
        admin = Admin(
            user_id=897676474,
            username="dmitriy_mityuk",
            permissions="all",
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        session.add(admin)
        
        # Create test lessons
        lessons = [
            Lesson(
                title="Free Python Lesson",
                description="Learn Python basics for free",
                price_stars=0,
                content_type="video",
                file_id="test_video_123",
                duration=600,
                is_active=True,
                is_free=True,
                category="Programming",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                views_count=0
            ),
            Lesson(
                title="Advanced JavaScript",
                description="Advanced JavaScript concepts and patterns",
                price_stars=100,
                content_type="video",
                file_id="test_video_456",
                duration=900,
                is_active=True,
                is_free=False,
                category="Programming",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                views_count=5
            )
        ]
        
        for lesson in lessons:
            session.add(lesson)
        
        await session.commit()
        
        print("  ✅ 1. Testing /start command...")
        try:
            message = create_mock_message()
            state = AsyncMock()
            await cmd_start(message, session, state)
            print("     ✅ /start command works")
        except Exception as e:
            print(f"     ❌ /start command failed: {e}")
        
        print("  ✅ 2. Testing catalog button...")
        try:
            callback = create_mock_callback(data="catalog")
            state = AsyncMock()
            await show_catalog(callback, session, state)
            print("     ✅ Catalog button works")
            
            # Check if edit_text was called
            if callback.message.edit_text.called:
                print("     ✅ Message edit_text was called")
            else:
                print("     ❌ Message edit_text was NOT called")
                
        except Exception as e:
            print(f"     ❌ Catalog button failed: {e}")
        
        print("  ✅ 3. Testing 'все уроки' (all lessons) button...")
        try:
            callback = create_mock_callback(data="catalog:all")
            await show_lessons_by_category(callback, session)
            print("     ✅ 'Все уроки' button works")
            
            # Check if edit_text was called
            if callback.message.edit_text.called:
                print("     ✅ Message edit_text was called for all lessons")
            else:
                print("     ❌ Message edit_text was NOT called for all lessons")
                
        except Exception as e:
            print(f"     ❌ 'Все уроки' button failed: {e}")
        
        print("  ✅ 4. Testing individual lesson detail...")
        try:
            callback = create_mock_callback(data="lesson:1")
            await show_lesson_detail(callback, session)
            print("     ✅ Lesson detail works")
            
            # Check if edit_text was called
            if callback.message.edit_text.called:
                print("     ✅ Message edit_text was called for lesson detail")
            else:
                print("     ❌ Message edit_text was NOT called for lesson detail")
                
        except Exception as e:
            print(f"     ❌ Lesson detail failed: {e}")
        
        print("  ✅ 5. Testing lesson access and permissions...")
        lesson_service = LessonService(session)
        user_service = UserService(session)
        
        # Test free lesson access
        has_free_access = await lesson_service.check_user_has_lesson(897676474, 1)
        print(f"     🎁 Free lesson access: {has_free_access}")
        
        # Test paid lesson access (should be False without purchase)
        has_paid_access = await lesson_service.check_user_has_lesson(897676474, 2)
        print(f"     💰 Paid lesson access: {has_paid_access}")
        
    await engine.dispose()
    print("🎉 UI lesson flow test completed!")

if __name__ == "__main__":
    asyncio.run(test_ui_lesson_flow())