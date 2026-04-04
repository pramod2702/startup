"""
FIXED Razorpay Integration - Backend Django Views
Properly handles dynamic pricing without hardcoded values
"""
import json
import razorpay
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)

# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@require_http_methods(["POST"])
@csrf_exempt
def create_razorpay_order_fixed(request):
    """
    FIXED: Create Razorpay order with dynamic amount
    NO HARDCODED VALUES
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        amount = data.get('amount')
        product_name = data.get('product_name', 'Product')
        product_data = data.get('product_data', {})
        
        # === DEBUGGING PRINTS (VERY IMPORTANT) ===
        print("=== BACKEND: CREATE ORDER ===")
        print("Received amount:", amount)
        print("Amount type:", type(amount))
        print("Product name:", product_name)
        print("Product data:", product_data)
        
        # Validate amount
        if not amount or amount <= 0:
            print("ERROR: Invalid amount")
            return JsonResponse({
                'success': False,
                'error': 'Invalid amount provided'
            }, status=400)
        
        # FIXED: Convert properly - DO NOT use int() directly
        amount = float(data["amount"])  # Use float, not int
        print("Amount after float conversion:", amount)
        print("Amount type after conversion:", type(amount))
        
        # FIXED: Convert to paise - multiply only ONCE
        amount_paise = int(amount * 100)
        print("Amount * 100:", amount * 100)
        print("Final amount in paise:", amount_paise)
        print("Expected display amount (₹):", amount_paise / 100)
        
        # Create Razorpay order with dynamic amount
        order_data = {
            'amount': amount_paise,  # Dynamic amount
            'currency': 'INR',
            'receipt': f'receipt_{product_data.get("product_id", "unknown")}_{amount}',
            'notes': {
                'product_name': product_name,
                'original_amount_rupees': str(amount),
                'product_data': json.dumps(product_data)
            }
        }
        
        # Create order in Razorpay
        razorpay_order = client.order.create(data=order_data)
        print("Razorpay order created:", razorpay_order['id'])
        
        # FIXED: Return Razorpay response directly - NO HARDCODING
        response_data = {
            'success': True,
            'order_data': {
                'key': settings.RAZORPAY_KEY_ID,
                'amount': razorpay_order['amount'],  # Use Razorpay amount
                'currency': razorpay_order['currency'],
                'name': 'VICTNOW Luxury Fragrances',
                'description': f'{product_name} - ₹{amount}',
                'order_id': razorpay_order['id'],  # Use Razorpay order_id
                'image': '/static/images/perfume.png',
                'prefill': {
                    'name': '',
                    'email': '',
                    'contact': ''
                },
                'notes': {
                    'product_name': product_name,
                    'original_amount': str(amount)
                }
            }
        }
        
        print("=== BACKEND RESPONSE ===")
        print("Sending amount (paise):", response_data['order_data']['amount'])
        print("Sending order_id:", response_data['order_data']['order_id'])
        print("Should display in Razorpay (₹):", response_data['order_data']['amount'] / 100)
        print("=== END CREATE ORDER ===")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print("ERROR:", str(e))
        logger.error(f"Error creating Razorpay order: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to create payment order: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def verify_razorpay_payment_fixed(request):
    """
    FIXED: Verify Razorpay payment
    """
    try:
        data = json.loads(request.body)
        
        print("=== BACKEND: VERIFY PAYMENT ===")
        print("Payment ID:", data.get('razorpay_payment_id'))
        print("Order ID:", data.get('razorpay_order_id'))
        
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': data.get('razorpay_order_id'),
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_signature': data.get('razorpay_signature')
        }
        
        try:
            client.utility.verify_payment_signature(params_dict)
            print("Payment signature verified successfully")
        except Exception as e:
            print("Payment verification failed:", str(e))
            return JsonResponse({
                'success': False,
                'error': 'Payment verification failed'
            }, status=400)
        
        # Create order in database (simplified for demo)
        order_id = f"ORDER_{data.get('razorpay_payment_id')}"
        
        print("=== END VERIFY PAYMENT ===")
        
        return JsonResponse({
            'success': True,
            'order_id': order_id,
            'redirect_url': '/payment-success/?order_id=' + order_id
        })
        
    except Exception as e:
        print("ERROR:", str(e))
        return JsonResponse({
            'success': False,
            'error': f'Payment verification failed: {str(e)}'
        }, status=500)

def payment_success_fixed(request):
    """Payment success page"""
    order_id = request.GET.get('order_id')
    return render(request, 'fragrances/payment_success.html', {'order_id': order_id})
