"""
Test script for support button functionality
"""
import asyncio
import sys
import os

# Add the LearningBot directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock, AsyncMock, patch
from aiogram.types import CallbackQuery, Message, User as TelegramUser
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.user.start import show_support, handle_support_message
from services.user import UserService
from states.user import UserStates
from keyboards.user import main_menu_keyboard


class MockTelegramUser:
    """Mock Telegram user for testing"""
    def __init__(self, user_id: int, username: str = None, full_name: str = "Test User"):
        self.id = user_id
        self.username = username
        self.full_name = full_name


class MockMessage:
    """Mock message for testing"""
    def __init__(self, text: str = None, from_user: TelegramUser = None):
        self.text = text
        self.from_user = from_user or MockTelegramUser(12345, "testuser", "Test User")
        self.date = asyncio.get_event_loop().time()
        self.answer = AsyncMock()


class MockCallbackQuery:
    """Mock callback query for testing"""
    def __init__(self, data: str = "support", from_user: TelegramUser = None):
        self.data = data
        self.from_user = from_user or MockTelegramUser(12345, "testuser", "Test User")
        self.message = Mock()
        self.message.edit_text = AsyncMock()
        self.answer = AsyncMock()


async def test_support_button_visibility():
    """Test that support button is visible in main menu"""
    print("Testing support button visibility...")
    
    keyboard = main_menu_keyboard()
    
    # Check if support button exists
    support_found = False
    for row in keyboard.inline_keyboard:
        for button in row:
            if button.callback_data == "support":
                support_found = True
                print(f"   ✅ Support button found: {button.text}")
                break
    
    if not support_found:
        print("   ❌ Support button not found in main menu!")
        return False
    
    return True


async def test_show_support_handler():
    """Test the show_support handler"""
    print("Testing show_support handler...")
    
    # Create mock objects
    callback = MockCallbackQuery()
    session = AsyncMock(spec=AsyncSession)
    state = AsyncMock(spec=FSMContext)
    
    # Mock user service
    with patch('handlers.user.start.UserService') as mock_user_service:
        mock_service_instance = AsyncMock()
        mock_user_service.return_value = mock_service_instance
        
        try:
            # Call the handler
            await show_support(callback, session, state)
            
            # Verify state was set
            state.set_state.assert_called_once_with(UserStates.contacting_support)
            print("   ✅ State set to contacting_support")
            
            # Verify message was edited
            callback.message.edit_text.assert_called_once()
            print("   ✅ Support message displayed")
            
            # Verify callback was answered
            callback.answer.assert_called_once()
            print("   ✅ Callback answered")
            
            # Verify user activity was updated
            mock_service_instance.update_user_activity.assert_called_once_with(callback.from_user.id)
            print("   ✅ User activity updated")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error in show_support handler: {e}")
            return False


async def test_handle_support_message():
    """Test the handle_support_message handler"""
    print("Testing handle_support_message handler...")
    
    # Create mock objects
    message = MockMessage("I need help with my lesson")
    session = AsyncMock(spec=AsyncSession)
    state = AsyncMock(spec=FSMContext)
    
    # Mock user service and user
    with patch('handlers.user.start.UserService') as mock_user_service:
        mock_service_instance = AsyncMock()
        mock_user_service.return_value = mock_service_instance
        
        # Mock user object
        mock_user = Mock()
        mock_user.full_name = "Test User"
        mock_service_instance.get_user_by_telegram_id.return_value = mock_user
        
        try:
            # Call the handler
            await handle_support_message(message, session, state)
            
            # Verify user was retrieved
            mock_service_instance.get_user_by_telegram_id.assert_called_once_with(message.from_user.id)
            print("   ✅ User retrieved from database")
            
            # Verify confirmation message was sent
            message.answer.assert_called_once()
            args, kwargs = message.answer.call_args
            assert "принято" in args[0].lower()  # Check for confirmation text
            print("   ✅ Confirmation message sent")
            
            # Verify state was cleared
            state.clear.assert_called_once()
            print("   ✅ State cleared")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error in handle_support_message handler: {e}")
            return False


async def test_support_with_empty_message():
    """Test handling of empty support message"""
    print("Testing empty support message handling...")
    
    # Create mock objects with no text
    message = MockMessage(text=None)
    session = AsyncMock(spec=AsyncSession)
    state = AsyncMock(spec=FSMContext)
    
    try:
        # Call the handler
        await handle_support_message(message, session, state)
        
        # Verify error message was sent
        message.answer.assert_called_once()
        args, kwargs = message.answer.call_args
        assert "текстовое сообщение" in args[0].lower()
        print("   ✅ Error message for empty text sent")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error handling empty message: {e}")
        return False


async def test_support_flow_states():
    """Test the complete support flow state management"""
    print("Testing support flow state management...")
    
    # Test transition from normal state to support state
    callback = MockCallbackQuery()
    session = AsyncMock(spec=AsyncSession)
    state = AsyncMock(spec=FSMContext)
    
    with patch('handlers.user.start.UserService'):
        try:
            # Step 1: User clicks support button
            await show_support(callback, session, state)
            state.set_state.assert_called_with(UserStates.contacting_support)
            print("   ✅ State transitioned to contacting_support")
            
            # Step 2: User sends message
            message = MockMessage("Test support message")
            state_message = AsyncMock(spec=FSMContext)
            
            with patch('handlers.user.start.UserService') as mock_user_service:
                mock_service_instance = AsyncMock()
                mock_user_service.return_value = mock_service_instance
                mock_user = Mock()
                mock_user.full_name = "Test User"
                mock_service_instance.get_user_by_telegram_id.return_value = mock_user
                
                await handle_support_message(message, session, state_message)
                state_message.clear.assert_called_once()
                print("   ✅ State cleared after message processing")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error in state management test: {e}")
            return False


async def run_all_tests():
    """Run all support functionality tests"""
    print("🧪 Testing Support Button Functionality")
    print("=" * 50)
    
    tests = [
        ("Support Button Visibility", test_support_button_visibility),
        ("Show Support Handler", test_show_support_handler),
        ("Handle Support Message", test_handle_support_message),
        ("Empty Message Handling", test_support_with_empty_message),
        ("Support Flow States", test_support_flow_states),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"   ✅ PASSED")
            else:
                print(f"   ❌ FAILED")
        except Exception as e:
            print(f"   ❌ FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed!")
    else:
        print(f"❌ {total - passed} tests failed")
    
    return passed == total


if __name__ == "__main__":
    result = asyncio.run(run_all_tests())
    
    # Print analysis and recommendations
    print("\n🔍 ANALYSIS:")
    print("Current support functionality includes:")
    print("  ✅ Support button in main menu")
    print("  ✅ Support message collection")
    print("  ✅ State management")
    print("  ✅ Basic user feedback")
    
    print("\n❌ MISSING FEATURES:")
    print("  - Admin notification system")
    print("  - Support ticket persistence")
    print("  - Admin interface for ticket management")
    print("  - Two-way communication")
    print("  - Ticket status tracking")
    
    print("\n📝 RECOMMENDATIONS:")
    print("  1. Implement SupportTicket and SupportResponse models")
    print("  2. Create SupportService for ticket management")
    print("  3. Add admin notification system")
    print("  4. Build admin interface for support")
    print("  5. Add comprehensive testing")
    
    sys.exit(0 if result else 1)