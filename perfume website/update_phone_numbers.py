#!/usr/bin/env python
"""
Update phone numbers for existing profiles
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

def update_phone_numbers():
    """Update phone numbers for existing profiles"""
    print("=== UPDATING PHONE NUMBERS ===")
    
    User = get_user_model()
    
    # Get profiles without phone numbers
    profiles_without_phone = UserProfile.objects.filter(phone_number__isnull=True)
    
    print(f"Found {profiles_without_phone.count()} profiles without phone numbers")
    
    for profile in profiles_without_phone:
        profile.phone_number = '987654321000'
        profile.save()
        print(f"✅ Updated phone number for: {profile.user.username}")
    
    # Verify the update
    updated_profiles = UserProfile.objects.exclude(phone_number__isnull=True)
    print(f"\n✅ Total profiles with phone numbers: {updated_profiles.count()}")
    
    return True

if __name__ == '__main__':
    update_phone_numbers()
