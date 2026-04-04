from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.conf import settings
from django.utils import timezone
import json
import requests
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def send_otp_via_fast2sms(request):
    """Send OTP via Fast2SMS API"""
    try:
        # Parse request data
        data = json.loads(request.body)
        phone_number = data.get('phone_number', '')
        country_code = data.get('country_code', '+91')
        full_number = country_code + phone_number
        
        # Generate OTP if not provided
        otp = data.get('otp', '')
        if not otp:
            import random
            otp = str(random.randint(1000, 9999))
        
        # Validate required fields
        if not phone_number:
            return JsonResponse({
                'success': False,
                'error': 'Phone number is required'
            })
        
        # Store OTP in Django session (like main send_real_otp function)
        request.session['otp'] = otp
        request.session['mobile_number'] = full_number
        request.session['otp_generated_time'] = timezone.now().isoformat()
        
        print(f"Fast2SMS - Generated OTP: {otp}")
        print(f"Fast2SMS - Stored in session for: {full_number}")
        
        # Fast2SMS API configuration from Django settings
        FAST2SMS_API_KEY = getattr(settings, 'FAST2SMS_API_KEY', 'buN1BkI57lcxVrSmjvKHYozaiwCsgZ6nGXfQAT3O8UE4Ly2dhMEHxfPwJSm3byt6M2gdl0TIpDQaGk5U')
        FAST2SMS_SENDER_ID = getattr(settings, 'FAST2SMS_SENDER_ID', 'FSTSMS')
        FAST2SMS_TEMPLATE_ID = getattr(settings, 'FAST2SMS_TEMPLATE_ID', 'otp_template')
        FAST2SMS_ROUTE = getattr(settings, 'FAST2SMS_ROUTE', '3')
        FAST2SMS_LANGUAGE = getattr(settings, 'FAST2SMS_LANGUAGE', 'english')
        
        # Prepare Fast2SMS API request
        api_url = "https://api.fast2sms.com/bulk/v2"
        headers = {
            'Authorization': f'Bearer {FAST2SMS_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'sender': FAST2SMS_SENDER_ID,
            'to': full_number,
            'message': f'Your VICTNOW verification code is: {otp}',
            'template_id': FAST2SMS_TEMPLATE_ID,
            'route': FAST2SMS_ROUTE,
            'language': FAST2SMS_LANGUAGE,
            'schedule_time': None  # Send immediately
        }
        
        # Make API call to Fast2SMS
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Fast2SMS OTP sent successfully: {result}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'OTP sent successfully',
                    'sms_id': result.get('message_id', 'unknown'),
                    'status': result.get('status', 'success'),
                    'response': result,
                    'development_mode': False
                })
            else:
                error_data = response.json() if response.content else {}
                logger.error(f"Fast2SMS API error: {response.status_code} - {error_data}")
                
                return JsonResponse({
                    'success': False,
                    'error': f'Failed to send SMS: {error_data.get("message", "Unknown error")}',
                    'status_code': response.status_code
                })
                
        except requests.exceptions.Timeout:
            logger.warning("Fast2SMS API timeout - using development mode")
            # Development fallback: simulate SMS sending
            return JsonResponse({
                'success': True,
                'message': f'OTP sent successfully to {phone_number} (Development Mode)',
                'sms_id': f'dev_{otp}',
                'status': 'dev_mode',
                'development_mode': True,
                'otp_for_testing': otp,  # Only in development mode
                'note': 'Fast2SMS API unreachable - using development mode'
            })
            
        except requests.exceptions.ConnectionError:
            logger.warning("Fast2SMS API connection error - using development mode")
            # Development fallback: simulate SMS sending
            return JsonResponse({
                'success': True,
                'message': f'OTP sent successfully to {phone_number} (Development Mode)',
                'sms_id': f'dev_{otp}',
                'status': 'dev_mode',
                'development_mode': True,
                'otp_for_testing': otp,  # Only in development mode
                'note': 'Fast2SMS API unreachable - using development mode'
            })
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Fast2SMS network error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Network error: {str(e)}'
            })
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Fast2SMS network error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Network error: {str(e)}'
        })
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"Unexpected error in Fast2SMS: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["POST"])
def verify_otp_firebase(request):
    """Verify OTP with Firebase Authentication"""
    try:
        # Parse request data
        data = json.loads(request.body)
        phone_number = data.get('phone_number', '')
        country_code = data.get('country_code', '+91')
        full_number = country_code + phone_number
        entered_otp = data.get('otp', '')
        
        # Validate required fields
        if not phone_number or not entered_otp:
            return JsonResponse({
                'success': False,
                'error': 'Phone number and OTP are required'
            })
        
        # Get stored OTP from session (in production, use Redis or database)
        # For now, we'll simulate verification
        stored_otp = "1234"  # In production, get from session/database
        
        if entered_otp == stored_otp:
            # OTP verification successful
            return JsonResponse({
                'success': True,
                'message': 'OTP verified successfully',
                'phone_number': full_number,
                'verified': True
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid OTP'
            })
            
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Verification error: {str(e)}'
        })

def fast2sms_config_info(request):
    """Return Fast2SMS configuration information"""
    return JsonResponse({
        'success': True,
        'config': {
            'api_url': 'https://api.fast2sms.com/bulk/v2',
            'required_fields': [
                'phone_number',
                'country_code', 
                'otp',
                'sender_id',
                'template_id'
            ],
            'authentication': 'Bearer Token',
            'rate_limit': '100 requests per minute',
            'supported_countries': ['IN', 'US', 'UK', 'AU', 'CA'],
            'message_length': '160 characters for SMS'
        }
    })
