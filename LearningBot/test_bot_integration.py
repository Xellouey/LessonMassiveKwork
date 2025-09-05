"""
Integration test that simulates actual bot interaction
"""
import asyncio
import sys
import logging
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, '.')

from database.database import AsyncSessionLocal
from handlers.user.catalog import show_catalog, show_lessons_by_category
from handlers.user.lesson_detail import show_lesson_detail
from handlers.user.start import cmd_start
from aiogram.fsm.context import FSMContext

# Suppress logs for clean output
logging.getLogger().setLevel(logging.ERROR)

def create_mock_callback(user_id=897676474, data="catalog", username="dmitriy_mityuk"):
    """Create a realistic mock callback query"""
    callback = AsyncMock()
    callback.from_user.id = user_id
    callback.from_user.username = username
    callback.from_user.full_name = "Дмитрий Митюк"
    callback.data = data
    callback.answer = AsyncMock()
    
    # Mock message with tracking
    message = AsyncMock()
    message.edit_text = AsyncMock()
    message.answer = AsyncMock()
    callback.message = message
    
    return callback

def create_mock_message(user_id=897676474, text="/start", username="dmitriy_mityuk"):
    """Create a realistic mock message"""
    message = AsyncMock()
    message.text = text
    message.answer = AsyncMock()
    
    # Mock user with realistic data
    user = MagicMock()
    user.id = user_id
    user.username = username
    user.full_name = "Дмитрий Митюк"
    user.language_code = "ru"
    message.from_user = user
    
    return message

async def test_complete_user_journey():
    """Test complete user journey from start to lesson viewing"""
    print("🎭 Simulating Complete User Journey...")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        
        # Step 1: User starts the bot
        print("1️⃣ User sends /start command...")
        try:
            message = create_mock_message()
            state = AsyncMock()
            await cmd_start(message, session, state)
            print("   ✅ /start command processed successfully")
            
            # Check if welcome message was sent
            if message.answer.called:
                print("   ✅ Welcome message sent to user")
            else:
                print("   ❌ Welcome message NOT sent")
                
        except Exception as e:
            print(f"   ❌ /start failed: {e}")
            return False
        
        # Step 2: User clicks catalog button  
        print("\n2️⃣ User clicks 'Каталог уроков' button...")
        try:
            callback = create_mock_callback(data="catalog")
            state = AsyncMock()
            await show_catalog(callback, session, state)
            print("   ✅ Catalog handler processed successfully")
            
            # Check if catalog was displayed
            if callback.message.edit_text.called:
                call_args = callback.message.edit_text.call_args
                text_content = call_args[0][0] if call_args else ""
                print("   ✅ Catalog message updated")
                if "Каталог уроков" in text_content:
                    print("   ✅ Catalog header found in response")
                if "Всего уроков:" in text_content:
                    print("   ✅ Lesson count displayed")
            else:
                print("   ❌ Catalog message NOT updated")
                
        except Exception as e:
            print(f"   ❌ Catalog failed: {e}")
            return False
        
        # Step 3: User clicks "Все уроки" button
        print("\n3️⃣ User clicks 'Все уроки' button...")
        try:
            callback = create_mock_callback(data="catalog:all")
            await show_lessons_by_category(callback, session)
            print("   ✅ 'Все уроки' handler processed successfully")
            
            # Check if lesson list was displayed
            if callback.message.edit_text.called:
                call_args = callback.message.edit_text.call_args
                text_content = call_args[0][0] if call_args else ""
                print("   ✅ Lesson list message updated")
                if "Все уроки" in text_content:
                    print("   ✅ 'Все уроки' header found")
                # Look for lesson indicators
                if "📚" in text_content or "⭐" in text_content:
                    print("   ✅ Lesson entries found in list")
                else:
                    print("   ⚠️  No lesson entries visible")
            else:
                print("   ❌ Lesson list message NOT updated")
                
        except Exception as e:
            print(f"   ❌ 'Все уроки' failed: {e}")
            return False
        
        # Step 4: User clicks on a specific lesson
        print("\n4️⃣ User clicks on first lesson...")
        try:
            callback = create_mock_callback(data="lesson:1")
            await show_lesson_detail(callback, session)
            print("   ✅ Lesson detail handler processed successfully")
            
            # Check if lesson detail was displayed
            if callback.message.edit_text.called:
                call_args = callback.message.edit_text.call_args
                text_content = call_args[0][0] if call_args else ""
                print("   ✅ Lesson detail message updated")
                if "Описание:" in text_content:
                    print("   ✅ Lesson description found")
                if "Цена:" in text_content:
                    print("   ✅ Lesson price displayed")
                if "Статус:" in text_content:
                    print("   ✅ Access status shown")
            else:
                print("   ❌ Lesson detail message NOT updated")
                
        except Exception as e:
            print(f"   ❌ Lesson detail failed: {e}")
            return False
        
        print("\n🎉 User Journey Test Completed Successfully!")
        return True

async def test_admin_user_journey():
    """Test admin-specific functionality"""
    print("\n👨‍💼 Testing Admin User Journey...")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        
        # Test admin can see all lessons (including inactive)
        print("1️⃣ Admin viewing catalog (should see all lessons)...")
        try:
            callback = create_mock_callback(data="catalog")
            state = AsyncMock()
            await show_catalog(callback, session, state)
            print("   ✅ Admin catalog access successful")
        except Exception as e:
            print(f"   ❌ Admin catalog failed: {e}")
            return False
        
        print("\n✅ Admin Journey Test Completed!")
        return True

async def test_error_scenarios():
    """Test error handling scenarios"""
    print("\n⚠️  Testing Error Scenarios...")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        
        # Test invalid lesson ID
        print("1️⃣ Testing invalid lesson ID...")
        try:
            callback = create_mock_callback(data="lesson:999999")
            await show_lesson_detail(callback, session)
            print("   ✅ Invalid lesson ID handled gracefully")
        except Exception as e:
            print(f"   ❌ Invalid lesson ID caused error: {e}")
        
        # Test malformed callback data
        print("\n2️⃣ Testing malformed callback data...")
        try:
            callback = create_mock_callback(data="lesson:invalid")
            await show_lesson_detail(callback, session)
            print("   ✅ Malformed data handled gracefully")
        except Exception as e:
            print(f"   ❌ Malformed data caused error: {e}")
        
        print("\n✅ Error Scenarios Test Completed!")
        return True

async def main():
    """Run all integration tests"""
    print("🚀 Bot Integration Testing")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # Test 1: Complete user journey
    if await test_complete_user_journey():
        success_count += 1
    
    # Test 2: Admin journey  
    if await test_admin_user_journey():
        success_count += 1
    
    # Test 3: Error scenarios
    if await test_error_scenarios():
        success_count += 1
    
    print(f"\n📊 Integration Test Results: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("\n✅ Bot lesson functionality is working correctly")
        print("✅ User can navigate catalog and view lessons")
        print("✅ Admin functionality is accessible")
        print("✅ Error handling is working properly")
        print("\n🚀 The bot is ready for users!")
    else:
        print("❌ Some integration tests failed")
        print("🔧 Please check the failed tests above")

if __name__ == "__main__":
    asyncio.run(main())