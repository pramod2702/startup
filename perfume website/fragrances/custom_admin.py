from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.contrib import messages
from django.shortcuts import render
from .models import Product, Testimonial, BlogPost, ContactMessage, Newsletter, Order, CorporateOrder, OrderTracking, BulkOrderTracking

class CustomAdminSite(admin.AdminSite):
    site_header = "VICTNOW Admin Panel"
    site_title = "VICTNOW Administration"
    index_template = "admin/admin_dashboard.html"
    
    def index(self, request, extra_context=None):
        # Get bulk order statistics
        bulk_orders = CorporateOrder.objects.count()
        pending_orders = CorporateOrder.objects.filter(status='pending').count()
        shipped_orders = CorporateOrder.objects.filter(status='shipped').count()
        bulk_revenue = sum(order.total_amount for order in CorporateOrder.objects.all())
        
        context = {
            **(extra_context or {}),
            'bulk_orders': bulk_orders,
            'pending_orders': pending_orders,
            'shipped_orders': shipped_orders,
            'bulk_revenue': bulk_revenue,
            'title': self.index_title or self.site_title,
        }
        
        return TemplateResponse(request, self.index_template or 'admin/index.html', context)

# Create custom admin site
custom_admin_site = CustomAdminSite(name='custom_admin')

@admin.register(Product, site=custom_admin_site)
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

@admin.register(Testimonial, site=custom_admin_site)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'client_title', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['client_name', 'content']

@admin.register(BlogPost, site=custom_admin_site)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'content']
    ordering = ['-created_at']

@admin.register(ContactMessage, site=custom_admin_site)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email', 'subject']
    ordering = ['-created_at']

@admin.register(Newsletter, site=custom_admin_site)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'created_at']
    ordering = ['-created_at']

@admin.register(Order, site=custom_admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'product_name', 'quantity', 'total_amount', 'order_status', 'payment_status', 'created_at']
    list_filter = ['order_status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'product__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    # Add actions for order management
    actions = ['mark_as_shipped', 'mark_as_delivered', 'mark_as_processing']
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(order_status='shipped')
        self.message_user(request, f"{updated} orders marked as shipped.", messages.SUCCESS)
    mark_as_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(order_status='delivered')
        self.message_user(request, f"{updated} orders marked as delivered.", messages.SUCCESS)
    mark_as_delivered.short_description = "Mark selected orders as delivered"
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(order_status='processing')
        self.message_user(request, f"{updated} orders marked as processing.", messages.SUCCESS)
    mark_as_processing.short_description = "Mark selected orders as processing"
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Shipping Information', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Order Details', {
            'fields': ('product', 'quantity', 'product_price', 'shipping_cost', 'total_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('Order Status', {
            'fields': ('order_status',)
        }),
        ('Additional Information', {
            'fields': ('order_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_name(self, obj):
        return obj.get_full_name()
    customer_name.short_description = 'Customer'
    
    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'

@admin.register(CorporateOrder, site=custom_admin_site)
class CorporateOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'company_name', 'name', 'email', 'fragrance_type', 'quantity', 'status', 'created_at']
    list_filter = ['status', 'fragrance_type', 'created_at']
    search_fields = ['company_name', 'name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    # Add actions for bulk order management
    actions = ['mark_bulk_confirmed', 'mark_bulk_processing', 'mark_bulk_shipped', 'mark_bulk_delivered']
    
    def mark_bulk_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f"{updated} bulk orders confirmed.", messages.SUCCESS)
    mark_bulk_confirmed.short_description = "Mark selected bulk orders as confirmed"
    
    def mark_bulk_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f"{updated} bulk orders marked as processing.", messages.SUCCESS)
    mark_bulk_processing.short_description = "Mark selected bulk orders as processing"
    
    def mark_bulk_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f"{updated} bulk orders shipped.", messages.SUCCESS)
    mark_bulk_shipped.short_description = "Mark selected bulk orders as shipped"
    
    def mark_bulk_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f"{updated} bulk orders delivered.", messages.SUCCESS)
    mark_bulk_delivered.short_description = "Mark selected bulk orders as delivered"
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('company_name', 'name', 'email', 'phone')
        }),
        ('Order Details', {
            'fields': ('fragrance_type', 'quantity', 'special_requirements')
        }),
        ('Status Management', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(OrderTracking, site=custom_admin_site)
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

@admin.register(BulkOrderTracking, site=custom_admin_site)
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
