from django.urls import path
from . import views
from . import views_trial
from . import views_direct_login
from . import views_auth
from . import views_fast2sms
from . import views_db_viewer
from . import views_razorpay
from . import views_fixed_razorpay

urlpatterns = [
    path('', views.home, name='home'),
    path('collection/', views.collection, name='collection'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart, name='cart'),
    path('cart-view/', views.cart_view, name='cart_view'),  # Cart view without authentication
    path('cart_checkout/', views.cart_checkout, name='cart_checkout'),
    path('checkout/', views.checkout, name='checkout'),  # Cart checkout
    path('customer_details/', views.customer_details, name='customer_details'),
    path('api/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('api/remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('api/update-cart-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('api/get-cart-info/', views.get_cart_info, name='get_cart_info'),
    path('checkout-complete/', views.checkout_complete, name='checkout_complete'),
    path('about/', views.about, name='about'),
    path('about-victnow-luxury/', views.about_victnow_luxury, name='about_victnow_luxury'),
    path('privacy/', views.privacy, name='privacy'),
    path('contact/', views.contact, name='contact'),
    path('reviews/', views.reviews, name='reviews'),
    path('corporate-gifting/', views.corporate_gifting, name='corporate_gifting'),
    path('trail_customer/', views.trail_customer, name='trail_customer'),
    path('bulk_customer/', views.bulk_customer, name='bulk_customer'),
    path('bulk-order-process/', views.bulk_order_process, name='bulk_order_process'),
    path('test-bulk/', views.test_bulk_order, name='test_bulk_order'),  # Test endpoint
    path('ping/', views.ping_test, name='ping_test'),  # Simple ping test
    path('track-bulk-order/', views.track_bulk_order, name='track_bulk_order'),  # Bulk order tracking
    path('test-db/', views.test_database, name='test_database'),  # Database test
    path('test-bulk-simple/', views.test_bulk_simple, name='test_bulk_simple'),  # Simple bulk test
    path('test-admin-integration/', views.test_admin_integration, name='test_admin_integration'),  # Admin integration test
    path('newsletter/', views.newsletter, name='newsletter'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('orders/', views.orders, name='orders'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    
    # Order Management URLs
    path('api/save-order/', views.save_order, name='save_order'),
    path('order-success/', views.order_success, name='order_success'),
    
    # Direct Login URLs
    path('api/direct-mobile-login/', views_direct_login.direct_mobile_login, name='direct_mobile_login'),
    path('api/complete-user-profile/', views_direct_login.complete_user_profile, name='complete_user_profile'),
    path('api/quick-login/', views_direct_login.quick_login_with_phone, name='quick_login_with_phone'),
    path('api/verify-quick-login/', views_direct_login.verify_quick_login, name='verify_quick_login'),
    path('api/login-stats/', views_direct_login.get_login_stats, name='get_login_stats'),
    
    # New Authentication URLs (UserProfile-based)
    path('api/auth/login/', views_auth.authenticate_user, name='authenticate_user'),
    path('api/auth/register/', views_auth.register_user_with_profile, name='register_user_with_profile'),
    path('api/auth/users/', views_auth.get_user_profiles, name='get_user_profiles'),
    
    # Fast2SMS API URLs
    path('send-otp-via-fast2sms/', views_fast2sms.send_otp_via_fast2sms, name='send_otp_via_fast2sms'),
    path('verify-otp-firebase/', views_fast2sms.verify_otp_firebase, name='verify_otp_firebase'),
    path('fast2sms-config/', views_fast2sms.fast2sms_config_info, name='fast2sms_config_info'),
    
    # Trial Pack URLs
    path('create-trial-pack/', views_trial.create_trial_pack, name='create_trial_pack'),
    path('update-trial-pack-payment/', views_trial.update_trial_pack_payment, name='update_trial_pack_payment'),
    path('api/trial-pack-orders/', views_trial.trial_pack_orders_list, name='trial_pack_orders_list'),
    
    # User Registration URLs
    path('api/send-otp/', views.send_real_otp, name='send_real_otp'),
    path('api/verify-otp/', views.verify_real_otp, name='verify_real_otp'),
    path('api/register/mobile/', views.register_user_with_mobile, name='register_user_with_mobile'),
    path('api/register/social/', views.register_user_with_social, name='register_user_with_social'),
    
    # Database Viewer URLs
    path('db-viewer/', views_db_viewer.database_viewer, name='database_viewer'),
    path('api/db/<str:table_name>/', views_db_viewer.table_data_api, name='table_data_api'),
    
    # Dynamic Razorpay Payment URLs
    path('api/create-razorpay-order/', views_razorpay.create_razorpay_order, name='create_razorpay_order'),
    path('api/verify-razorpay-payment/', views_razorpay.verify_razorpay_payment, name='verify_razorpay_payment'),
    path('payment-success/', views_razorpay.payment_success, name='payment_success'),
    
    # FIXED Razorpay Payment URLs (USE THESE)
    path('api/create-order/', views_fixed_razorpay.create_razorpay_order_fixed, name='create_razorpay_order_fixed'),
    path('api/verify-payment/', views_fixed_razorpay.verify_razorpay_payment_fixed, name='verify_razorpay_payment_fixed'),
    path('payment-success-fixed/', views_fixed_razorpay.payment_success_fixed, name='payment_success_fixed'),
    
    # Demo Page
    path('dynamic-payment-demo/', views.dynamic_payment_demo, name='dynamic_payment_demo'),
    path('decimal-price-demo/', views.decimal_price_demo, name='decimal_price_demo'),
    
    # Fixed Razorpay Test Page
    path('fixed-razorpay-test/', views.fixed_razorpay_test, name='fixed_razorpay_test'),
]
