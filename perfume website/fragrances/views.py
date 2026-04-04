from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.utils import timezone
from django.contrib.auth import login, authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
import json
from .models import Product, Testimonial, BlogPost, ContactMessage, Newsletter, Order, UserProfile, CorporateOrder, TrialPack, UserActivity, Cart

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def home(request):
    """Serve the main index.html page with signature products"""
    products = Product.objects.all().order_by('-created_at')
    context = {'products': products}
    return render(request, 'index.html', context)

def collection(request):
    products = Product.objects.all().order_by('-created_at')
    context = {'products': products}
    return render(request, 'fragrances/collection.html', context)

@login_required
@never_cache
def cart(request):
    """Render the shopping cart page with user-specific items"""
    user = request.user
    
    # Get user's cart items from database
    cart_items = Cart.get_user_cart(user)
    cart_count = Cart.get_cart_count(user)
    cart_total = Cart.get_cart_total(user)
    
    # Log cart activity
    if cart_items.exists():
        UserActivity.log_activity(
            user=user,
            activity_type='cart_updated',
            description=f'Viewed cart with {cart_count} items, total: ₹{cart_total}',
            request=request
        )
    
    # Convert cart items to JSON format for JavaScript (same as order summary)
    cart_data = []
    for item in cart_items:
        item_data = {
            'id': item.product.id,
            'name': item.product.name,
            'price': float(item.product.price),
            'quantity': item.quantity,
            'image': item.product.image.url if item.product.image else '/static/images/perfume.png',
            'subtotal': float(item.get_total_price())
        }
        cart_data.append(item_data)
    
    context = {
        'cart_items': cart_items,
        'cart_count': cart_count,
        'cart_total': cart_total,
        'cart_data_json': json.dumps(cart_data),  # Same format as order summary
        'debug_user_id': user.id,
        'debug_username': user.username,
    }
    return render(request, 'fragrances/cart.html', context)

@never_cache
def cart_view(request):
    """Cart view without authentication - uses localStorage"""
    # Return empty cart data - will be populated by JavaScript from localStorage
    cart_data = []
    
    context = {
        'cart_items': [],
        'cart_count': 0,
        'cart_total': 0,
        'cart_data_json': json.dumps(cart_data),
    }
    return render(request, 'fragrances/cart.html', context)

def cart_checkout(request):
    """Render the checkout page for cart items"""
    return render(request, 'fragrances/cart_checkout.html')

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.exclude(id=product_id)[:3]
    
    if request.method == 'POST':
        quantity = request.POST.get('quantity', 1)
        return redirect('checkout', product_id=product.id, quantity=quantity)
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'fragrances/product_detail.html', context)

def customer_details(request):
    """Display customer details form for checkout"""
    context = {
        'product_name': 'Order Items',
        'product_price': '0.00',
    }
    
    return render(request, 'fragrances/customer_details.html', context)

def checkout(request, product_id=None, quantity=1):
    # Handle cart checkout (no product_id) or single product checkout
    if product_id:
        # Single product checkout
        product = get_object_or_404(Product, id=product_id)
        cart_items = [{
            'product': product,
            'quantity': quantity,
            'subtotal': product.price * quantity
        }]
        total_amount = product.price * quantity
    else:
        # Cart checkout - get items from session
        cart = request.session.get('cart', {})
        cart_items = []
        total_amount = 0
        
        for item_id, item_data in cart.items():
            try:
                product = Product.objects.get(id=item_id)
                item_total = product.price * item_data['quantity']
                cart_items.append({
                    'product': product,
                    'quantity': item_data['quantity'],
                    'subtotal': item_total
                })
                total_amount += item_total
            except Product.DoesNotExist:
                continue
    
    shipping = 10 if total_amount > 0 else 0
    tax = total_amount * 0.18  # 18% GST
    final_total = total_amount + shipping + tax
    
    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'shipping': shipping,
        'tax': tax,
        'final_total': final_total,
        'product': cart_items[0]['product'] if cart_items else None,
        'quantity': cart_items[0]['quantity'] if cart_items else 1,
    }
    
    return render(request, 'fragrances/checkout.html', context)

def login(request):
    """Render login page with mobile number and OTP authentication"""
    return render(request, 'fragrances/login.html')

@csrf_exempt
def logout_view(request):
    """Handle user logout"""
    print(f"Logout view called with method: {request.method}")
    if request.method == 'POST':
        # Log logout activity if user is logged in
        if request.user.is_authenticated:
            # Clear user's cart before logout
            Cart.clear_user_cart(request.user)
            
            UserActivity.log_activity(
                user=request.user,
                activity_type='logout',
                description='User logged out (cart cleared)',
                request=request
            )
        
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return JsonResponse({
            'success': True, 
            'message': 'Logged out successfully',
            'force_refresh': True,
            'redirect_url': '/',
            'timestamp': timezone.now().timestamp()
        })
    return redirect('home')

@login_required
@never_cache
def fixed_razorpay_test(request):
    """Test page for the fixed Razorpay integration"""
    return render(request, 'fragrances/fixed_razorpay_test.html')

@login_required
@never_cache
def decimal_price_demo(request):
    """Demo page for testing decimal price handling in Razorpay"""
    return render(request, 'fragrances/decimal_price_demo.html')

@login_required
@never_cache
def dynamic_payment_demo(request):
    """Demo page for testing dynamic Razorpay payments"""
    return render(request, 'fragrances/dynamic_payment_demo.html')

@login_required
@never_cache
def user_dashboard(request):
    user = request.user
    
    # Debug: Print user information
    print(f"DEBUG: Dashboard accessed by user: {user.username} (ID: {user.id})")
    
    # Get user's profile
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    # Get user's orders with different types
    regular_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    trial_packs = TrialPack.objects.filter(user=user).order_by('-created_at')[:5]
    corporate_orders = CorporateOrder.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get user's recent activities
    recent_activities = UserActivity.objects.filter(user=user).order_by('-created_at')[:15]
    
    # Calculate statistics
    total_orders = Order.objects.filter(user=user).count()
    total_trial_packs = TrialPack.objects.filter(user=user).count()
    total_corporate_orders = CorporateOrder.objects.filter(user=user).count()
    total_spent = sum(order.total_amount for order in Order.objects.filter(user=user, payment_status='completed'))
    
    # Get login statistics
    successful_logins = profile.successful_logins
    last_login = profile.last_login
    
    # Debug: Print statistics
    print(f"DEBUG: User stats - Orders: {total_orders}, Trial Packs: {total_trial_packs}, Activities: {recent_activities.count()}")
    
    context = {
        'profile': profile,
        'regular_orders': regular_orders,
        'trial_packs': trial_packs,
        'corporate_orders': corporate_orders,
        'recent_activities': recent_activities,
        'total_orders': total_orders,
        'total_trial_packs': total_trial_packs,
        'total_corporate_orders': total_corporate_orders,
        'total_spent': total_spent,
        'successful_logins': successful_logins,
        'last_login': last_login,
        # Debug information
        'debug_user_id': user.id,
        'debug_username': user.username,
    }
    return render(request, 'fragrances/user_dashboard.html', context)

@login_required
@never_cache
def orders(request):
    """Render the orders page showing logged-in user's order history"""
    user = request.user
    
    # Debug: Print user information
    print(f"DEBUG: Orders page accessed by user: {user.username} (ID: {user.id})")
    
    # Get user's orders
    user_orders = Order.objects.filter(user=user).order_by('-created_at')
    user_trial_packs = TrialPack.objects.filter(user=user).order_by('-created_at')
    user_corporate_orders = CorporateOrder.objects.filter(user=user).order_by('-created_at')
    
    # Get user's recent activities
    recent_activities = UserActivity.objects.filter(user=user).order_by('-created_at')[:10]
    
    # Calculate statistics
    pending_orders = user_orders.filter(order_status='pending').count()
    processing_orders = user_orders.filter(order_status='processing').count()
    delivered_orders = user_orders.filter(order_status='delivered').count()
    cancelled_orders = user_orders.filter(order_status='cancelled').count()
    
    # Debug: Print counts
    print(f"DEBUG: User orders count: {user_orders.count()}, Trial packs: {user_trial_packs.count()}, Activities: {recent_activities.count()}")
    
    context = {
        'orders': user_orders,
        'trial_packs': user_trial_packs,
        'corporate_orders': user_corporate_orders,
        'recent_activities': recent_activities,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        # Debug information
        'debug_user_id': user.id,
        'debug_username': user.username,
    }
    return render(request, 'fragrances/orders.html', context)

@csrf_exempt
@login_required
def add_to_cart(request):
    """Add item to user's cart"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
            
            user = request.user
            product = get_object_or_404(Product, id=product_id)
            
            # Add to cart
            cart_item = Cart.add_to_cart(user, product, quantity)
            
            # Log activity
            UserActivity.log_activity(
                user=user,
                activity_type='cart_updated',
                description=f'Added {product.name} × {quantity} to cart',
                request=request,
                content_type='Product',
                object_id=product.id,
                object_repr=str(product)
            )
            
            # Get updated cart info
            cart_count = Cart.get_cart_count(user)
            cart_total = Cart.get_cart_total(user)
            
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to cart',
                'cart_count': cart_count,
                'cart_total': float(cart_total),
                'cart_item_id': cart_item.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required
def remove_from_cart(request):
    """Remove item from user's cart"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            
            user = request.user
            product = get_object_or_404(Product, id=product_id)
            
            # Remove from cart
            removed = Cart.remove_from_cart(user, product)
            
            if removed:
                # Log activity
                UserActivity.log_activity(
                    user=user,
                    activity_type='cart_updated',
                    description=f'Removed {product.name} from cart',
                    request=request,
                    content_type='Product',
                    object_id=product.id,
                    object_repr=str(product)
                )
            
            # Get updated cart info
            cart_count = Cart.get_cart_count(user)
            cart_total = Cart.get_cart_total(user)
            
            return JsonResponse({
                'success': True,
                'message': f'{product.name} removed from cart',
                'cart_count': cart_count,
                'cart_total': float(cart_total),
                'removed': removed
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required
def update_cart_quantity(request):
    """Update cart item quantity"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
            
            user = request.user
            product = get_object_or_404(Product, id=product_id)
            
            # Update quantity
            cart_item = Cart.update_quantity(user, product, quantity)
            
            # Log activity
            UserActivity.log_activity(
                user=user,
                activity_type='cart_updated',
                description=f'Updated {product.name} quantity to {quantity}',
                request=request,
                content_type='Product',
                object_id=product.id,
                object_repr=str(product)
            )
            
            # Get updated cart info
            cart_count = Cart.get_cart_count(user)
            cart_total = Cart.get_cart_total(user)
            
            return JsonResponse({
                'success': True,
                'message': f'Updated {product.name} quantity',
                'cart_count': cart_count,
                'cart_total': float(cart_total),
                'item_quantity': cart_item.quantity
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def get_cart_info(request):
    """Get current cart information"""
    user = request.user
    cart_count = Cart.get_cart_count(user)
    cart_total = Cart.get_cart_total(user)
    
    return JsonResponse({
        'success': True,
        'cart_count': cart_count,
        'cart_total': float(cart_total)
    })

def checkout_complete(request):
    if request.method == 'POST':
        try:
            # Check if user is logged in
            current_user = request.user if request.user.is_authenticated else None
            
            # Check if this is a cart order or single product order
            cart = request.session.get('cart', {})
            product_id = request.POST.get('product_id')
            final_total = float(request.POST.get('final_total', 0))
            
            if cart and not product_id:
                # Handle cart order (multiple items from session)
                orders = []
                total_amount = 0
                
                for item_id, item_data in cart.items():
                    try:
                        product = get_object_or_404(Product, id=item_id)
                        item_total = product.price * item_data['quantity']
                        total_amount += item_total
                        
                        # Create order for this item
                        order = Order.objects.create(
                            # User Information
                            user=current_user,
                            
                            # Customer Information
                            first_name=request.POST.get('first_name'),
                            last_name=request.POST.get('last_name'),
                            email=request.POST.get('email'),
                            phone=request.POST.get('phone'),
                            
                            # Shipping Information
                            address=request.POST.get('address'),
                            city=request.POST.get('city'),
                            state=request.POST.get('state'),
                            postal_code=request.POST.get('postal_code'),
                            country=request.POST.get('country'),
                            
                            # Order Details
                            product=product,
                            quantity=item_data['quantity'],
                            product_price=product.price,
                            shipping_cost=500.00,  # Fixed shipping per item in INR
                            total_amount=item_total + 500.00,
                            
                            # Payment Information
                            payment_method=request.POST.get('payment_method'),
                            payment_status='pending',
                            
                            # Additional Information
                            order_notes=request.POST.get('order_notes', ''),
                        )
                        orders.append(order)
                        
                        # Log activity if user is logged in
                        if current_user:
                            UserActivity.log_activity(
                                user=current_user,
                                activity_type='order_created',
                                description=f'Order #{order.id} created for {product.name} × {item_data["quantity"]}',
                                request=request,
                                content_type='Order',
                                object_id=order.id,
                                object_repr=str(order)
                            )
                    except Product.DoesNotExist:
                        continue
                
                # Send confirmation email for cart order
                try:
                    order_details = '\n'.join([
                        f"- {order.product.name} × {order.quantity} = ₹{(order.product_price * order.quantity):.2f}"
                        for order in orders
                    ])
                    
                    send_mail(
                        f'Order Confirmation - VICTNOW Orders #{", ".join([str(order.id) for order in orders])}',
                        f'''Dear {request.POST.get('first_name')} {request.POST.get('last_name')},

Thank you for your order! Your orders have been received and are being processed.

Order Details:
{order_details}

Total Amount: ₹{final_total:.2f}

Shipping Address:
{request.POST.get('address')}
{request.POST.get('city')}, {request.POST.get('state')} {request.POST.get('postal_code')}
{request.POST.get('country')}

We will notify you once your orders have been shipped.

Best regards,
VICTNOW Team''',
                        settings.DEFAULT_FROM_EMAIL,
                        [request.POST.get('email')],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Email sending failed: {e}")
                
                # Clear cart after successful order
                request.session['cart'] = {}
                request.session.modified = True
                
                messages.success(request, f'Orders placed successfully! Your order numbers are: #{", ".join([str(order.id) for order in orders])}.')
                return redirect('home')
                
            else:
                # Handle single product order (existing logic)
                product_id = request.POST.get('product_id')
                quantity = int(request.POST.get('quantity', 1))
                
                # Get product
                product = get_object_or_404(Product, id=product_id)
                
                # Calculate totals
                product_price = product.price
                shipping_cost = 500.00  # INR shipping
                total_amount = (product_price * quantity) + shipping_cost
                
                # Create order
                order = Order.objects.create(
                    # User Information
                    user=current_user,
                    
                    # Customer Information
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name'),
                    email=request.POST.get('email'),
                    phone=request.POST.get('phone'),
                    
                    # Shipping Information
                    address=request.POST.get('address'),
                    city=request.POST.get('city'),
                    state=request.POST.get('state'),
                    postal_code=request.POST.get('postal_code'),
                    country=request.POST.get('country'),
                    
                    # Order Details
                    product=product,
                    quantity=quantity,
                    product_price=product_price,
                    shipping_cost=shipping_cost,
                    total_amount=total_amount,
                    
                    # Payment Information
                    payment_method=request.POST.get('payment_method'),
                    payment_status='pending',
                    
                    # Additional Information
                    order_notes=request.POST.get('order_notes', ''),
                )
                
                # Log activity if user is logged in
                if current_user:
                    UserActivity.log_activity(
                        user=current_user,
                        activity_type='order_created',
                        description=f'Order #{order.id} created for {product.name} × {quantity}',
                        request=request,
                        content_type='Order',
                        object_id=order.id,
                        object_repr=str(order)
                    )
                
                # Send confirmation email (optional)
                try:
                    send_mail(
                        f'Order Confirmation - VICTNOW Order #{order.id}',
                        f'''Dear {order.get_full_name()},

Thank you for your order! Your order has been received and is being processed.

Order Details:
- Order Number: #{order.id}
- Product: {product.name}
- Quantity: {quantity}
- Total Amount: ₹{total_amount}

Shipping Address:
{order.address}
{order.city}, {order.state} {order.postal_code}
{order.country}

We will notify you once your order has been shipped.

Best regards,
VICTNOW Team''',
                        settings.DEFAULT_FROM_EMAIL,
                        [order.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Email sending failed: {e}")
                
                messages.success(request, f'Order placed successfully! Your order number is #{order.id}.')
            
            # Clear cart after successful order
            if cart_data_json:
                # Note: We can't directly clear localStorage from Django view
                # This will be handled in the frontend JavaScript
                pass
            
            return redirect('home')
            
        except Exception as e:
            messages.error(request, f'An error occurred while processing your order: {str(e)}')
            return redirect('cart')
    
    return redirect('home')

def corporate_gifting(request):
    context = {}
    return render(request, 'fragrances/corporate_gifting.html', context)

def bulk_order_process(request):
    """Process enhanced bulk order submission"""
    if request.method == 'POST':
        try:
            print(f"BULK ORDER: Received POST request")
            print(f"BULK ORDER: POST data: {dict(request.POST)}")
            
            # Get form data
            name = request.POST.get('name')
            email = request.POST.get('email')
            company_name = request.POST.get('company')
            phone = request.POST.get('phone')
            shipping_address = request.POST.get('address')
            
            fragrance_type = request.POST.get('fragrance_type')
            quantity_str = request.POST.get('quantity')
            unit_size = request.POST.get('unit_size', '50ml')
            packaging = request.POST.get('packaging', 'standard')
            
            delivery_date = request.POST.get('delivery_date')
            special_instructions = request.POST.get('message', '')
            
            print(f"BULK ORDER: Parsed data - name: {name}, email: {email}, company: {company_name}")
            print(f"BULK ORDER: Product data - fragrance: {fragrance_type}, quantity: {quantity_str}")
            
            # Validate required fields
            if not all([name, email, company_name, phone, shipping_address, fragrance_type, quantity_str]):
                error_msg = "Missing required fields"
                print(f"BULK ORDER: Validation error - {error_msg}")
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                })
            
            # Convert quantity to integer safely
            try:
                quantity = int(quantity_str)
                if quantity < 10:
                    error_msg = "Minimum quantity is 10 units"
                    print(f"BULK ORDER: Quantity validation error - {error_msg}")
                    return JsonResponse({
                        'success': False,
                        'message': error_msg
                    })
            except ValueError:
                error_msg = "Invalid quantity format"
                print(f"BULK ORDER: Quantity format error - {error_msg}")
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                })
            
            # Calculate pricing
            prices = {
                'victnow_forge': 2999,
                'victnow_muse': 2999,
                'victnow_nexus': 2999,
                'mixed_collection': 2499,
                'custom': 41500
            }
            
            packaging_costs = {
                'standard': 0,
                'premium': 200,
                'custom': 500
            }
            
            unit_price = prices.get(fragrance_type, 2999)
            packaging_cost = packaging_costs.get(packaging, 0)
            total_amount = (unit_price + packaging_cost) * quantity
            
            print(f"BULK ORDER: Calculated pricing - unit_price: {unit_price}, packaging_cost: {packaging_cost}, total: {total_amount}")
            
            # Generate unique order ID
            import time
            order_id = f"BULK_{int(time.time())}"
            
            print(f"BULK ORDER: Creating order with ID: {order_id}")
            
            # Create bulk order
            bulk_order = CorporateOrder.objects.create(
                order_id=order_id,
                name=name,
                email=email,
                company_name=company_name,
                phone=phone,
                shipping_address=shipping_address,
                fragrance_type=fragrance_type,
                quantity=quantity,
                unit_size=unit_size,
                packaging=packaging,
                unit_price=unit_price,
                packaging_cost=packaging_cost,
                total_amount=total_amount,
                delivery_date=delivery_date if delivery_date else None,
                special_instructions=special_instructions,
                status='pending'
            )
            
            print(f"BULK ORDER: Order created successfully - ID: {bulk_order.id}, Order ID: {bulk_order.order_id}")
            
            # Verify order was saved
            try:
                saved_order = CorporateOrder.objects.get(order_id=order_id)
                print(f"BULK ORDER: Verified order exists in database - ID: {saved_order.id}")
            except CorporateOrder.DoesNotExist:
                print(f"BULK ORDER: ERROR - Order not found in database after creation!")
                return JsonResponse({
                    'success': False,
                    'message': 'Order was not saved to database. Please try again.'
                })
            
            # Send email notification
            try:
                send_mail(
                    f'New Bulk Order: {order_id}',
                    f'New bulk order received:\n\n'
                    f'Order ID: {order_id}\n'
                    f'Company: {company_name}\n'
                    f'Contact: {name} ({email})\n'
                    f'Phone: {phone}\n'
                    f'Fragrance: {fragrance_type}\n'
                    f'Quantity: {quantity} {unit_size}\n'
                    f'Packaging: {packaging}\n'
                    f'Total Amount: ₹{total_amount:,.2f}\n\n'
                    f'Special Instructions: {special_instructions}',
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.DEFAULT_FROM_EMAIL],
                    fail_silently=True,
                )
                print(f"BULK ORDER: Email notification sent to admin")
            except Exception as e:
                print(f"BULK ORDER: Error sending email: {e}")
            
            # Return success response
            response_data = {
                'success': True,
                'order_id': order_id,
                'message': f'Bulk order submitted successfully! Order ID: {order_id}'
            }
            print(f"BULK ORDER: Returning success response: {response_data}")
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"BULK ORDER: Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'An error occurred: {str(e)}'
            })
    
    print(f"BULK ORDER: Invalid request method: {request.method}")
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

def test_bulk_order(request):
    """Test bulk order creation directly"""
    print("TEST BULK ORDER: Creating test order...")
    
    try:
        from .models import CorporateOrder
        import time
        
        # Create test order
        order_id = f"TEST_{int(time.time())}"
        test_order = CorporateOrder.objects.create(
            order_id=order_id,
            name="Test User",
            email="test@example.com",
            company_name="Test Company",
            phone="1234567890",
            shipping_address="Test Address",
            fragrance_type="victnow_forge",
            quantity=10,
            unit_size="50ml",
            packaging="standard",
            unit_price=2999.00,
            packaging_cost=0.00,
            total_amount=29990.00,
            delivery_date=None,
            special_instructions="Test order",
            status='pending'
        )
        
        print(f"TEST BULK ORDER: Created order - ID: {test_order.id}, Order ID: {test_order.order_id}")
        
        # Count orders
        order_count = CorporateOrder.objects.count()
        print(f"TEST BULK ORDER: Total orders in database: {order_count}")
        
        return JsonResponse({
            'success': True,
            'message': f'Test order created successfully! Order ID: {order_id}. Total orders: {order_count}'
        })
        
    except Exception as e:
        print(f"TEST BULK ORDER: Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Error creating test order: {str(e)}'
        })

def ping_test(request):
    """Simple ping test to verify frontend-backend connection"""
    print("PING TEST: Frontend connected to backend!")
    return JsonResponse({
        'success': True,
        'message': 'Backend is reachable!',
        'timestamp': str(timezone.now()),
        'method': request.method
    })

def test_admin_integration(request):
    """Comprehensive test to verify admin panel integration"""
    print("ADMIN INTEGRATION TEST: Starting comprehensive test...")
    
    try:
        from .models import CorporateOrder
        from django.contrib.admin.sites import site
        import time
        
        # Test 1: Check if model is registered with admin
        print("ADMIN INTEGRATION TEST: Checking admin registration...")
        admin_registry = site._registry
        corporate_order_registered = CorporateOrder in admin_registry
        print(f"ADMIN INTEGRATION TEST: CorporateOrder registered in admin: {corporate_order_registered}")
        
        if corporate_order_registered:
            admin_class = admin_registry[CorporateOrder]
            print(f"ADMIN INTEGRATION TEST: Admin class: {admin_class.__class__.__name__}")
            print(f"ADMIN INTEGRATION TEST: List display: {admin_class.list_display}")
            print(f"ADMIN INTEGRATION TEST: Search fields: {admin_class.search_fields}")
        
        # Test 2: Count existing orders
        print("\nADMIN INTEGRATION TEST: Counting existing orders...")
        existing_count = CorporateOrder.objects.count()
        print(f"ADMIN INTEGRATION TEST: Existing bulk orders: {existing_count}")
        
        # Test 3: Create test order
        print("\nADMIN INTEGRATION TEST: Creating test order...")
        order_id = f"ADMIN_TEST_{int(time.time())}"
        test_order = CorporateOrder.objects.create(
            order_id=order_id,
            name="Admin Test User",
            email="admin@test.com",
            company_name="Admin Test Company",
            phone="1234567890",
            shipping_address="Admin Test Address",
            fragrance_type="victnow_forge",
            quantity=15,
            unit_size="50ml",
            packaging="standard",
            unit_price=2999.00,
            packaging_cost=0.00,
            total_amount=44985.00,
            delivery_date=None,
            special_instructions="Admin integration test order",
            status='pending'
        )
        
        print(f"ADMIN INTEGRATION TEST: Created test order - ID: {test_order.id}")
        print(f"ADMIN INTEGRATION TEST: Order ID: {test_order.order_id}")
        
        # Test 4: Verify order exists
        print("\nADMIN INTEGRATION TEST: Verifying order exists...")
        try:
            retrieved_order = CorporateOrder.objects.get(order_id=order_id)
            print(f"ADMIN INTEGRATION TEST: Order retrieved successfully - {retrieved_order.company_name}")
        except CorporateOrder.DoesNotExist:
            print("ADMIN INTEGRATION TEST: ERROR - Order not found after creation!")
            return JsonResponse({
                'success': False,
                'message': 'Order creation failed - not found in database'
            })
        
        # Test 5: Count new total
        new_count = CorporateOrder.objects.count()
        print(f"ADMIN INTEGRATION TEST: New total orders: {new_count}")
        
        # Test 6: Check admin URL
        print("\nADMIN INTEGRATION TEST: Checking admin URLs...")
        from django.urls import reverse
        try:
            admin_changelist_url = reverse('admin:fragrances_corporateorder_changelist')
            print(f"ADMIN INTEGRATION TEST: Admin changelist URL: {admin_changelist_url}")
        except Exception as e:
            print(f"ADMIN INTEGRATION TEST: Admin URL error: {e}")
        
        # Test 7: List all orders for debugging
        print("\nADMIN INTEGRATION TEST: Listing all orders...")
        all_orders = CorporateOrder.objects.all()
        for order in all_orders:
            print(f"ADMIN INTEGRATION TEST: Order - ID: {order.id}, OrderID: {order.order_id}, Company: {order.company_name}, Status: {order.status}")
        
        return JsonResponse({
            'success': True,
            'message': f'Admin integration test completed! Created order {order_id}',
            'admin_registered': corporate_order_registered,
            'existing_count': existing_count,
            'new_count': new_count,
            'test_order_details': {
                'id': test_order.id,
                'order_id': test_order.order_id,
                'company_name': test_order.company_name,
                'quantity': test_order.quantity,
                'status': test_order.status
            },
            'total_orders_in_db': new_count
        })
        
    except Exception as e:
        print(f"ADMIN INTEGRATION TEST: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Admin integration test failed: {str(e)}'
        })

def test_bulk_simple(request):
    """Simple test to check if bulk order endpoint is working"""
    print("SIMPLE BULK TEST: Testing bulk order process...")
    
    if request.method == 'POST':
        print("SIMPLE BULK TEST: Received POST request")
        print(f"SIMPLE BULK TEST: POST data: {dict(request.POST)}")
        
        # Test data
        test_data = {
            'name': 'Test User Simple',
            'email': 'test@simple.com',
            'company': 'Test Company Simple',
            'phone': '1234567890',
            'address': 'Test Address Simple',
            'fragrance_type': 'victnow_forge',
            'quantity': '10',
            'unit_size': '50ml',
            'packaging': 'standard',
            'delivery_date': '',
            'message': 'Simple test order'
        }
        
        print("SIMPLE BULK TEST: Using test data:", test_data)
        
        # Simulate form data
        from django.http import QueryDict
        request.POST = QueryDict(mutable=True)
        for key, value in test_data.items():
            request.POST[key] = value
        
        print("SIMPLE BULK TEST: Modified request.POST:", dict(request.POST))
        
        # Call the actual bulk order process function
        return bulk_order_process(request)
    else:
        return JsonResponse({
            'success': False,
            'message': 'Only POST method allowed'
        })

def test_database(request):
    """Test database operations for bulk orders"""
    print("DATABASE TEST: Testing bulk order creation...")
    
    try:
        from .models import CorporateOrder
        import time
        
        # Count existing orders
        existing_count = CorporateOrder.objects.count()
        print(f"DATABASE TEST: Existing bulk orders: {existing_count}")
        
        # Create test order
        order_id = f"TEST_DB_{int(time.time())}"
        test_order = CorporateOrder.objects.create(
            order_id=order_id,
            name="Database Test User",
            email="test@database.com",
            company_name="Test Company DB",
            phone="1234567890",
            shipping_address="Test Address DB",
            fragrance_type="victnow_forge",
            quantity=10,
            unit_size="50ml",
            packaging="standard",
            unit_price=2999.00,
            packaging_cost=0.00,
            total_amount=29990.00,
            delivery_date=None,
            special_instructions="Database test order",
            status='pending'
        )
        
        # Verify creation
        new_count = CorporateOrder.objects.count()
        print(f"DATABASE TEST: Created order ID: {test_order.order_id}")
        print(f"DATABASE TEST: New total orders: {new_count}")
        
        # Get the created order
        retrieved_order = CorporateOrder.objects.get(order_id=order_id)
        print(f"DATABASE TEST: Retrieved order: {retrieved_order.company_name}")
        
        return JsonResponse({
            'success': True,
            'message': f'Database test successful! Created order {order_id}',
            'existing_count': existing_count,
            'new_count': new_count,
            'order_details': {
                'order_id': retrieved_order.order_id,
                'company_name': retrieved_order.company_name,
                'quantity': retrieved_order.quantity,
                'status': retrieved_order.status
            }
        })
        
    except Exception as e:
        print(f"DATABASE TEST: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Database test failed: {str(e)}'
        })

def track_bulk_order(request):
    """Handle bulk order tracking requests"""
    if request.method == 'POST':
        order_id = request.POST.get('order_id', '').strip()
        email = request.POST.get('email', '').strip()
        
        print(f"BULK TRACKING: Looking for order {order_id} with email {email}")
        
        try:
            # Try to find the bulk order
            from .models import CorporateOrder, BulkOrderTracking
            
            order = CorporateOrder.objects.filter(order_id__iexact=order_id).first()
            
            if not order:
                return JsonResponse({
                    'success': False,
                    'message': 'Order ID not found. Please check your order ID and try again.'
                })
            
            # Verify email (optional but recommended for security)
            if email and order.email.lower() != email.lower():
                return JsonResponse({
                    'success': False,
                    'message': 'Email does not match our records for this order.'
                })
            
            # Get tracking information if available
            tracking_info = None
            try:
                tracking = BulkOrderTracking.objects.get(bulk_order=order)
                tracking_info = {
                    'tracking_number': tracking.tracking_number,
                    'carrier': tracking.carrier,
                    'status': tracking.status,
                    'estimated_delivery': tracking.estimated_delivery.strftime('%Y-%m-%d') if tracking.estimated_delivery else None,
                    'actual_delivery': tracking.actual_delivery.strftime('%Y-%m-%d') if tracking.actual_delivery else None,
                    'tracking_notes': tracking.tracking_notes,
                    'updated_at': tracking.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            except BulkOrderTracking.DoesNotExist:
                tracking_info = None
            
            # Prepare order details
            order_details = {
                'order_id': order.order_id,
                'company_name': order.company_name,
                'name': order.name,
                'email': order.email,
                'fragrance_type': order.get_fragrance_display(),
                'quantity': order.quantity,
                'unit_size': order.unit_size,
                'packaging': order.packaging,
                'total_amount': f"₹{order.total_amount:,.2f}",
                'status': order.status,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'shipping_address': order.shipping_address,
                'special_instructions': order.special_instructions
            }
            
            return JsonResponse({
                'success': True,
                'order': order_details,
                'tracking': tracking_info,
                'message': 'Order found successfully!'
            })
            
        except Exception as e:
            print(f"BULK TRACKING: Error - {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while tracking your order. Please try again.'
            })
    
    # Handle GET request - show tracking page
    return render(request, 'fragrances/track_bulk_order.html')

def about(request):
    testimonials = Testimonial.objects.all()
    context = {'testimonials': testimonials}
    return render(request, 'fragrances/about.html', context)

def privacy(request):
    """Render the privacy policy page"""
    return render(request, 'fragrances/privacy.html')

def about_victnow_luxury(request):
    """Render the luxury about victnow page"""
    return render(request, 'fragrances/about_victnow_luxury.html')

def reviews(request):
    print("Reviews view called")  # Debug print
    try:
        # Use the simple template that always works
        print("Using simple reviews template")
        return render(request, 'fragrances/reviews_simple.html')
    except Exception as e:
        print(f"Error in reviews view: {e}")  # Debug print
        import traceback
        traceback.print_exc()  # Debug print full error
        # Return empty page on error
        return render(request, 'fragrances/reviews_simple.html')

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

def contact(request):
    try:
        if request.method == 'POST':
            name = request.POST.get('name')
            email = request.POST.get('email')
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            
            # Save to database
            contact_message = ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
        
        # For GET requests, render the redesigned template
        return render(request, 'fragrances/contact.html')
    except Exception as e:
        print(f"Contact view error: {e}")
        import traceback
        traceback.print_exc()
        # Return a simple error page
        return render(request, 'fragrances/contact.html')

def newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            Newsletter.objects.get(email=email)
            messages.warning(request, 'You are already subscribed to our newsletter.')
        except Newsletter.DoesNotExist:
            Newsletter.objects.create(email=email)
            messages.success(request, 'Thank you for subscribing to our newsletter!')
    
    return redirect('home')

# User Registration Views
@csrf_exempt
@require_POST
def send_real_otp(request):
    try:
        data = json.loads(request.body)
        mobile_number = data.get('mobile_number')
        country_code = data.get('country_code', '+91')
        full_number = country_code + mobile_number
        
        print("Sending real OTP to:", full_number)
        
        # Generate random 6-digit OTP
        import random
        otp = str(random.randint(100000, 999999))
        
        # Store OTP in session
        request.session['otp'] = otp
        request.session['mobile_number'] = full_number
        request.session['otp_generated_time'] = timezone.now().isoformat()
        
        print("Generated OTP:", otp)
        
        # Fast2SMS Integration (real SMS sending):
        import requests
        from django.conf import settings
        
        # Fast2SMS API endpoint
        url = "https://api.fast2sms.com/bulk/v2"
        
        # Fast2SMS API configuration
        FAST2SMS_API_KEY = getattr(settings, 'FAST2SMS_API_KEY', 'buN1BkI57lcxVrSmjvKHYozaiwCsgZ6nGXfQAT3O8UE4Ly2dhMEHxfPwJSm3byt6M2gdl0TIpDQaGk5U')
        FAST2SMS_SENDER_ID = getattr(settings, 'FAST2SMS_SENDER_ID', 'FSTSMS')
        FAST2SMS_TEMPLATE_ID = getattr(settings, 'FAST2SMS_TEMPLATE_ID', 'otp_template')
        FAST2SMS_ROUTE = getattr(settings, 'FAST2SMS_ROUTE', '3')
        FAST2SMS_LANGUAGE = getattr(settings, 'FAST2SMS_LANGUAGE', 'english')
        
        # Prepare headers and payload for Fast2SMS
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
        
        # Send SMS via Fast2SMS
        try:
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
            
            print("Fast2SMS Response:", response_data)
            
            # Check if SMS was sent successfully
            if response.status_code == 200 and response_data.get('return') == True:
                print(f"SMS sent successfully to {full_number}")
                print(f"SMS ID: {response_data.get('message_id', 'unknown')}")
            else:
                print(f"SMS sending failed: {response_data.get('message', 'Unknown error')}")
                
        except Exception as sms_error:
            print(f"Fast2SMS Error: {str(sms_error)}")
            # Continue with OTP generation even if SMS fails
        
        return JsonResponse({
            'success': True,
            'message': f'OTP sent to {full_number[-4:]}****',
            # 'otp_for_testing': otp  # Remove this in production
        })
        
    except Exception as e:
        print("Error sending OTP:", str(e))
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def verify_real_otp(request):
    try:
        data = json.loads(request.body)
        entered_otp = data.get('otp')
        
        stored_otp = request.session.get('otp')
        mobile_number = request.session.get('mobile_number')
        
        print("Verifying OTP - Entered:", entered_otp)
        print("Verifying OTP - Stored:", stored_otp)
        
        if not stored_otp:
            return JsonResponse({'success': False, 'error': 'OTP not found. Please request new OTP'})
        
        if entered_otp == stored_otp:
            # Clear OTP from session
            del request.session['otp']
            
            # Register or get user
            username = f"user_{mobile_number[-4:]}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@victnow.com',
                    'first_name': 'User',
                    'last_name': mobile_number[-4:]
                }
            )
            
            # Create or update user profile
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'phone_number': mobile_number,
                    'country_code': mobile_number[:3] if mobile_number else '+91',
                    'login_method': 'mobile',
                    'is_verified': True
                }
            )
            
            # Update profile information with frontend login data
            profile.phone_number = mobile_number
            profile.country_code = mobile_number[:3] if mobile_number else '+91'
            profile.login_method = 'mobile'
            profile.is_verified = True
            profile.last_login = timezone.now()
            
            # Capture frontend login information
            profile.login_ip_address = get_client_ip(request)
            profile.login_user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limit length
            profile.frontend_session_id = request.session.session_key or ''
            
            # Detect device type and browser
            user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
            if 'mobile' in user_agent:
                profile.login_device_type = 'mobile'
            elif 'tablet' in user_agent:
                profile.login_device_type = 'tablet'
            else:
                profile.login_device_type = 'desktop'
            
            # Extract browser information
            if 'chrome' in user_agent:
                profile.login_browser = 'Chrome'
            elif 'firefox' in user_agent:
                profile.login_browser = 'Firefox'
            elif 'safari' in user_agent:
                profile.login_browser = 'Safari'
            elif 'edge' in user_agent:
                profile.login_browser = 'Edge'
            else:
                profile.login_browser = 'Unknown'
            
            # Update login counters
            profile.successful_logins += 1
            profile.save()
            
            print(f"Updated profile for: {user.username}")
            print(f"Login IP: {profile.login_ip_address}")
            print(f"Device: {profile.login_device_type}")
            print(f"Browser: {profile.login_browser}")
            print(f"Successful logins: {profile.successful_logins}")
            
            # Log in the user using Django's authentication system
            from django.contrib.auth import login
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            return JsonResponse({
                'success': True,
                'message': 'OTP verified successfully',
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
                    'is_verified': profile.is_verified
                }
            })
        else:
            return JsonResponse({'success': False, 'error': 'Invalid OTP. Please try again'})
            
    except Exception as e:
        print("Error verifying OTP:", str(e))
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def register_user_with_mobile(request):
    print("register_user_with_mobile called")  # Debug print
    print("Request method:", request.method)  # Debug print
    print("Request body:", request.body)  # Debug print
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Parsed data:", data)  # Debug print
            
            phone_number = data.get('phone_number')
            country_code = data.get('country_code', '+91')
            
            print("Phone number:", phone_number)  # Debug print
            print("Country code:", country_code)  # Debug print
            
            # Create or get user
            username = f"user_{phone_number[-4:]}"  # Use last 4 digits as username
            print("Creating user with username:", username)  # Debug print
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@victnow.com',
                    'first_name': 'User',
                    'last_name': phone_number[-4:]
                }
            )
            
            print("User created:", created)  # Debug print
            print("User ID:", user.id)  # Debug print
            
            # Create or update user profile
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'phone_number': phone_number,
                    'country_code': country_code,
                    'login_method': 'mobile',
                    'is_verified': True
                }
            )
            
            print("Profile created:", profile_created)  # Debug print
            print("Profile ID:", profile.id)  # Debug print
            
            if not profile_created:
                profile.phone_number = phone_number
                profile.country_code = country_code
                profile.is_verified = True
                profile.last_login = timezone.now()
                profile.save()
                print("Profile updated")  # Debug print
            else:
                # For newly created profiles, set last_login
                profile.last_login = timezone.now()
                profile.save(update_fields=['last_login'])
            
            # Log in the user using Django's authentication system
            login(request, user)
            
            print("User and profile created successfully")  # Debug print
            
            return JsonResponse({
                'success': True,
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
                    'is_verified': profile.is_verified
                }
            })
            
        except Exception as e:
            print("Error in register_user_with_mobile:", str(e))  # Debug print
            import traceback
            traceback.print_exc()  # Debug print
            return JsonResponse({'success': False, 'error': str(e)})
    
    print("Invalid request method")  # Debug print
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@require_POST
def register_user_with_social(request):
    try:
        data = json.loads(request.body)
        provider = data.get('provider')  # 'google' or 'facebook'
        name = data.get('name')
        email = data.get('email')
        picture = data.get('picture', '')
        
        # Create or get user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'first_name': name.split(' ')[0] if ' ' in name else name,
                'last_name': name.split(' ')[1] if ' ' in name else '',
            }
        )
        
        # Create or update user profile
        profile, profile_created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'login_method': provider,
                'profile_picture': picture,
                'is_verified': True
            }
        )
        
        if not profile_created:
            profile.login_method = provider
            profile.profile_picture = picture
            profile.is_verified = True
            profile.last_login = timezone.now()
            profile.save()
        else:
            # For newly created profiles, set last_login
            profile.last_login = timezone.now()
            profile.save(update_fields=['last_login'])
        
        # Log in the user
        login(request, user)
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'login_method': profile.login_method,
                'profile_picture': profile.profile_picture,
                'is_verified': profile.is_verified
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def save_order(request):
    """Save order to database"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        import json
        from django.utils import timezone
        from .models import Order, Product
        
        # Parse order data
        order_data = json.loads(request.body)
        
        # Get customer name from order data
        customer_name = order_data.get('customer_name', '')
        name_parts = customer_name.split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Get product (default to first product if not specified)
        product_id = order_data.get('product_id')
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                product = Product.objects.first()  # Fallback to first product
        else:
            product = Product.objects.first()  # Fallback to first product
        
        # Create order record
        order = Order.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=order_data.get('customer_email', ''),
            phone=order_data.get('customer_phone', ''),
            address=order_data.get('address', ''),
            city=order_data.get('city', ''),
            state=order_data.get('state', ''),
            postal_code=order_data.get('pincode', ''),
            country='India',  # Default country
            product=product,
            quantity=order_data.get('quantity', 1),
            product_price=product.price if product else 2999.00,
            shipping_cost=500.00,  # Default shipping cost
            total_amount=order_data.get('total_amount', product.price if product else 2999.00),
            payment_method=order_data.get('payment_method', 'cod'),
            payment_status=order_data.get('payment_status', 'pending'),
            order_status='confirmed' if order_data.get('payment_status') == 'success' else 'pending',
            order_notes=json.dumps(order_data.get('items', [])) if order_data.get('items') else ''
        )
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'message': 'Order saved successfully'
        })
        
    except Exception as e:
        print(f"Error saving order: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

def order_success(request):
    """Display order success page"""
    order_id = request.GET.get('order_id', '')
    
    context = {
        'order_id': order_id,
        'message': 'Thank you for your order!'
    }
    
    return render(request, 'fragrances/order_success.html', context)

def trail_customer(request):
    """Render the trail customer form page"""
    return render(request, 'fragrances/trail_customer.html')

def bulk_customer(request):
    """Render the bulk customer form page"""
    return render(request, 'fragrances/bulk_customer.html')
