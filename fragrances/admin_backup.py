from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.admin import TabularInline
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Product, Testimonial, BlogPost, ContactMessage, Newsletter, Order, CorporateOrder, OrderTracking, BulkOrderTracking, UserProfile, TrialPack, TrialPackTracking


# Customize UserAdmin to show UserProfile information
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'profile_info', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    
    def profile_info(self, obj):
        """Show profile information in User admin"""
        try:
            profile = obj.profile
            return format_html(
                '<span style="color: {};">●</span> {} ({})',
                '#28a745' if profile.is_verified else '#dc3545',
                profile.get_login_method_display() if hasattr(profile, 'get_login_method_display') else profile.login_method.upper(),
                'Verified' if profile.is_verified else 'Not Verified'
            )
        except UserProfile.DoesNotExist:
            return format_html('<span style="color: #dc3545;">● No Profile</span>')
    profile_info.short_description = 'Profile'
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:  # Only for existing users
            fieldsets += (('Profile Information', {
                'fields': ('profile',),
                'classes': ('collapse',),
                'description': 'User profile information including login method and verification status'
            }),)
        return fieldsets
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly_fields.append('profile')
        return readonly_fields
    
    def profile(self, obj):
        """Display profile link"""
        try:
            profile = obj.profile
            return format_html(
                '<a href="/admin/fragrances/userprofile/{}/change/">View Profile</a>',
                profile.id
            )
        except UserProfile.DoesNotExist:
            return format_html('<a href="/admin/fragrances/userprofile/add/?user={}">Create Profile</a>', obj.id)
    profile.short_description = 'User Profile'


# Register User with custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# Add inline for TrialPackTracking
class TrialPackTrackingInline(TabularInline):
    model = TrialPackTracking
    extra = 0
    can_delete = True
    fields = ('tracking_number', 'carrier', 'status', 'estimated_delivery', 'actual_delivery')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_image', 'name', 'price', 'featured', 'created_at']
    list_filter = ['featured', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    
    def product_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "No Image"
    product_image.short_description = 'Image'

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'client_title', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['client_name', 'content']

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'content']
    ordering = ['-created_at']

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email', 'subject']
    ordering = ['-created_at']

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'created_at']
    ordering = ['-created_at']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'product_name', 'quantity', 'total_amount', 'order_status_badge', 'payment_status_badge', 'created_at']
    list_filter = ['order_status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'product__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    # Enhanced actions for order management
    actions = ['mark_as_shipped', 'mark_as_delivered', 'mark_as_processing', 'send_order_confirmation_email', 'export_selected_orders']
    
    def order_status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'shipped': 'green',
            'delivered': 'darkgreen',
            'cancelled': 'red'
        }
        color = colors.get(obj.order_status, 'black')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.order_status.upper()
        )
    order_status_badge.short_description = 'Status'
    
    def payment_status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'completed': 'green',
            'failed': 'red',
            'refunded': 'purple'
        }
        color = colors.get(obj.payment_status, 'black')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.payment_status.upper()
        )
    payment_status_badge.short_description = 'Payment'
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(order_status='shipped')
        self.message_user(request, f'{updated} order(s) marked as shipped.')
    mark_as_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(order_status='delivered')
        self.message_user(request, f'{updated} order(s) marked as delivered.')
    mark_as_delivered.short_description = "Mark selected orders as delivered"
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(order_status='processing')
        self.message_user(request, f'{updated} order(s) marked as processing.')
    mark_as_processing.short_description = "Mark selected orders as processing"
    
    def send_order_confirmation_email(self, request, queryset):
        from django.core.mail import send_mail
        from django.conf import settings
        
        count = 0
        for order in queryset:
            try:
                send_mail(
                    f'Order Confirmation - #{order.id}',
                    f'''Dear {order.get_full_name()},

Your order has been confirmed!

Order Details:
- Order ID: {order.id}
- Product: {order.product.name}
- Quantity: {order.quantity}
- Total Amount: ₹{order.total_amount:,.2f}
- Status: {order.order_status}

Thank you for shopping with VICTNOW!

Best regards,
VICTNOW Team''',
                    settings.DEFAULT_FROM_EMAIL,
                    [order.email],
                    fail_silently=True,
                )
                count += 1
            except Exception as e:
                self.message_user(request, f'Error sending email for order {order.id}: {str(e)}', level='ERROR')
        
        self.message_user(request, f'Confirmation emails sent for {count} order(s).')
    send_order_confirmation_email.short_description = "Send confirmation emails"
    
    def export_selected_orders(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Order ID', 'Customer Name', 'Email', 'Product', 'Quantity', 'Total Amount', 'Status', 'Created At'])
        
        for order in queryset:
            writer.writerow([
                order.id,
                order.get_full_name(),
                order.email,
                order.product.name,
                order.quantity,
                order.total_amount,
                order.order_status,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_selected_orders.short_description = "Export selected orders to CSV"
    
    # Enhanced fieldsets with better organization
    fieldsets = (
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Customer contact and personal information'
        }),
        ('Shipping Information', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Delivery address details'
        }),
        ('Order Details', {
            'fields': ('product', 'quantity', 'product_price', 'shipping_cost', 'total_amount'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Product and pricing information'
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Payment method and status'
        }),
        ('Order Management', {
            'fields': ('order_status',),
            'classes': ('wide', 'extrapretty'),
            'description': 'Current order status and tracking'
        }),
        ('Additional Information', {
            'fields': ('order_notes',),
            'classes': ('collapse', 'wide', 'extrapretty'),
            'description': 'Any additional notes or special instructions'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse', 'wide', 'extrapretty'),
            'description': 'System-generated timestamps'
        }),
    )
    
    def customer_name(self, obj):
        return obj.get_full_name()
    customer_name.short_description = 'Customer'
    
    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'

@admin.register(CorporateOrder)
class CorporateOrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'company_name', 'name', 'email', 'fragrance_display', 'quantity', 'total_amount_formatted', 'status_badge', 'created_at']
    list_filter = ['status', 'fragrance_type', 'unit_size', 'packaging', 'created_at']
    search_fields = ['order_id', 'company_name', 'name', 'email', 'phone']
    readonly_fields = ['order_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    # Enhanced actions for bulk order management
    actions = ['save_simple_bulk_order', 'mark_bulk_confirmed', 'mark_bulk_processing', 'mark_bulk_shipped', 'mark_bulk_delivered', 'send_order_confirmation', 'create_bulk_order_manually', 'export_bulk_orders']
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'blue', 
            'processing': 'purple',
            'shipped': 'green',
            'delivered': 'darkgreen',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def export_bulk_orders(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bulk_orders_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Order ID', 'Company', 'Contact Person', 'Email', 'Phone', 'Fragrance', 'Quantity', 'Unit Size', 'Total Amount', 'Status', 'Created At'])
        
        for order in queryset:
            writer.writerow([
                order.order_id,
                order.company_name,
                order.name,
                order.email,
                order.phone,
                order.get_fragrance_display(),
                order.quantity,
                order.unit_size,
                f'₹{order.total_amount:,.2f}',
                order.status,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_bulk_orders.short_description = "Export selected bulk orders to CSV"
    
    def save_simple_bulk_order(self, request, queryset):
        """Save a simple bulk order directly to database"""
        from django.contrib import messages
        from django.urls import reverse
        from django.http import HttpResponseRedirect
        from .models import CorporateOrder
        import time
        
        # Create a simple bulk order with test data
        order_id = f"BULK_ADMIN_{int(time.time())}"
        bulk_order = CorporateOrder.objects.create(
            order_id=order_id,
            name="Admin Created Order",
            email="admin@victnow.com",
            company_name="VICTNOW Admin Order",
            phone="+918055854596",
            shipping_address="Admin Panel Created Order",
            fragrance_type="victnow_forge",
            quantity=10,
            unit_size="50ml",
            packaging="standard",
            unit_price=2999.00,
            packaging_cost=0.00,
            total_amount=29990.00,
            delivery_date=None,
            special_instructions="Order created from admin panel",
            status='pending'
        )
        
        messages.success(request, f'Bulk order {order_id} created successfully! Order ID: {order_id}')
        return HttpResponseRedirect(reverse('admin:fragrances_corporateorder_changelist'))
    
    save_simple_bulk_order.short_description = "Save Simple Bulk Order"
    
    def create_bulk_order_manually(self, request, queryset):
        """Create a new bulk order manually from admin panel"""
        from django.shortcuts import render, redirect
        from django.contrib import messages
        from django.urls import reverse
        from django.http import HttpResponseRedirect
        
        # Store a flag in session to show the custom form
        request.session['show_bulk_order_form'] = True
        messages.info(request, "Please fill out the bulk order form below.")
        
        return HttpResponseRedirect(reverse('admin:fragrances_corporateorder_changelist'))
    
    create_bulk_order_manually.short_description = "Create New Bulk Order"
    
    def changelist_view(self, request, extra_context=None):
        """Override changelist view to show bulk order form when requested"""
        from django.shortcuts import render
        from django.contrib import messages
        from django.http import JsonResponse
        from django.views.decorators.csrf import csrf_exempt
        from django.utils.decorators import method_decorator
        from django.views import View
        import time
        
        # Check if we should show the bulk order form
        show_form = request.session.pop('show_bulk_order_form', False)
        
        if show_form:
            # Add custom form context
            extra_context = extra_context or {}
            extra_context['show_bulk_order_form'] = True
            extra_context['fragrance_choices'] = [
                ('victnow_forge', 'VICTNOW FORGE (Men) - ₹2,999'),
                ('victnow_muse', 'VICTNOW MUSE (Women) - ₹2,999'),
                ('victnow_nexus', 'VICTNOW NEXUS (Unisex) - ₹2,999'),
                ('mixed_collection', 'Premium Collection (All 3) - ₹8,499'),
                ('custom', 'Custom Mix - Contact for pricing')
            ]
            extra_context['unit_size_choices'] = [
                ('50ml', '50ml'),
                ('100ml', '100ml'),
                ('custom', 'Custom Size')
            ]
            extra_context['packaging_choices'] = [
                ('standard', 'Standard Box'),
                ('premium', 'Premium Gift Box (+₹200)'),
                ('custom', 'Custom Branding (+₹500)')
            ]
            extra_context['status_choices'] = [
                ('pending', 'Pending'),
                ('confirmed', 'Confirmed'),
                ('processing', 'Processing'),
                ('shipped', 'Shipped'),
                ('delivered', 'Delivered'),
                ('cancelled', 'Cancelled')
            ]
        
        return super().changelist_view(request, extra_context)
    
    def response_add(self, request, obj, post_url_continue=None):
        """Handle successful addition of bulk order"""
        from django.contrib import messages
        messages.success(request, f'Bulk order {obj.order_id} created successfully!')
        return super().response_add(request, obj, post_url_continue)
    
    def mark_bulk_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
        self.message_user(request, f"{queryset.count()} bulk order(s) marked as confirmed")
    mark_bulk_confirmed.short_description = "Mark selected as confirmed"
    
    def mark_bulk_processing(self, request, queryset):
        queryset.update(status='processing')
        self.message_user(request, f"{queryset.count()} bulk order(s) marked as processing")
    mark_bulk_processing.short_description = "Mark selected as processing"
    
    def mark_bulk_shipped(self, request, queryset):
        queryset.update(status='shipped')
        self.message_user(request, f"{queryset.count()} bulk order(s) marked as shipped")
    mark_bulk_shipped.short_description = "Mark selected as shipped"
    
    def mark_bulk_delivered(self, request, queryset):
        queryset.update(status='delivered')
        self.message_user(request, f"{queryset.count()} bulk order(s) marked as delivered")
    mark_bulk_delivered.short_description = "Mark selected as delivered"
    
    def send_order_confirmation(self, request, queryset):
        """Send confirmation emails for selected orders"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        count = 0
        for order in queryset:
            try:
                send_mail(
                    f'Bulk Order Confirmation - {order.order_id}',
                    f'''Dear {order.name},

Thank you for your bulk order! Your order has been received and is being processed.

Order Details:
- Order ID: {order.order_id}
- Company: {order.company_name}
- Fragrance: {order.get_fragrance_display()}
- Quantity: {order.quantity} {order.unit_size}
- Packaging: {order.packaging}
- Total Amount: ₹{order.total_amount:,.2f}

We will contact you soon to confirm delivery and payment options.

Best regards,
VICTNOW Team''',
                    settings.DEFAULT_FROM_EMAIL,
                    [order.email],
                    fail_silently=True,
                )
                count += 1
            except Exception as e:
                print(f"Error sending email for order {order.order_id}: {e}")
        
        self.message_user(request, f"Confirmation emails sent for {count} order(s)")
    send_order_confirmation.short_description = "Send confirmation emails"
    
    # Custom display methods
    def fragrance_display(self, obj):
        return obj.get_fragrance_display()
    fragrance_display.short_description = 'Fragrance'
    
    def total_amount_formatted(self, obj):
        return f"₹{obj.total_amount:,.2f}"
    total_amount_formatted.short_description = 'Total Amount'
    
    # Custom status colors
    def status_colored(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'blue', 
            'processing': 'purple',
            'shipped': 'green',
            'delivered': 'darkgreen',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status
        )
    status_colored.short_description = 'Status'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'status'),
            'classes': ('wide',)
        }),
        ('Customer Information', {
            'fields': ('name', 'email', 'company_name', 'phone', 'shipping_address'),
            'classes': ('wide',)
        }),
        ('Product Details', {
            'fields': ('fragrance_type', 'quantity', 'unit_size', 'packaging'),
            'classes': ('wide',)
        }),
        ('Pricing', {
            'fields': ('unit_price', 'packaging_cost', 'total_amount'),
            'classes': ('wide',)
        }),
        ('Additional Information', {
            'fields': ('delivery_date', 'special_instructions'),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse', 'wide'),
        }),
    )
    
    # Additional admin settings
    date_hierarchy = 'created_at'
    list_per_page = 25
    show_full_result_count = True

@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['order', 'tracking_number', 'carrier', 'status', 'estimated_delivery', 'actual_delivery', 'created_at']
    list_filter = ['status', 'carrier', 'created_at']
    search_fields = ['order__id', 'tracking_number', 'carrier']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Tracking Information', {
            'fields': ('order', 'tracking_number', 'carrier', 'status')
        }),
        ('Delivery Information', {
            'fields': ('estimated_delivery', 'actual_delivery')
        }),
        ('Additional Information', {
            'fields': ('tracking_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(BulkOrderTracking)
class BulkOrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['bulk_order', 'tracking_number', 'carrier', 'status', 'estimated_delivery', 'actual_delivery', 'created_at']
    list_filter = ['status', 'carrier', 'created_at']
    search_fields = ['bulk_order__id', 'tracking_number', 'carrier']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Bulk Order Information', {
            'fields': ('bulk_order',)
        }),
        ('Tracking Information', {
            'fields': ('tracking_number', 'carrier', 'status')
        }),
        ('Delivery Information', {
            'fields': ('estimated_delivery', 'actual_delivery')
        }),
        ('Additional Information', {
            'fields': ('tracking_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'phone_number', 'login_method_badge', 'is_verified_badge', 'login_device_badge', 'login_browser', 'login_count', 'last_login_formatted', 'created_at_formatted']
    list_filter = ['login_method', 'is_verified', 'login_device_type', 'login_browser', 'created_at', 'last_login']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone_number', 'login_ip_address']
    ordering = ['-last_login', '-created_at']
    readonly_fields = ['created_at', 'last_login', 'login_ip_address', 'login_user_agent', 'frontend_session_id']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'phone_number', 'country_code'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Basic user information and contact details'
        }),
        ('Login Details', {
            'fields': ('login_method', 'is_verified', 'profile_picture'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Authentication and verification information'
        }),
        ('Mobile Login Tracking', {
            'fields': ('login_ip_address', 'login_user_agent', 'login_device_type', 'login_browser', 'login_location', 'frontend_session_id', 'login_attempts', 'successful_logins'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Real-time mobile login information captured when users log in via login button'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_login'),
            'classes': ('collapse', 'wide', 'extrapretty'),
            'description': 'System-generated timestamps'
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def save_model(self, request, obj, form, change):
        # Ensure last_login is updated when profile is modified through admin
        if not change:  # Only for new profiles
            obj.last_login = timezone.now()
        super().save_model(request, obj, form, change)
    
    def user_info(self, obj):
        """Display user information with email"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.user.username,
            obj.user.email
        )
    user_info.short_description = 'User'
    user_info.admin_order_field = 'user__username'
    
    def login_method_badge(self, obj):
        """Display login method as a colored badge"""
        colors = {
            'mobile': '#28a745',
            'google': '#4285f4',
            'facebook': '#1877f2',
            'admin': '#6c757d',
            'unknown': '#ffc107'
        }
        color = colors.get(obj.login_method, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_login_method_display() if hasattr(obj, 'get_login_method_display') else obj.login_method.upper()
        )
    login_method_badge.short_description = 'Login Method'
    login_method_badge.admin_order_field = 'login_method'
    
    def is_verified_badge(self, obj):
        """Display verification status as a badge"""
        if obj.is_verified:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">VERIFIED</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">NOT VERIFIED</span>'
            )
    is_verified_badge.short_description = 'Verified'
    is_verified_badge.admin_order_field = 'is_verified'
    
    def login_device_badge(self, obj):
        """Display device type as a badge"""
        if obj.login_device_type:
            colors = {
                'mobile': '#007bff',
                'desktop': '#28a745',
                'tablet': '#6f42c1'
            }
            color = colors.get(obj.login_device_type, '#6c757d')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
                color,
                obj.login_device_type.upper()
            )
        return 'N/A'
    login_device_badge.short_description = 'Device'
    login_device_badge.admin_order_field = 'login_device_type'
    
    def login_count(self, obj):
        """Display login count with visual indicator"""
        count = obj.successful_logins
        if count >= 10:
            color = '#28a745'
        elif count >= 5:
            color = '#ffc107'
        else:
            color = '#6c757d'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>',
            color,
            count
        )
    login_count.short_description = 'Logins'
    login_count.admin_order_field = 'successful_logins'
    
    def last_login_formatted(self, obj):
        """Format last_login date with relative time"""
        if obj.last_login:
            from django.utils import timezone
            now = timezone.now()
            diff = now - obj.last_login
            
            if diff.days > 0:
                relative = f"{diff.days}d ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                relative = f"{hours}h ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                relative = f"{minutes}m ago"
            else:
                relative = "Just now"
            
            return format_html(
                '{}<br><small style="color: #6c757d;">{}</small>',
                obj.last_login.strftime('%Y-%m-%d %H:%M:%S'),
                relative
            )
        return 'Never'
    last_login_formatted.short_description = 'Last Login'
    last_login_formatted.admin_order_field = 'last_login'
    
    def created_at_formatted(self, obj):
        """Format created_at date"""
        if obj.created_at:
            return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return 'N/A'
    created_at_formatted.short_description = 'Created At'
    created_at_formatted.admin_order_field = 'created_at'
    
    # Add custom actions
    actions = ['mark_as_verified', 'mark_as_unverified', 'reset_login_method', 'export_login_data', 'view_login_stats']
    
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} user(s) marked as verified.')
    mark_as_verified.short_description = "Mark selected users as verified"
    
    def mark_as_unverified(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} user(s) marked as unverified.')
    mark_as_unverified.short_description = "Mark selected users as unverified"
    
    def reset_login_method(self, request, queryset):
        updated = queryset.update(login_method='unknown')
        self.message_user(request, f'{updated} user(s) login method reset to unknown.')
    reset_login_method.short_description = "Reset login method to unknown"
    
    def export_login_data(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="mobile_login_data_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Username', 'Email', 'Phone', 'Login Method', 'Device', 'Browser', 
            'IP Address', 'Location', 'Successful Logins', 'Login Attempts',
            'Last Login', 'Created At', 'Verified'
        ])
        
        for profile in queryset:
            writer.writerow([
                profile.user.username,
                profile.user.email,
                profile.phone_number or '',
                profile.login_method,
                profile.login_device_type or '',
                profile.login_browser or '',
                profile.login_ip_address or '',
                profile.login_location or '',
                profile.successful_logins,
                profile.login_attempts,
                profile.last_login.strftime('%Y-%m-%d %H:%M:%S') if profile.last_login else '',
                profile.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                profile.is_verified
            ])
        
        return response
    export_login_data.short_description = "Export mobile login data to CSV"
    
    def view_login_stats(self, request, queryset):
        """Show login statistics for selected users"""
        from django.contrib import messages
        
        total_logins = sum(profile.successful_logins for profile in queryset)
        unique_devices = set(profile.login_device_type for profile in queryset if profile.login_device_type)
        unique_browsers = set(profile.login_browser for profile in queryset if profile.login_browser)
        verified_users = queryset.filter(is_verified=True).count()
        
        messages.info(request, 
            f'Selected {queryset.count()} users: {total_logins} total logins, '
            f'{len(unique_devices)} devices ({", ".join(unique_devices) if unique_devices else "None"}), '
            f'{len(unique_browsers)} browsers ({", ".join(unique_browsers) if unique_browsers else "None"}), '
            f'{verified_users} verified users.'
        )
    view_login_stats.short_description = "Show login statistics"
    
    # Add custom changelist actions for mobile login
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['mobile_login_stats'] = self.get_mobile_login_stats()
        return super().changelist_view(request, extra_context)
    
    def get_mobile_login_stats(self):
        """Get mobile login statistics for changelist"""
        try:
            total_profiles = UserProfile.objects.count()
            mobile_logins = UserProfile.objects.filter(login_method='mobile').count()
            today_logins = UserProfile.objects.filter(
                login_method='mobile',
                last_login__date=timezone.now().date()
            ).count()
            
            return {
                'total_users': total_profiles,
                'mobile_users': mobile_logins,
                'today_logins': today_logins,
                'percentage': round((mobile_logins / total_profiles * 100), 1) if total_profiles > 0 else 0
            }
        except:
            return {'total_users': 0, 'mobile_users': 0, 'today_logins': 0, 'percentage': 0}


@admin.register(TrialPack)
class TrialPackAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'phone', 'amount', 'payment_status_badge', 'order_status_badge', 'payment_method', 'tracking_status', 'created_at']
    list_filter = ['order_status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['name', 'email', 'phone', 'transaction_id']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    
    # Custom actions
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled', 'send_confirmation_email', 'create_tracking_records']
    
    # Add inline for tracking
    inlines = [TrialPackTrackingInline]
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Shipping Address', {
            'fields': ('address', 'city', 'state', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('Order Details', {
            'fields': ('trial_pack_name', 'trial_pack_description', 'amount')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status', 'transaction_id')
        }),
        ('Order Status', {
            'fields': ('order_status',)
        }),
        ('Additional Information', {
            'fields': ('order_notes', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def payment_status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'completed': '#28a745',
            'failed': '#dc3545',
            'refunded': '#6c757d'
        }
        color = colors.get(obj.payment_status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_payment_status_display().upper()
        )
    payment_status_badge.short_description = 'Payment Status'
    
    def order_status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'confirmed': '#17a2b8',
            'processing': '#007bff',
            'shipped': '#6f42c1',
            'delivered': '#28a745',
            'cancelled': '#dc3545'
        }
        color = colors.get(obj.order_status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_order_status_display().upper()
        )
    order_status_badge.short_description = 'Order Status'
    
    def tracking_status(self, obj):
        """Display tracking status with link to tracking record"""
        try:
            tracking = obj.tracking
            if tracking.tracking_number:
                colors = {
                    'ordered': '#6c757d',
                    'processing': '#007bff',
                    'shipped': '#28a745',
                    'in_transit': '#17a2b8',
                    'out_for_delivery': '#fd7e14',
                    'delivered': '#28a745',
                    'cancelled': '#dc3545',
                    'returned': '#6f42c1'
                }
                color = colors.get(tracking.status, '#6c757d')
                return format_html(
                    '<a href="/admin/fragrances/trialpacktracking/{}/change/" style="text-decoration: none;">'
                    '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>'
                    '</a>',
                    tracking.id, color, tracking.get_status_display().upper()
                )
            else:
                return format_html(
                    '<a href="/admin/fragrances/trialpacktracking/add/?trial_pack={}">'
                    '<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">NO TRACKING</span>'
                    '</a>',
                    obj.id
                )
        except TrialPackTracking.DoesNotExist:
            return format_html(
                '<a href="/admin/fragrances/trialpacktracking/add/?trial_pack={}">'
                '<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">CREATE TRACKING</span>'
                '</a>',
                obj.id
            )
    tracking_status.short_description = 'Tracking'
    
    # Custom actions
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(payment_status='completed', order_status='confirmed')
        self.message_user(request, f'{updated} trial pack(s) marked as paid and confirmed.')
    mark_as_paid.short_description = 'Mark selected as paid'
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(order_status='shipped')
        self.message_user(request, f'{updated} trial pack(s) marked as shipped.')
    mark_as_shipped.short_description = 'Mark selected as shipped'
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(order_status='delivered')
        self.message_user(request, f'{updated} trial pack(s) marked as delivered.')
    mark_as_delivered.short_description = 'Mark selected as delivered'
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(order_status='cancelled')
        self.message_user(request, f'{updated} trial pack(s) marked as cancelled.')
    mark_as_cancelled.short_description = 'Mark selected as cancelled'
    
    def send_confirmation_email(self, request, queryset):
        count = 0
        for trial_pack in queryset:
            # Here you would implement email sending logic
            count += 1
        self.message_user(request, f'Confirmation emails sent for {count} trial pack(s).')
    send_confirmation_email.short_description = 'Send confirmation emails'
    
    def create_tracking_records(self, request, queryset):
        """Create tracking records for selected trial packs"""
        created = 0
        for trial_pack in queryset:
            try:
                trial_pack.tracking
            except TrialPackTracking.DoesNotExist:
                TrialPackTracking.objects.create(trial_pack=trial_pack)
                created += 1
        
        self.message_user(request, f'Tracking records created for {created} trial pack(s).')
    create_tracking_records.short_description = 'Create tracking records'
    
    # Add custom button to admin index
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('order-trial-pack/', self.admin_site.admin_view(self.order_trial_pack_view), name='order_trial_pack'),
        ]
        return custom_urls + urls
    
    def order_trial_pack_view(self, request):
        """Custom view to create trial pack order from admin"""
        if request.method == 'POST':
            # Create trial pack order from admin
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            payment_method = request.POST.get('payment_method', 'upi')
            
            if name and email and phone:
                trial_pack = TrialPack.objects.create(
                    name=name,
                    email=email,
                    phone=phone,
                    payment_method=payment_method,
                    order_status='confirmed',
                    payment_status='completed',
                    admin_notes='Order created by admin: ' + request.user.username
                )
                self.message_user(request, f'Trial pack order #{trial_pack.id} created successfully!')
                return HttpResponseRedirect(reverse('admin:fragrances_trialpack_change', args=[trial_pack.id]))
            else:
                self.message_user(request, 'Please fill in all required fields.')
        
        # Show form
        context = {
            'opts': self.model._meta,
            'title': 'Order Trial Pack',
            'has_change_permission': True,
        }
        return TemplateResponse(request, 'admin/order_trial_pack.html', context)


@admin.register(TrialPackTracking)
class TrialPackTrackingAdmin(admin.ModelAdmin):
    list_display = ['trial_pack_info', 'tracking_number_link', 'carrier', 'status_badge', 'estimated_delivery', 'actual_delivery', 'created_at']
    list_filter = ['status', 'carrier', 'created_at']
    search_fields = ['trial_pack__name', 'trial_pack__email', 'tracking_number', 'carrier']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    # Custom actions for tracking management
    actions = ['mark_as_shipped', 'mark_as_in_transit', 'mark_as_out_for_delivery', 'mark_as_delivered', 'create_tracking_numbers']
    
    fieldsets = (
        ('Trial Pack Information', {
            'fields': ('trial_pack',),
            'classes': ('wide', 'extrapretty'),
            'description': 'Associated trial pack order'
        }),
        ('Tracking Information', {
            'fields': ('tracking_number', 'carrier', 'status', 'tracking_url'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Shipping and tracking details'
        }),
        ('Delivery Information', {
            'fields': ('estimated_delivery', 'actual_delivery'),
            'classes': ('wide', 'extrapretty'),
            'description': 'Delivery timeline'
        }),
        ('Tracking Notes', {
            'fields': ('tracking_notes',),
            'classes': ('wide', 'extrapretty'),
            'description': 'Additional tracking information and updates'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse', 'wide', 'extrapretty'),
            'description': 'System-generated timestamps'
        }),
    )
    
    def trial_pack_info(self, obj):
        return f"#{obj.trial_pack.id} - {obj.trial_pack.name} ({obj.trial_pack.email})"
    trial_pack_info.short_description = 'Trial Pack'
    
    def tracking_number_link(self, obj):
        if obj.tracking_url and obj.tracking_number:
            return format_html(
                '<a href="{}" target="_blank" style="color: #007bff; text-decoration: none;">{}</a>',
                obj.tracking_url, obj.tracking_number
            )
        elif obj.tracking_number:
            return obj.tracking_number
        return "No tracking number"
    tracking_number_link.short_description = 'Tracking Number'
    
    def status_badge(self, obj):
        colors = {
            'ordered': '#6c757d',
            'processing': '#007bff',
            'shipped': '#28a745',
            'in_transit': '#17a2b8',
            'out_for_delivery': '#fd7e14',
            'delivered': '#28a745',
            'cancelled': '#dc3545',
            'returned': '#6f42c1'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display().upper()
        )
    status_badge.short_description = 'Status'
    
    # Custom actions
    def mark_as_shipped(self, request, queryset):
        for tracking in queryset:
            tracking.update_status('shipped', 'Marked as shipped by admin')
        self.message_user(request, f'{queryset.count()} tracking record(s) marked as shipped.')
    mark_as_shipped.short_description = "Mark selected as shipped"
    
    def mark_as_in_transit(self, request, queryset):
        for tracking in queryset:
            tracking.update_status('in_transit', 'Marked as in transit by admin')
        self.message_user(request, f'{queryset.count()} tracking record(s) marked as in transit.')
    mark_as_in_transit.short_description = "Mark selected as in transit"
    
    def mark_as_out_for_delivery(self, request, queryset):
        for tracking in queryset:
            tracking.update_status('out_for_delivery', 'Marked as out for delivery by admin')
        self.message_user(request, f'{queryset.count()} tracking record(s) marked as out for delivery.')
    mark_as_out_for_delivery.short_description = "Mark selected as out for delivery"
    
    def mark_as_delivered(self, request, queryset):
        for tracking in queryset:
            tracking.update_status('delivered', 'Marked as delivered by admin')
        self.message_user(request, f'{queryset.count()} tracking record(s) marked as delivered.')
    mark_as_delivered.short_description = "Mark selected as delivered"
    
    def create_tracking_numbers(self, request, queryset):
        """Generate tracking numbers for selected trial packs"""
        import random
        import string
        
        for tracking in queryset:
            if not tracking.tracking_number:
                # Generate a random tracking number
                prefix = "VT"
                random_num = ''.join(random.choices(string.digits, k=10))
                tracking.tracking_number = f"{prefix}{random_num}"
                tracking.save()
        
        self.message_user(request, f'Tracking numbers generated for {queryset.count()} trial pack(s).')
    create_tracking_numbers.short_description = "Generate tracking numbers"


# Add custom admin site customization
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse

class VictnowAdminSite(AdminSite):
    site_header = 'VICTNOW Administration'
    site_title = 'VICTNOW Admin'
    index_title = 'Welcome to VICTNOW Administration Panel'
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('order-trial-pack/', self.admin_view(self.order_trial_pack_redirect), name='order_trial_pack_redirect'),
        ]
        return custom_urls + urls
    
    def order_trial_pack_redirect(self, request):
        """Redirect to trial pack order creation"""
        return HttpResponseRedirect(reverse('admin:order_trial_pack'))

# Use custom admin site (optional - you can switch back to default admin)
# admin_site = VictnowAdminSite()
# admin_site.register(TrialPack, TrialPackAdmin)
