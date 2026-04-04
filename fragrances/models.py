from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum


def get_client_ip(request):
    """Get client IP address from request"""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class UserProfile(models.Model):
    LOGIN_METHODS = [
        ('mobile', 'Mobile OTP'),
        ('google', 'Google OAuth'),
        ('facebook', 'Facebook OAuth'),
        ('standard', 'Standard Registration'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    country_code = models.CharField(max_length=10, default='+91')
    login_method = models.CharField(max_length=20, choices=LOGIN_METHODS, default='mobile')
    profile_picture = models.URLField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    last_login = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Registration information fields
    registration_ip_address = models.GenericIPAddressField(blank=True, null=True, help_text="IP address from which user registered")
    registration_user_agent = models.TextField(blank=True, null=True, help_text="Browser/device information from registration")
    registration_device_type = models.CharField(max_length=50, blank=True, null=True, help_text="Device type used for registration")
    registration_browser = models.CharField(max_length=100, blank=True, null=True, help_text="Browser used for registration")
    registration_location = models.CharField(max_length=200, blank=True, null=True, help_text="Location from which user registered")
    
    # Frontend login tracking fields
    login_ip_address = models.GenericIPAddressField(blank=True, null=True, help_text="IP address from which user logged in")
    login_user_agent = models.TextField(blank=True, null=True, help_text="Browser/device information from login")
    login_device_type = models.CharField(max_length=50, blank=True, null=True, help_text="Device type (mobile, desktop, tablet)")
    login_browser = models.CharField(max_length=100, blank=True, null=True, help_text="Browser used for login")
    login_location = models.CharField(max_length=200, blank=True, null=True, help_text="Location from which user logged in")
    frontend_session_id = models.CharField(max_length=100, blank=True, null=True, help_text="Frontend session identifier")
    login_attempts = models.PositiveIntegerField(default=0, help_text="Number of login attempts")
    successful_logins = models.PositiveIntegerField(default=0, help_text="Number of successful logins")
    
    def __str__(self):
        return f"{self.user.username} - {self.login_method}"
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('men', 'Men'),
        ('women', 'Women'),
        ('unisex', 'Unisex'),
    ]
    
    SIZE_CHOICES = [
        ('50ml', '50ml'),
        ('100ml', '100ml'),
        ('30ml', '30ml'),
    ]
    
    STOCK_STATUS_CHOICES = [
        ('in_stock', 'In Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('limited', 'Limited Stock'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='unisex')
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='50ml')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    featured = models.BooleanField(default=False)
    stock_status = models.CharField(max_length=20, choices=STOCK_STATUS_CHOICES, default='in_stock')
    stock_quantity = models.PositiveIntegerField(default=10, help_text="Number of items in stock")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    @property
    def available(self):
        """Check if product is available for purchase (property for template usage)"""
        return self.stock_status != 'out_of_stock'
    
    def is_available(self):
        """Check if product is available for purchase"""
        return self.stock_status != 'out_of_stock'
    
    def get_stock_display(self):
        """Get user-friendly stock display"""
        if self.stock_status == 'in_stock':
            return f"In Stock ({self.stock_quantity} available)"
        elif self.stock_status == 'limited':
            return f"Limited Stock ({self.stock_quantity} left)"
        else:
            return "Out of Stock"

class Testimonial(models.Model):
    client_name = models.CharField(max_length=100)
    client_title = models.CharField(max_length=100)
    content = models.TextField()
    rating = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.client_name} - {self.client_title}"

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='blog/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.subject}"

class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.email

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    # User Information (optional - for guest orders it can be null)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    # Customer Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Shipping Information
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    
    # Order Details
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment Information
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Order Status
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    
    # Additional Information
    order_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

class CorporateOrder(models.Model):
    """Corporate bulk orders"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    FRAGRANCE_CHOICES = [
        ('victnow_forge', 'VICTNOW FORGE'),
        ('victnow_muse', 'VICTNOW MUSE'),
        ('victnow_nexus', 'VICTNOW NEXUS'),
        ('mixed_collection', 'Mixed Collection'),
        ('custom', 'Custom Mix'),
    ]
    
    UNIT_SIZE_CHOICES = [
        ('50ml', '50ml'),
        ('100ml', '100ml'),
        ('custom', 'Custom Size'),
    ]
    
    PACKAGING_CHOICES = [
        ('standard', 'Standard Box'),
        ('premium', 'Premium Gift Box'),
        ('custom', 'Custom Branding'),
    ]
    
    # Order Information
    order_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    
    # User Information (optional - for guest orders it can be null)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='corporate_orders')
    
    # Customer Information
    name = models.CharField(max_length=100, blank=True, null=True)  # Full name
    email = models.EmailField()
    company_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    
    # Product Details
    fragrance_type = models.CharField(max_length=20, choices=FRAGRANCE_CHOICES)
    quantity = models.IntegerField()
    unit_size = models.CharField(max_length=10, choices=UNIT_SIZE_CHOICES, default='50ml', blank=True, null=True)
    packaging = models.CharField(max_length=10, choices=PACKAGING_CHOICES, default='standard', blank=True, null=True)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=2999.00, blank=True, null=True)
    packaging_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Additional Information
    delivery_date = models.DateField(blank=True, null=True)
    special_instructions = models.TextField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Bulk Order #{self.order_id} - {self.company_name}"
    
    def get_fragrance_display(self):
        return dict(self.FRAGRANCE_CHOICES).get(self.fragrance_type, self.fragrance_type)
    
    def save(self, *args, **kwargs):
        # Calculate total amount if not set
        if not self.total_amount:
            self.total_amount = (self.unit_price + self.packaging_cost) * self.quantity
        super().save(*args, **kwargs)

class OrderTracking(models.Model):
    """Order tracking information"""
    TRACKING_STATUS_CHOICES = [
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('exception', 'Delivery Exception'),
        ('returned', 'Returned'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='tracking')
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    carrier = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=TRACKING_STATUS_CHOICES, blank=True, null=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    actual_delivery = models.DateField(blank=True, null=True)
    tracking_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Tracking #{self.order.id} - {self.tracking_number or 'No tracking'}"

class BulkOrderTracking(models.Model):
    """Bulk order tracking information"""
    TRACKING_STATUS_CHOICES = [
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('exception', 'Delivery Exception'),
        ('returned', 'Returned'),
    ]
    
    bulk_order = models.OneToOneField(CorporateOrder, on_delete=models.CASCADE, related_name='bulk_tracking')
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    carrier = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=TRACKING_STATUS_CHOICES, blank=True, null=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    actual_delivery = models.DateField(blank=True, null=True)
    tracking_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Bulk Tracking #{self.bulk_order.id} - {self.tracking_number or 'No tracking'}"


class TrialPack(models.Model):
    """Trial Pack orders for VICTNOW trial pack"""
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('upi', 'UPI'),
        ('card', 'Credit/Debit Card'),
        ('netbanking', 'Net Banking'),
        ('wallet', 'Digital Wallet'),
    ]
    
    # User Information (optional - for guest orders it can be null)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='trial_packs')
    
    # Customer Information
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Address Information
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Order Details
    trial_pack_name = models.CharField(max_length=200, default="VICTNOW Trial Pack")
    trial_pack_description = models.TextField(default="VICTNOW MUSE, VICTNOW NEXUS, VICTNOW FORGE - 5ML each")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=2499.00)
    
    # Payment Information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='upi')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Order Status
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    
    # Additional Information
    order_notes = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Trial Pack Order"
        verbose_name_plural = "Trial Pack Orders"
    
    def __str__(self):
        return f"Trial Pack #{self.id} - {self.name}"
    
    def get_absolute_url(self):
        return reverse('admin:fragrances_trialpack_change', args=[self.id])
    
    def get_admin_link(self):
        return f'<a href="/admin/fragrances/trialpack/{self.id}/change/" target="_blank">View Order</a>'
    
    def mark_as_paid(self):
        """Mark trial pack as paid"""
        self.payment_status = 'completed'
        self.order_status = 'confirmed'
        self.save()
    
    def mark_as_shipped(self):
        """Mark trial pack as shipped"""
        self.order_status = 'shipped'
        self.save()
    
    def mark_as_delivered(self):
        """Mark trial pack as delivered"""
        self.order_status = 'delivered'
        self.save()


class TrialPackTracking(models.Model):
    """Tracking information for Trial Pack orders"""
    TRACKING_STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    
    CARRIER_CHOICES = [
        ('delhivery', 'Delhivery'),
        ('fedex', 'FedEx'),
        ('dhl', 'DHL'),
        ('bluedart', 'Blue Dart'),
        ('xpressbees', 'Xpressbees'),
        ('ekart', 'Ekart'),
        ('india_post', 'India Post'),
        ('other', 'Other'),
    ]
    
    trial_pack = models.OneToOneField(TrialPack, on_delete=models.CASCADE, related_name='tracking')
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    carrier = models.CharField(max_length=20, choices=CARRIER_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=20, choices=TRACKING_STATUS_CHOICES, default='ordered')
    
    # Delivery Information
    estimated_delivery = models.DateTimeField(blank=True, null=True)
    actual_delivery = models.DateTimeField(blank=True, null=True)
    
    # Tracking Details
    tracking_url = models.URLField(blank=True, null=True)
    tracking_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Trial Pack Tracking"
        verbose_name_plural = "Trial Pack Tracking"
    
    def __str__(self):
        if self.tracking_number:
            return f"Tracking #{self.tracking_number} - {self.trial_pack.name}"
        return f"Tracking for Trial Pack #{self.trial_pack.id}"
    
    def get_tracking_link(self):
        if self.tracking_url and self.tracking_number:
            return f'<a href="{self.tracking_url}" target="_blank">{self.tracking_number}</a>'
        elif self.tracking_number:
            return self.tracking_number
        return "No tracking number"
    
    def update_status(self, new_status, notes=None):
        """Update tracking status with optional notes"""
        self.status = new_status
        if notes:
            if self.tracking_notes:
                self.tracking_notes += f"\n\n{timezone.now().strftime('%Y-%m-%d %H:%M')}: {notes}"
            else:
                self.tracking_notes = f"{timezone.now().strftime('%Y-%m-%d %H:%M')}: {notes}"
        self.save()
        
        # Update trial pack status if delivered
        if new_status == 'delivered':
            self.trial_pack.order_status = 'delivered'
            self.trial_pack.actual_delivery = timezone.now()
            self.trial_pack.save()


class UserActivity(models.Model):
    """Track user activities and history"""
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('order_created', 'Order Created'),
        ('trial_pack_created', 'Trial Pack Created'),
        ('corporate_order_created', 'Corporate Order Created'),
        ('profile_updated', 'Profile Updated'),
        ('password_changed', 'Password Changed'),
        ('product_viewed', 'Product Viewed'),
        ('cart_updated', 'Cart Updated'),
        ('payment_completed', 'Payment Completed'),
        ('review_submitted', 'Review Submitted'),
        ('contact_submitted', 'Contact Form Submitted'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Related object information (optional)
    content_type = models.CharField(max_length=100, blank=True, null=True, help_text="Type of related object (e.g., 'Order', 'TrialPack')")
    object_id = models.PositiveIntegerField(blank=True, null=True, help_text="ID of related object")
    object_repr = models.CharField(max_length=200, blank=True, null=True, help_text="String representation of related object")
    
    # Additional metadata
    metadata = models.JSONField(blank=True, null=True, help_text="Additional activity data as JSON")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def log_activity(cls, user, activity_type, description=None, request=None, content_type=None, object_id=None, object_repr=None, metadata=None):
        """Log a user activity"""
        activity = cls.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            ip_address=get_client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else '',
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr,
            metadata=metadata
        )
        return activity


class Cart(models.Model):
    """User-specific cart items"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'product']  # Ensure one cart item per product per user
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'product']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} × {self.quantity}"
    
    def get_total_price(self):
        return self.product.price * self.quantity
    
    @classmethod
    def get_user_cart(cls, user):
        """Get all cart items for a user"""
        return cls.objects.filter(user=user)
    
    @classmethod
    def add_to_cart(cls, user, product, quantity=1):
        """Add or update cart item for user"""
        cart_item, created = cls.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        return cart_item
    
    @classmethod
    def remove_from_cart(cls, user, product):
        """Remove cart item for user"""
        try:
            cart_item = cls.objects.get(user=user, product=product)
            cart_item.delete()
            return True
        except cls.DoesNotExist:
            return False
    
    @classmethod
    def update_quantity(cls, user, product, quantity):
        """Update cart item quantity"""
        if quantity <= 0:
            return cls.remove_from_cart(user, product)
        
        cart_item, created = cls.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity = quantity
            cart_item.save()
        return cart_item
    
    @classmethod
    def clear_user_cart(cls, user):
        """Clear all cart items for a user"""
        cls.objects.filter(user=user).delete()
    
    @classmethod
    def get_cart_count(cls, user):
        """Get total number of items in user's cart"""
        return cls.objects.filter(user=user).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    @classmethod
    def get_cart_total(cls, user):
        """Get total price of all items in user's cart"""
        total = 0
        for item in cls.objects.filter(user=user):
            total += item.get_total_price()
        return total
