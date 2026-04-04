from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile
import json
import random
from datetime import datetime

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def detect_device_and_browser(request):
    """Detect device type and browser from user agent"""
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    # Device detection
    if 'mobile' in user_agent:
        device_type = 'mobile'
    elif 'tablet' in user_agent:
        device_type = 'tablet'
    else:
        device_type = 'desktop'
    
    # Browser detection
    if 'chrome' in user_agent:
        browser = 'Chrome'
    elif 'firefox' in user_agent:
        browser = 'Firefox'
    elif 'safari' in user_agent:
        browser = 'Safari'
    elif 'edge' in user_agent:
        browser = 'Edge'
    elif 'opera' in user_agent:
        browser = 'Opera'
    else:
        browser = 'Unknown'
    
    return device_type, browser

@csrf_exempt
@require_POST
def direct_mobile_login(request):
    """
    Direct mobile login endpoint - authenticates user and stores comprehensive login data
    """
    try:
        data = json.loads(request.body)
        mobile_number = data.get('mobile_number', '').strip()
        country_code = data.get('country_code', '+91')
        full_number = country_code + mobile_number
        
        print(f"Direct mobile login attempt: {full_number}")
        print(f"Mobile number received: '{mobile_number}' (length: {len(mobile_number) if mobile_number else 0})")
        
        if not mobile_number or len(mobile_number) < 10:
            print(f"Invalid mobile number: '{mobile_number}', length: {len(mobile_number) if mobile_number else 0}")
            return JsonResponse({
                'success': False,
                'error': f'Invalid mobile number: {mobile_number} (length: {len(mobile_number) if mobile_number else 0})'
            })
        
        # Find or create user based on mobile number
        user = None
        created = False
        
        # First try to find existing user by phone number in UserProfile
        try:
            profile = UserProfile.objects.get(phone_number=mobile_number)
            user = profile.user
            print(f"Found existing user: {user.username}")
            created = False
        except UserProfile.DoesNotExist:
            # Try to find user by matching the mobile number pattern in username
            username = f"user_{mobile_number[-4:]}"
            try:
                user = User.objects.get(username=username)
                print(f"Found existing user by username: {user.username}")
                created = False
            except User.DoesNotExist:
                # Create new user
                user = User.objects.create(
                    username=username,
                    email=f'{username}@victnow.com',
                    first_name='User',
                    last_name=mobile_number[-4:],
                    is_active=True
                )
                print(f"Created new user: {user.username}")
                created = True
        
        # Create or update user profile with comprehensive login data
        profile, profile_created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'phone_number': mobile_number,
                'country_code': country_code,
                'login_method': 'mobile',
                'is_verified': True
            }
        )
        
        # Capture comprehensive login information
        profile.phone_number = mobile_number
        profile.country_code = country_code
        profile.login_method = 'mobile'
        profile.is_verified = True
        profile.last_login = timezone.now()
        
        # Frontend login tracking data
        profile.login_ip_address = get_client_ip(request)
        profile.login_user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        profile.frontend_session_id = request.session.session_key or f"session_{random.randint(10000, 99999)}"
        
        # Device and browser detection
        device_type, browser = detect_device_and_browser(request)
        profile.login_device_type = device_type
        profile.login_browser = browser
        
        # Update login counters
        profile.login_attempts = getattr(profile, 'login_attempts', 0) + 1
        profile.successful_logins = getattr(profile, 'successful_logins', 0) + 1
        
        # Additional mobile login specific data
        profile.login_location = request.META.get('HTTP_CF_IPCOUNTRY', 'Unknown')  # Cloudflare country detection
        
        profile.save()
        
        # Log in the user using Django's authentication system
        login(request, user)
        
        print(f"Direct login successful for: {user.username}")
        print(f"IP: {profile.login_ip_address}")
        print(f"Device: {profile.login_device_type}")
        print(f"Browser: {profile.login_browser}")
        print(f"Successful logins: {profile.successful_logins}")
        
        return JsonResponse({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'phone_number': profile.phone_number,
                'country_code': profile.country_code,
                'login_method': profile.login_method,
                'is_verified': profile.is_verified,
                'login_count': profile.successful_logins,
                'last_login': profile.last_login.strftime('%Y-%m-%d %H:%M:%S'),
                'device_type': profile.login_device_type,
                'browser': profile.login_browser,
                'ip_address': profile.login_ip_address
            },
            'redirect_url': '/'  # Redirect to home page after login
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        print(f"Error in direct mobile login: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def quick_login_with_phone(request):
    """
    Quick login endpoint for mobile phone authentication
    """
    try:
        data = json.loads(request.body)
        phone_number = data.get('phone_number', '').strip()
        
        if not phone_number:
            return JsonResponse({
                'success': False,
                'error': 'Phone number is required'
            })
        
        # Generate a simple 4-digit OTP for quick login
        otp = str(random.randint(1000, 9999))
        
        # Store OTP in session
        request.session['quick_otp'] = otp
        request.session['quick_phone'] = phone_number
        request.session['otp_generated_time'] = timezone.now().isoformat()
        
        print(f"Quick OTP generated for {phone_number}: {otp}")
        
        return JsonResponse({
            'success': True,
            'message': f'OTP sent to {phone_number[-4:]}****',
            'otp_for_testing': otp,  # Remove this in production
            'expires_in': 300  # 5 minutes
        })
        
    except Exception as e:
        print(f"Error generating quick OTP: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def verify_quick_login(request):
    """
    Verify OTP and complete quick login
    """
    try:
        data = json.loads(request.body)
        entered_otp = data.get('otp', '')
        
        stored_otp = request.session.get('quick_otp')
        phone_number = request.session.get('quick_phone')
        
        if not stored_otp:
            return JsonResponse({'success': False, 'error': 'OTP expired. Please try again'})
        
        if entered_otp == stored_otp:
            # Clear OTP from session
            del request.session['quick_otp']
            del request.session['quick_phone']
            
            # Use the direct mobile login function
            return direct_mobile_login(request)
        else:
            return JsonResponse({'success': False, 'error': 'Invalid OTP'})
            
    except Exception as e:
        print(f"Error verifying quick login: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

def get_login_stats(request):
    """
    Get login statistics for admin dashboard
    """
    try:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Unauthorized'})
        
        profiles = UserProfile.objects.all()
        
        stats = {
            'total_users': profiles.count(),
            'mobile_logins': profiles.filter(login_method='mobile').count(),
            'today_logins': profiles.filter(last_login__date=timezone.now().date()).count(),
            'device_stats': {
                'mobile': profiles.filter(login_device_type='mobile').count(),
                'desktop': profiles.filter(login_device_type='desktop').count(),
                'tablet': profiles.filter(login_device_type='tablet').count()
            },
            'browser_stats': {
                'Chrome': profiles.filter(login_browser='Chrome').count(),
                'Firefox': profiles.filter(login_browser='Firefox').count(),
                'Safari': profiles.filter(login_browser='Safari').count(),
                'Edge': profiles.filter(login_browser='Edge').count(),
                'Other': profiles.filter(login_browser='Unknown').count()
            },
            'recent_logins': []
        }
        
        # Get recent logins
        recent_profiles = profiles.order_by('-last_login')[:10]
        for profile in recent_profiles:
            stats['recent_logins'].append({
                'username': profile.user.username,
                'phone': profile.phone_number,
                'login_time': profile.last_login.strftime('%Y-%m-%d %H:%M:%S'),
                'device': profile.login_device_type,
                'browser': profile.login_browser,
                'ip': profile.login_ip_address
            })
        
        return JsonResponse({'success': True, 'stats': stats})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def complete_user_profile(request):
    """
    Complete user profile with additional details after OTP verification
    """
    try:
        data = json.loads(request.body)
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()
        birth_date = data.get('birth_date', '')
        gender = data.get('gender', '')
        mobile_number = data.get('mobile_number', '').strip()
        country_code = data.get('country_code', '+91')
        
        print(f"Complete profile request for: {mobile_number}")
        print(f"Profile data: {first_name} {last_name}, {email}, {birth_date}, {gender}")
        
        # Validate required fields
        if not first_name or not last_name or not email:
            return JsonResponse({
                'success': False,
                'error': 'First name, last name, and email are required'
            })
        
        # Validate email format
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        import re
        if not re.match(email_regex, email):
            return JsonResponse({
                'success': False,
                'error': 'Invalid email format'
            })
        
        # Find or create user based on mobile number
        user = None
        created = False
        
        # First try to find existing user by phone number in UserProfile
        try:
            profile = UserProfile.objects.get(phone_number=mobile_number)
            user = profile.user
            print(f"Found existing user: {user.username}")
            created = False
        except UserProfile.DoesNotExist:
            # Try to find user by matching the mobile number pattern in username
            username = f"user_{mobile_number[-4:]}"
            try:
                user = User.objects.get(username=username)
                print(f"Found existing user by username: {user.username}")
                created = False
            except User.DoesNotExist:
                # Create new user
                user = User.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True
                )
                print(f"Created new user: {user.username}")
                created = True
        
        # Update user information
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        
        # Create or update user profile with comprehensive data
        profile, profile_created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'phone_number': mobile_number,
                'country_code': country_code,
                'login_method': 'mobile',
                'is_verified': True
            }
        )
        
        # Update profile with new information
        profile.phone_number = mobile_number
        profile.country_code = country_code
        profile.login_method = 'mobile'
        profile.is_verified = True
        profile.last_login = timezone.now()
        
        # Add additional profile fields if they exist in model
        if hasattr(profile, 'birth_date') and birth_date:
            try:
                profile.birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            except ValueError:
                pass  # Invalid date format, skip
        
        if hasattr(profile, 'gender') and gender:
            profile.gender = gender
        
        # Capture comprehensive login information
        profile.login_ip_address = get_client_ip(request)
        profile.login_user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        profile.frontend_session_id = request.session.session_key or f"session_{random.randint(10000, 99999)}"
        
        # Device and browser detection
        device_type, browser = detect_device_and_browser(request)
        profile.login_device_type = device_type
        profile.login_browser = browser
        
        # Update login counters
        profile.login_attempts = getattr(profile, 'login_attempts', 0) + 1
        profile.successful_logins = getattr(profile, 'successful_logins', 0) + 1
        
        # Additional mobile login specific data
        profile.login_location = request.META.get('HTTP_CF_IPCOUNTRY', 'Unknown')
        
        profile.save()
        
        # Log in the user using Django's authentication system
        login(request, user)
        
        print(f"Profile completed successfully for: {user.username}")
        print(f"Updated profile: {profile.phone_number}, {profile.login_method}")
        
        return JsonResponse({
            'success': True,
            'message': 'Profile completed successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'phone_number': profile.phone_number,
                'country_code': profile.country_code,
                'login_method': profile.login_method,
                'is_verified': profile.is_verified,
                'login_count': profile.successful_logins,
                'last_login': profile.last_login.strftime('%Y-%m-%d %H:%M:%S'),
                'device_type': profile.login_device_type,
                'browser': profile.login_browser,
                'ip_address': profile.login_ip_address,
                'birth_date': profile.birth_date.strftime('%Y-%m-%d') if hasattr(profile, 'birth_date') and profile.birth_date else None,
                'gender': getattr(profile, 'gender', None)
            },
            'redirect_url': '/'  # Redirect to home page after profile completion
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        print(f"Error in complete user profile: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})
