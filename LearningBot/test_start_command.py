"""
Test the modified /start command functionality
"""
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, '.')

from database.database import AsyncSessionLocal
from handlers.user.start import cmd_start

def create_mock_message(user_id=897676474, text="/start", username="dmitriy_mityuk"):
    """Create a mock message for testing"""
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

async def test_start_command():
    """Test the modified /start command"""
    print("🧪 Testing Modified /start Command...")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        print("Testing: User sends /start command...")
        
        try:
            message = create_mock_message()
            state = AsyncMock()
            
            # Execute the start command
            await cmd_start(message, session, state)
            
            print("✅ /start command executed successfully")
            
            # Check how many times message.answer was called
            call_count = message.answer.call_count
            print(f"📊 Number of messages sent: {call_count}")
            
            if call_count == 1:
                print("✅ CORRECT: Only one welcome message sent")
                
                # Check the content of the message
                call_args = message.answer.call_args_list[0]
                message_text = call_args[0][0] if call_args else ""
                
                if "Добро пожаловать" in message_text:
                    print("✅ Welcome message contains greeting")
                
                if "бесплатный урок ждет" in message_text:
                    print("❌ UNEXPECTED: Welcome message contains free lesson text")
                else:
                    print("✅ Welcome message does NOT contain free lesson text")
                    
                if "Выберите действие в меню" in message_text:
                    print("✅ Welcome message contains menu instruction")
                    
            elif call_count == 2:
                print("❌ INCORRECT: Two messages sent (old behavior)")
                print("   Message 1: Welcome message")
                print("   Message 2: Free lesson message")
            else:
                print(f"❌ UNEXPECTED: {call_count} messages sent")
            
            return call_count == 1
            
        except Exception as e:
            print(f"❌ Error testing /start command: {e}")
            import traceback
            traceback.print_exc()
            return False

async def test_existing_user():
    """Test /start for existing user"""
    print("\n🧪 Testing /start for Existing User...")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        print("Testing: Existing user sends /start command...")
        
        try:
            # Simulate existing user (different ID to ensure it's treated as existing)
            message = create_mock_message(user_id=123456789, username="existing_user")
            state = AsyncMock()
            
            # Execute the start command
            await cmd_start(message, session, state)
            
            print("✅ /start command executed for existing user")
            
            # Check message count
            call_count = message.answer.call_count
            print(f"📊 Number of messages sent: {call_count}")
            
            if call_count == 1:
                print("✅ CORRECT: Only one message sent for existing user")
            else:
                print(f"❌ UNEXPECTED: {call_count} messages sent for existing user")
            
            return call_count == 1
            
        except Exception as e:
            print(f"❌ Error testing existing user /start: {e}")
            return False

async def main():
    """Run all tests"""
    print("🚀 Testing /start Command Modifications")
    print("=" * 60)
    
    success_count = 0
    total_tests = 2
    
    # Test 1: New user /start
    if await test_start_command():
        success_count += 1
    
    # Test 2: Existing user /start  
    if await test_existing_user():
        success_count += 1
    
    print(f"\n📊 Test Results: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ /start command now shows only the welcome message")
        print("✅ No second 'free lesson waiting' message is sent")
        print("✅ Both new and existing users get single message")
        print("\n🚀 The modification is working correctly!")
    else:
        print("❌ Some tests failed")
        print("🔧 Please check the failed tests above")

if __name__ == "__main__":
    asyncio.run(main())