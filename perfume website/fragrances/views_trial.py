from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from .models import TrialPack
import json
import razorpay
import hashlib
import hmac
import time

@method_decorator(csrf_exempt, name='dispatch')
class CreateTrialPackView(View):
    def post(self, request):
        try:
            # Get form data
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            
            # Optional fields
            address = request.POST.get('address', '').strip()
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()
            postal_code = request.POST.get('postal_code', '').strip()
            
            # Payment and order details
            payment_method = request.POST.get('payment_method', 'upi')
            payment_status = request.POST.get('payment_status', 'completed')
            order_status = request.POST.get('order_status', 'confirmed')
            trial_pack_name = request.POST.get('trial_pack_name', 'VICTNOW Trial Pack')
            trial_pack_description = request.POST.get('trial_pack_description', 'VICTNOW MUSE, VICTNOW NEXUS, VICTNOW FORGE - 5ML each')
            amount = request.POST.get('amount', '29.99')
            
            # Validation
            if not name or not email or not phone:
                return JsonResponse({
                    'success': False,
                    'error': 'Name, email, and phone are required fields.'
                })
            
            # Create trial pack order
            trial_pack = TrialPack.objects.create(
                name=name,
                email=email,
                phone=phone,
                address=address,
                city=city,
                state=state,
                postal_code=postal_code,
                payment_method=payment_method,
                payment_status=payment_status,
                order_status=order_status,
                trial_pack_name=trial_pack_name,
                trial_pack_description=trial_pack_description,
                amount=amount,
                admin_notes='Order created from frontend trial pack modal'
            )
            
            return JsonResponse({
                'success': True,
                'order_id': trial_pack.id,
                'customer_name': trial_pack.name,
                'email': trial_pack.email,
                'phone': trial_pack.phone,
                'amount': str(trial_pack.amount),
                'payment_method': trial_pack.payment_method,
                'order_status': trial_pack.order_status,
                'message': 'Trial pack order created successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    def get(self, request):
        return JsonResponse({
            'success': False,
            'error': 'Only POST method is allowed'
        })


# Alternative function-based view
@csrf_exempt
@require_http_methods(["POST"])
def create_trial_pack(request):
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # Optional fields
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        
        # Payment and order details
        payment_method = request.POST.get('payment_method', 'upi')
        payment_status = request.POST.get('payment_status', 'completed')
        order_status = request.POST.get('order_status', 'confirmed')
        trial_pack_name = request.POST.get('trial_pack_name', 'VICTNOW Trial Pack')
        trial_pack_description = request.POST.get('trial_pack_description', 'VICTNOW MUSE, VICTNOW NEXUS, VICTNOW FORGE - 5ML each')
        amount = request.POST.get('amount', '29.99')
        
        # Validation
        if not name or not email or not phone:
            return JsonResponse({
                'success': False,
                'error': 'Name, email, and phone are required fields.'
            })
        
        # Create trial pack order
        trial_pack = TrialPack.objects.create(
            name=name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            state=state,
            postal_code=postal_code,
            payment_method=payment_method,
            payment_status=payment_status,
            order_status=order_status,
            trial_pack_name=trial_pack_name,
            trial_pack_description=trial_pack_description,
            amount=amount,
            admin_notes='Order created from frontend trial pack modal'
        )
        
        return JsonResponse({
            'success': True,
            'order_id': trial_pack.id,
            'customer_name': trial_pack.name,
            'email': trial_pack.email,
            'phone': trial_pack.phone,
            'amount': str(trial_pack.amount),
            'payment_method': trial_pack.payment_method,
            'order_status': trial_pack.order_status,
            'message': 'Trial pack order created successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
def update_trial_pack_payment(request):
    """Update trial pack order with payment information"""
    try:
        import json
        from django.utils import timezone
        
        # Get payment data
        data = json.loads(request.body)
        order_id = data.get('order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        payment_status = data.get('payment_status')
        order_status = data.get('order_status')
        
        if not order_id:
            return JsonResponse({
                'success': False,
                'error': 'Order ID is required'
            })
        
        # Find the trial pack order
        try:
            trial_pack = TrialPack.objects.get(id=order_id)
        except TrialPack.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Order not found'
            })
        
        # Update payment information
        if razorpay_payment_id:
            trial_pack.razorpay_payment_id = razorpay_payment_id
        
        if payment_status:
            trial_pack.payment_status = payment_status
        
        if order_status:
            trial_pack.order_status = order_status
        
        trial_pack.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Payment status updated successfully',
            'order_id': trial_pack.id,
            'payment_status': trial_pack.payment_status,
            'order_status': trial_pack.order_status
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def trial_pack_orders_list(request):
    """API endpoint to get trial pack orders (for admin dashboard)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    orders = TrialPack.objects.all().order_by('-created_at')
    
    orders_data = []
    for order in orders:
        orders_data.append({
            'id': order.id,
            'name': order.name,
            'email': order.email,
            'phone': order.phone,
            'amount': str(order.amount),
            'payment_status': order.payment_status,
            'order_status': order.order_status,
            'payment_method': order.payment_method,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'admin_link': f'/admin/fragrances/trialpack/{order.id}/change/'
        })
    
    return JsonResponse({
        'success': True,
        'orders': orders_data,
        'total_count': len(orders_data)
    })
