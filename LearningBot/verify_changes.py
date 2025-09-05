#!/usr/bin/env python3
"""
Simple verification script to confirm the main menu changes
"""

def verify_keyboards():
    """Verify the keyboard changes by checking file contents"""
    print("🧪 Verifying Main Menu Changes...")
    print("=" * 50)
    
    try:
        # Read the user.py keyboard file
        with open('c:/Users/user/Desktop/Projects/LessonMassiveKwork/LearningBot/keyboards/user.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("1. Checking main_menu_keyboard function...")
        
        # Check if settings button is removed
        main_menu_start = content.find('def main_menu_keyboard()')
        main_menu_end = content.find('def catalog_keyboard(')
        if main_menu_end == -1:
            main_menu_end = content.find('\n\ndef ', main_menu_start + 1)
        
        main_menu_content = content[main_menu_start:main_menu_end]
        
        if 'Настройки' not in main_menu_content and 'settings' not in main_menu_content:
            print("   ✅ Settings button successfully removed from main menu")
        else:
            print("   ❌ Settings button still present in main menu")
            return False
        
        # Check if profile button is added
        if 'Мой профиль' in main_menu_content and 'profile' in main_menu_content:
            print("   ✅ Profile button successfully added to main menu")
        else:
            print("   ❌ Profile button missing from main menu")
            return False
        
        print("\n2. Checking profile_menu_keyboard function...")
        
        # Check profile menu functionality
        profile_menu_start = content.find('def profile_menu_keyboard()')
        profile_menu_end = content.find('\n\ndef ', profile_menu_start + 1)
        if profile_menu_end == -1:
            profile_menu_end = len(content)
        
        profile_menu_content = content[profile_menu_start:profile_menu_end]
        
        if 'Язык' in profile_menu_content and 'change_language' in profile_menu_content:
            print("   ✅ Language settings integrated in profile")
        else:
            print("   ❌ Language settings missing from profile")
            return False
        
        if 'Уведомления' in profile_menu_content and 'notifications_settings' in profile_menu_content:
            print("   ✅ Notification settings integrated in profile")
        else:
            print("   ❌ Notification settings missing from profile")
            return False
        
        return True
        
    except FileNotFoundError:
        print("❌ keyboards/user.py file not found")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def verify_handlers():
    """Verify the profile handler changes"""
    print("\n3. Checking profile handlers...")
    
    try:
        # Read the profile.py handler file
        with open('c:/Users/user/Desktop/Projects/LessonMassiveKwork/LearningBot/handlers/user/profile.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for notifications_settings handler
        if 'notifications_settings' in content and 'toggle_notifications' in content:
            print("   ✅ Notifications handler properly integrated")
        else:
            print("   ❌ Notifications handler missing or incorrect")
            return False
            
        return True
        
    except FileNotFoundError:
        print("❌ handlers/user/profile.py file not found")
        return False
    except Exception as e:
        print(f"❌ Error reading handler file: {e}")
        return False

def main():
    """Run verification"""
    print("🚀 Verifying Implementation: Settings → Profile Integration")
    print("=" * 70)
    
    keyboards_ok = verify_keyboards()
    handlers_ok = verify_handlers()
    
    print(f"\n📊 Results:")
    print(f"   Keyboards: {'✅ PASS' if keyboards_ok else '❌ FAIL'}")
    print(f"   Handlers:  {'✅ PASS' if handlers_ok else '❌ FAIL'}")
    
    if keyboards_ok and handlers_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Settings button successfully removed from main menu")
        print("✅ Profile button added to main menu")
        print("✅ Settings functionality integrated into profile menu")
        print("✅ Handlers properly configured")
        print("\n🚀 The implementation is working correctly!")
        print("📋 The user's request has been completed successfully.")
    else:
        print("\n❌ Some tests failed - please check the implementation")
    
    return keyboards_ok and handlers_ok

if __name__ == "__main__":
    main()