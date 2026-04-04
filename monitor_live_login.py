#!/usr/bin/env python
import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blissme_project.settings')
django.setup()

from django.contrib.auth.models import User
from fragrances.models import UserProfile
from django.utils import timezone

print("=== LIVE LOGIN MONITOR ===")
print("Monitoring real-time login information...")
print("Press Ctrl+C to stop monitoring")

try:
    while True:
        # Clear screen for better visibility
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=== REAL-TIME LOGIN INFORMATION ===")
        print(f"Last Updated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Show all users with their current login info
        users = User.objects.select_related('profile').all()
        
        print("┌─────────────────────────────────────────────────────────────────────────────────────────────────┐")
        print("│ USER INFO                    │ PHONE      │ METHOD   │ VERIFIED │ LAST LOGIN           │")
        print("├─────────────────────────────────────────────────────────────────────────────────────────────────┤")
        
        for user in users:
            try:
                profile = user.profile
                name = f"{user.first_name} {user.last_name}".strip()
                if not name:
                    name = user.username
                
                phone = profile.phone_number or "N/A"
                method = profile.login_method.upper()[:7]
                verified = "✅ YES" if profile.is_verified else "❌ NO"
                
                if profile.last_login:
                    login_time = profile.last_login.strftime('%H:%M:%S')
                    login_date = profile.last_login.strftime('%m-%d')
                else:
                    login_time = "NEVER"
                    login_date = "--"
                
                print(f"│ {name:<27} │ {phone:<10} │ {method:<8} │ {verified:<8} │ {login_date} {login_time:<8} │")
                
            except UserProfile.DoesNotExist:
                print(f"│ {user.username:<27} │ N/A        │ N/A      │ N/A      │ NO PROFILE          │")
        
        print("└─────────────────────────────────────────────────────────────────────────────────────────────────┘")
        print()
        print("🔄 Real-time login tracking is ACTIVE")
        print("📱 When users log in via mobile OTP, this updates instantly")
        print("🌐 When users log in via social auth, this updates instantly")
        print("🔐 When users log in via admin, this updates instantly")
        print()
        print("💡 To test: Login with phone 9876543210 (Pramod Mahankal)")
        print("💡 Admin Panel: http://127.0.0.1:8000/admin/fragrances/userprofile/")
        print()
        print("Monitoring... (updates every 5 seconds)")
        
        # Wait before next update
        time.sleep(5)
        
except KeyboardInterrupt:
    print("\n\n🛑 Monitoring stopped by user")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
