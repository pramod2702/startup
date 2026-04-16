from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Product, Testimonial, BlogPost, ContactMessage, Newsletter, Order, CorporateOrder, OrderTracking, BulkOrderTracking, UserProfile, TrialPack, TrialPackTracking, TrialPackPrice, UserActivity

# Simple Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'featured', 'created_at']
    list_filter = ['featured', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

# Simple Testimonial Admin
@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['client_name', 'content']

# Simple BlogPost Admin
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'content']
    ordering = ['-created_at']

# Simple ContactMessage Admin
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email', 'subject']
    ordering = ['-created_at']

# Simple Newsletter Admin
@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'created_at']
    ordering = ['-created_at']

# Simple Order Admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'product_name', 'total_amount', 'order_status', 'payment_status', 'created_at']
    list_filter = ['order_status', 'payment_status', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']
    ordering = ['-created_at']
    
    def customer_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    customer_name.short_description = 'Customer'
    
    def product_name(self, obj):
        return obj.product.name if obj.product else 'N/A'
    product_name.short_description = 'Product'

# Simple CorporateOrder Admin
@admin.register(CorporateOrder)
class CorporateOrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'company_name', 'name', 'email', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_id', 'company_name', 'name', 'email']
    ordering = ['-created_at']

# Simple OrderTracking Admin
@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['order', 'tracking_number', 'carrier', 'status', 'created_at']
    list_filter = ['status', 'carrier', 'created_at']
    search_fields = ['tracking_number', 'carrier']
    ordering = ['-created_at']

# Simple BulkOrderTracking Admin
@admin.register(BulkOrderTracking)
class BulkOrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['bulk_order', 'tracking_number', 'carrier', 'status', 'created_at']
    list_filter = ['status', 'carrier', 'created_at']
    search_fields = ['tracking_number', 'carrier']
    ordering = ['-created_at']

# Simple UserProfile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_email', 'phone_number', 'login_method', 'is_verified', 'created_at']
    list_filter = ['login_method', 'is_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number']
    ordering = ['-created_at']
    
    def user_email(self, obj):
        return obj.user.email if obj.user.email else 'No Email'
    user_email.short_description = 'Email'

# Simple TrialPackPrice Admin
@admin.register(TrialPackPrice)
class TrialPackPriceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        # Log price changes
        if change:
            try:
                old_obj = TrialPackPrice.objects.get(pk=obj.pk)
                if old_obj.price != obj.price:
                    from django.contrib.admin.models import LogEntry
                    LogEntry.objects.log_action(
                        user_id=request.user.id,
                        content_type_id=None,
                        object_id=str(obj.pk),
                        object_repr=str(obj),
                        action_flag=2,  # CHANGE
                        change_message=f'Price changed from ₹{old_obj.price} to ₹{obj.price}'
                    )
            except TrialPackPrice.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)

# Simple TrialPack Admin
@admin.register(TrialPack)
class TrialPackAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'trial_pack_name', 'amount', 'order_status', 'created_at']
    list_filter = ['order_status', 'payment_method', 'created_at']
    search_fields = ['name', 'email', 'phone', 'trial_pack_name']
    ordering = ['-created_at']
    
    def product_name(self, obj):
        return obj.trial_pack_name or 'Trial Pack'
    product_name.short_description = 'Product'

# Simple TrialPackTracking Admin
@admin.register(TrialPackTracking)
class TrialPackTrackingAdmin(admin.ModelAdmin):
    list_display = ['trial_pack', 'tracking_number', 'carrier', 'status', 'created_at']
    list_filter = ['status', 'carrier', 'created_at']
    search_fields = ['tracking_number', 'carrier']
    ordering = ['-created_at']

# Simple UserActivity Admin
@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'created_at']
    list_filter = ['created_at', 'activity_type']
    search_fields = ['user__username', 'activity_type']
    ordering = ['-created_at']
admin.site.site_header = "VICTNOW Administration"
admin.site.site_title = "VICTNOW Admin"
admin.site.index_title = "Welcome to VICTNOW Admin Panel"
