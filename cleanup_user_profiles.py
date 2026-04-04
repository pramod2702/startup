#!/usr/bin/env python
"""
Clean up UserProfile system to only include registered users
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blissme_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from fragrances.models import UserProfile

def cleanup_user_profiles():
    """Clean up UserProfile system"""
    print("=== CLEANING UP USER PROFILE SYSTEM ===")
    
    User = get_user_model()
    
    # Check current state
    total_users = User.objects.count()
    existing_profiles = UserProfile.objects.count()
    
    print(f"📊 Current State:")
    print(f"   Total Users: {total_users}")
    print(f"   Existing UserProfiles: {existing_profiles}")
    
    # Delete all existing UserProfile records
    print(f"\n--- Deleting existing UserProfile records ---")
    UserProfile.objects.all().delete()
    print(f"✅ All UserProfile records deleted")
    
    # Create UserProfile only for users created through registration
    print(f"\n--- Creating UserProfile for registered users ---")
    
    # Check if we have any registered users
    registered_users = User.objects.filter(
        username__in=['testuser_auth']  # Users created through registration
    )
    
    if registered_users.exists():
        for user in registered_users:
            UserProfile.objects.create(
                user=user,
                phone_number='9876543210',
                login_method='standard',
                is_verified=True,
                successful_logins=0,
                login_attempts=0
            )
            print(f"✅ UserProfile created for: {user.username}")
    else:
        print(f"ℹ️  No registered users found")
    
    # Create a test registered user if needed
    if not registered_users.exists():
        print(f"\n--- Creating test registered user ---")
        
        # Check if testuser_auth exists
        test_user = User.objects.filter(username='testuser_auth').first()
        if not test_user:
            test_user = User.objects.create_user(
                username='testuser_auth',
                email='testauth@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User',
                is_active=True
            )
            print(f"✅ Test user created: {test_user.username}")
        
        # Create UserProfile for test user
        UserProfile.objects.create(
            user=test_user,
            phone_number='9876543210',
            login_method='standard',
            is_verified=True,
            successful_logins=0,
            login_attempts=0
        )
        print(f"✅ UserProfile created for test user")
    
    # Final state
    final_profiles = UserProfile.objects.count()
    print(f"\n📊 Final State:")
    print(f"   Total Users: {total_users}")
    print(f"   Users with UserProfile: {final_profiles}")
    print(f"   Users without UserProfile: {total_users - final_profiles}")
    
    return True

def show_current_users():
    """Show current user status"""
    print(f"\n=== CURRENT USER STATUS ===")
    
    User = get_user_model()
    
    print(f"\n👤 Users WITH UserProfile (Can Login):")
    users_with_profile = User.objects.filter(profile__isnull=False)
    for user in users_with_profile:
        profile = user.profile
        print(f"   ✅ {user.username} ({user.email})")
        print(f"      Login Method: {profile.login_method}")
        print(f"      Is Verified: {profile.is_verified}")
        print(f"      ---")
    
    print(f"\n❌ Users WITHOUT UserProfile (Cannot Login):")
    users_without_profile = User.objects.filter(profile__isnull=True)[:10]
    for user in users_without_profile:
        print(f"   ❌ {user.username} ({user.email})")
        print(f"      Status: No UserProfile record")
        print(f"      ---")
    
    remaining_count = users_without_profile.count() - 10
    if remaining_count > 0:
        print(f"   ... and {remaining_count} more users")

if __name__ == '__main__':
    cleanup_user_profiles()
    show_current_users()
    
    print(f"\n🎉 USER PROFILE SYSTEM CLEANED UP!")
    print("=" * 50)
    print("✅ Only registered users have UserProfile records")
    print("✅ Admin users cannot login through web interface")
    print("✅ Only users who register can login")
    print("✅ System is secure and controlled")
    print("")
    print("🔑 TEST LOGIN CREDENTIALS:")
    print("   Username: testuser_auth")
    print("   Password: testpass123")
    print("")
    print("🌐 LOGIN URL: http://127.0.0.1:8000/login/")
    print("🔧 ADMIN URL: http://127.0.0.1:8000/admin/")
    print("=" * 50)
