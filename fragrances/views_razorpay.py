"""
Dynamic Razorpay Payment Integration
Backend Django Views
"""
import json
import razorpay
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Product, Order, TrialPack, UserProfile
import logging

logger = logging.getLogger(__name__)

# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@require_http_methods(["POST"])
@csrf_exempt
def create_razorpay_order(request):
    """
    Create Razorpay order with dynamic amount
    Accepts amount from frontend and returns order details
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        amount = data.get('amount')
        product_name = data.get('product_name', 'Product')
        product_data = data.get('product_data', {})
        
        # Debug logging
        print(f"=== BACKEND: CREATE ORDER ===")
        print(f"Received amount (₹): {amount}")
        print(f"Amount type: {type(amount)}")
        print(f"Product name: {product_name}")
        print(f"Product data: {product_data}")
        
        # Validate amount
        if not amount or amount <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Invalid amount provided'
            }, status=400)
        
        # Convert to float for consistency (handles decimal properly)
        amount = float(amount)
        print(f"Amount after float conversion: {amount}")
        print(f"Amount type after conversion: {type(amount)}")
        
        # Convert to paise (Razorpay uses smallest currency unit)
        # Multiply by 100 only once and convert to int
        amount_in_paise = int(amount * 100)
        print(f"Amount * 100: {amount * 100}")
        print(f"Final amount in paise: {amount_in_paise}")
        print(f"Expected display amount (₹): {amount_in_paise / 100}")
        
        # Create Razorpay order
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': f'receipt_{product_data.get("product_id", "unknown")}_{int(amount)}',
            'notes': {
                'product_name': product_name,
                'product_data': json.dumps(product_data),
                'source': 'django_frontend'
            }
        }
        
        # Create order in Razorpay
        razorpay_order = client.order.create(data=order_data)
        print(f"Razorpay order created: {razorpay_order['id']}")
        
        # Prepare response for frontend
        response_data = {
            'success': True,
            'order_data': {
                'key': settings.RAZORPAY_KEY_ID,
                'amount': razorpay_order['amount'],  # Amount in paise
                'currency': razorpay_order['currency'],
                'name': 'VICTNOW Luxury Fragrances',
                'description': f'{product_name} - ₹{amount}',
                'order_id': razorpay_order['id'],
                'image': '/static/images/perfume.png',
                'prefill': {
                    'name': '',
                    'email': '',
                    'contact': ''
                },
                'notes': {
                    'product_name': product_name,
                    'original_amount_rupees': str(amount),
                    'original_amount_float': float(amount),
                    **product_data
                }
            }
        }
        
        print(f"=== BACKEND RESPONSE ===")
        print(f"Sending to frontend amount (paise): {response_data['order_data']['amount']}")
        print(f"Should display in Razorpay (₹): {response_data['order_data']['amount'] / 100}")
        print(f"Original amount was (₹): {amount}")
        print(f"=== END CREATE ORDER ===")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error creating Razorpay order: {str(e)}")
        print(f"ERROR: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to create payment order: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def verify_razorpay_payment(request):
    """
    Verify Razorpay payment and create order in database
    """
    try:
        data = json.loads(request.body)
        
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        order_data = data.get('order_data', {})
        
        print(f"=== BACKEND: VERIFY PAYMENT ===")
        print(f"Payment ID: {razorpay_payment_id}")
        print(f"Order ID: {razorpay_order_id}")
        print(f"Order data: {order_data}")
        
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            client.utility.verify_payment_signature(params_dict)
            print("Payment signature verified successfully")
        except Exception as e:
            print(f"Payment verification failed: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Payment verification failed'
            }, status=400)
        
        # Extract product information
        notes = order_data.get('notes', {})
        product_name = notes.get('product_name', 'Product')
        original_amount = float(notes.get('original_amount_rupees', 0))
        product_data = json.loads(notes.get('product_data', '{}'))
        
        # Create order in database based on product type
        if 'trial_pack' in product_name.lower() or product_data.get('type') == 'trial_pack':
            # Create trial pack order
            order = create_trial_pack_order(data, order_data, original_amount)
        elif 'cart' in product_name.lower() or 'items' in product_data:
            # Create cart order
            order = create_cart_order(data, order_data, original_amount, product_data)
        else:
            # Create single product order
            order = create_single_product_order(data, order_data, original_amount, product_data)
        
        print(f"Order created in database: {order.id if order else 'Failed'}")
        print(f"=== END VERIFY PAYMENT ===")
        
        return JsonResponse({
            'success': True,
            'order_id': order.id if order else None,
            'redirect_url': '/payment-success/?order_id=' + str(order.id if order else ''),
            'message': 'Payment successful and order created'
        })
        
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        print(f"ERROR: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Payment verification failed: {str(e)}'
        }, status=500)

def create_trial_pack_order(payment_data, order_data, amount):
    """Create trial pack order after successful payment"""
    try:
        notes = order_data.get('notes', {})
        product_data = json.loads(notes.get('product_data', '{}'))
        
        order = TrialPack.objects.create(
            name=product_data.get('name', 'Customer'),
            email=product_data.get('email', ''),
            phone=product_data.get('phone', ''),
            address=product_data.get('address', ''),
            city=product_data.get('city', ''),
            trial_pack_name='VICTNOW Trial Pack',
            trial_pack_description='VICTNOW MUSE, VICTNOW NEXUS, VICTNOW FORGE - 5ML each',
            amount=amount,
            payment_method='razorpay',
            payment_status='completed',
            transaction_id=payment_data.get('razorpay_payment_id'),
            razorpay_order_id=payment_data.get('razorpay_order_id'),
            razorpay_payment_id=payment_data.get('razorpay_payment_id'),
            order_status='confirmed',
            admin_notes=f'Order created via Razorpay - Payment ID: {payment_data.get("razorpay_payment_id")}'
        )
        return order
    except Exception as e:
        print(f"Error creating trial pack order: {str(e)}")
        return None

def create_single_product_order(payment_data, order_data, amount, product_data):
    """Create single product order after successful payment"""
    try:
        product_id = product_data.get('product_id')
        quantity = product_data.get('quantity', 1)
        
        if not product_id:
            raise Exception("Product ID not found")
        
        product = Product.objects.get(id=product_id)
        
        order = Order.objects.create(
            first_name=product_data.get('name', 'Customer').split()[0],
            last_name=' '.join(product_data.get('name', 'Customer').split()[1:]) if len(product_data.get('name', '').split()) > 1 else '',
            email=product_data.get('email', ''),
            phone=product_data.get('phone', ''),
            address=product_data.get('address', ''),
            city=product_data.get('city', ''),
            quantity=quantity,
            product_price=product.price,
            shipping_cost=500.00,
            total_amount=amount,
            payment_method='razorpay',
            payment_status='completed',
            payment_id=payment_data.get('razorpay_payment_id'),
            product_id=product_id
        )
        return order
    except Exception as e:
        print(f"Error creating product order: {str(e)}")
        return None

def create_cart_order(payment_data, order_data, amount, product_data):
    """Create cart order after successful payment"""
    try:
        items = product_data.get('items', [])
        if not items:
            raise Exception("No items found in cart")
        
        # Create orders for each item in cart
        orders = []
        for item in items:
            product = Product.objects.get(id=item['product_id'])
            order = Order.objects.create(
                first_name=product_data.get('name', 'Customer').split()[0],
                last_name=' '.join(product_data.get('name', 'Customer').split()[1:]) if len(product_data.get('name', '').split()) > 1 else '',
                email=product_data.get('email', ''),
                phone=product_data.get('phone', ''),
                address=product_data.get('address', ''),
                city=product_data.get('city', ''),
                quantity=item['quantity'],
                product_price=product.price,
                shipping_cost=500.00,
                total_amount=item['subtotal'] + 500.00,
                payment_method='razorpay',
                payment_status='completed',
                payment_id=payment_data.get('razorpay_payment_id'),
                product_id=product.id
            )
            orders.append(order)
        
        return orders[0] if orders else None  # Return first order as reference
    except Exception as e:
        print(f"Error creating cart order: {str(e)}")
        return None

def payment_success(request):
    """Payment success page"""
    order_id = request.GET.get('order_id')
    return render(request, 'fragrances/payment_success.html', {'order_id': order_id})
