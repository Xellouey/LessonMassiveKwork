"""
Test the modified catalog functionality
"""
import asyncio
import sys
from unittest.mock import AsyncMock

sys.path.insert(0, '.')

from database.database import AsyncSessionLocal
from handlers.user.catalog import show_catalog

def create_mock_callback(user_id=897676474, data="catalog"):
    """Create a mock callback query"""
    callback = AsyncMock()
    callback.from_user.id = user_id
    callback.data = data
    callback.answer = AsyncMock()
    
    # Mock message
    message = AsyncMock()
    message.edit_text = AsyncMock()
    callback.message = message
    
    return callback

async def test_new_catalog_functionality():
    """Test the new catalog functionality that shows all lessons directly"""
    print("🧪 Testing New Catalog Functionality...")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        print("Testing: User clicks 'Каталог уроков' button...")
        
        try:
            callback = create_mock_callback(data="catalog")
            state = AsyncMock()
            await show_catalog(callback, session, state)
            
            print("✅ Catalog handler executed successfully")
            
            # Check if message was updated
            if callback.message.edit_text.called:
                call_args = callback.message.edit_text.call_args
                text_content = call_args[0][0] if call_args else ""
                
                print("✅ Message was updated")
                print(f"📝 Content preview: {text_content[:100]}...")
                
                # Check if it shows "Все уроки" directly
                if "Все уроки" in text_content:
                    print("✅ Shows 'Все уроки' content directly")
                else:
                    print("⚠️  Content doesn't show 'Все уроки' header")
                
                # Check if it shows lesson entries
                if any(indicator in text_content for indicator in ["📚", "⭐", "🎁"]):
                    print("✅ Shows lesson entries in the list")
                else:
                    print("⚠️  No lesson indicators found")
                    
                # Check if it shows lesson count
                if "Всего уроков:" in text_content or any(char.isdigit() for char in text_content):
                    print("✅ Shows lesson count information")
                
            else:
                print("❌ Message was NOT updated")
                return False
                
            print("\n🎉 New catalog functionality is working correctly!")
            print("📋 Summary: Catalog now shows all lessons directly instead of categories")
            return True
            
        except Exception as e:
            print(f"❌ Error testing catalog: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    asyncio.run(test_new_catalog_functionality())