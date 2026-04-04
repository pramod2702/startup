#!/usr/bin/env python
"""
Debug admin dashboard template content
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blissme_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def debug_dashboard_content():
    """Debug what's actually being served in the dashboard"""
    print("=== Debug Admin Dashboard Content ===")
    
    # Create admin user
    User = get_user_model()
    admin_user, created = User.objects.get_or_create(
        username='debugadmin',
        defaults={
            'email': 'debugadmin@example.com',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
    
    # Test with client
    client = Client()
    login_success = client.login(username='debugadmin', password='admin123')
    
    if login_success:
        print("✅ Admin login successful")
        
        # Get dashboard content
        response = client.get('/admin/dashboard/')
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            print(f"📄 Dashboard content length: {len(content)} characters")
            
            # Check key elements
            checks = [
                ('bulk-orders', 'Bulk orders stat element'),
                ('animateValue', 'JavaScript animation function'),
                ('loadAdminStats', 'Admin stats loading function'),
                ('admin/api/stats/', 'API endpoint call'),
                ('Bulk Orders', 'Bulk Orders text'),
                ('stat-number', 'Stat number class'),
                ('loading', 'Loading indicator'),
            ]
            
            print("\n--- Element Check ---")
            for element, description in checks:
                if element in content:
                    print(f"✅ {description}: FOUND")
                else:
                    print(f"❌ {description}: NOT FOUND")
            
            # Look for the specific bulk orders stat card
            print("\n--- Bulk Orders Stat Card Check ---")
            if 'id="bulk-orders"' in content:
                print("✅ Bulk orders element with correct ID found")
                
                # Extract the surrounding HTML
                start_idx = content.find('id="bulk-orders"')
                if start_idx != -1:
                    # Get some context around the element
                    context_start = max(0, start_idx - 200)
                    context_end = min(len(content), start_idx + 200)
                    context = content[context_start:context_end]
                    print(f"Context around bulk-orders element:")
                    print(f"   {context}")
            else:
                print("❌ Bulk orders element with correct ID NOT found")
            
            # Check if it's using the right template
            print("\n--- Template Check ---")
            if 'admin-panel-header' in content:
                print("✅ Using custom admin dashboard template")
            else:
                print("❌ NOT using custom admin dashboard template")
                print("   Might be using default Django admin template")
            
            # Check JavaScript section
            print("\n--- JavaScript Section Check ---")
            script_start = content.find('<script>')
            script_end = content.find('</script>', script_start) + 9
            
            if script_start != -1 and script_end != -1:
                script_content = content[script_start:script_end]
                print(f"JavaScript section found ({len(script_content)} characters)")
                
                if 'animateValue' in script_content:
                    print("✅ animateValue function found in JavaScript")
                else:
                    print("❌ animateValue function NOT found in JavaScript")
                
                if 'bulk-orders' in script_content:
                    print("✅ bulk-orders referenced in JavaScript")
                else:
                    print("❌ bulk-orders NOT referenced in JavaScript")
            else:
                print("❌ No JavaScript section found")
                
        else:
            print(f"❌ Dashboard failed with status: {response.status_code}")
            
    else:
        print("❌ Admin login failed")
    
    print("\n=== Direct Access Instructions ===")
    print("If bulk orders are not showing in dashboard:")
    print("1. Go directly to: http://localhost:8000/admin/fragrances/corporateorder/")
    print("2. This will show ALL bulk orders in the standard admin interface")
    print("3. Look for 'Fragrances' section in main admin: http://localhost:8000/admin/")
    print("4. Click on 'Corporate orders' to see the list")

if __name__ == '__main__':
    debug_dashboard_content()
