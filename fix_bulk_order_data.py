#!/usr/bin/env python
"""
Fix data integrity issues for old bulk orders
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blissme_project.settings')
django.setup()

from fragrances.models import CorporateOrder
import time

def fix_bulk_order_data():
    """Fix data integrity issues for old bulk orders"""
    print("=== Fixing Bulk Order Data Integrity Issues ===")
    
    # Get all bulk orders with missing order_id or total_amount
    problematic_orders = CorporateOrder.objects.filter(
        models.Q(order_id__isnull=True) | 
        models.Q(order_id='') | 
        models.Q(total_amount__isnull=True) |
        models.Q(total_amount=0)
    )
    
    print(f"Found {problematic_orders.count()} orders with data issues")
    
    fixed_count = 0
    for order in problematic_orders:
        print(f"\n--- Processing Order ID: {order.id} ---")
        print(f"Current data:")
        print(f"  - Order ID: {order.order_id}")
        print(f"  - Company: {order.company_name}")
        print(f"  - Email: {order.email}")
        print(f"  - Quantity: {order.quantity}")
        print(f"  - Unit Price: {order.unit_price}")
        print(f"  - Packaging Cost: {order.packaging_cost}")
        print(f"  - Total Amount: {order.total_amount}")
        
        # Fix missing order_id
        if not order.order_id:
            import time
            order.order_id = f"BULK_FIXED_{int(time.time())}_{order.id}"
            print(f"  ✅ Fixed order_id: {order.order_id}")
        
        # Fix missing total_amount
        if not order.total_amount or order.total_amount == 0:
            # Use default pricing if unit_price is missing
            unit_price = order.unit_price if order.unit_price else 2999
            packaging_cost = order.packaging_cost if order.packaging_cost else 0
            quantity = order.quantity if order.quantity else 1
            
            order.total_amount = (unit_price + packaging_cost) * quantity
            print(f"  ✅ Fixed total_amount: {order.total_amount}")
        
        # Fix missing unit_price
        if not order.unit_price or order.unit_price == 0:
            order.unit_price = 2999
            print(f"  ✅ Fixed unit_price: {order.unit_price}")
        
        # Save the order
        order.save()
        fixed_count += 1
        print(f"  ✅ Order saved successfully")
    
    print(f"\n=== Summary ===")
    print(f"Fixed {fixed_count} bulk orders")
    
    # Verify all orders now have valid data
    remaining_issues = CorporateOrder.objects.filter(
        models.Q(order_id__isnull=True) | 
        models.Q(order_id='') | 
        models.Q(total_amount__isnull=True) |
        models.Q(total_amount=0)
    )
    
    if remaining_issues.count() == 0:
        print("✅ All bulk orders now have valid data!")
    else:
        print(f"❌ Still have {remaining_issues.count()} orders with issues")
    
    # Show final statistics
    total_orders = CorporateOrder.objects.count()
    print(f"\n=== Final Bulk Order Statistics ===")
    print(f"Total bulk orders: {total_orders}")
    print(f"Orders with valid order_id: {CorporateOrder.objects.exclude(order_id__isnull=True).exclude(order_id='').count()}")
    print(f"Orders with valid total_amount: {CorporateOrder.objects.exclude(total_amount__isnull=True).exclude(total_amount=0).count()}")
    
    # Show recent orders
    recent_orders = CorporateOrder.objects.order_by('-created_at')[:5]
    print(f"\nRecent 5 bulk orders:")
    for order in recent_orders:
        print(f"  - {order.order_id}: {order.company_name} - {order.quantity} units - ₹{order.total_amount} ({order.status})")

if __name__ == '__main__':
    print("Starting Bulk Order Data Fix...")
    print("=" * 50)
    
    # Import models here to avoid circular imports
    from django.db import models
    
    fix_bulk_order_data()
    
    print("\n" + "=" * 50)
    print("Data fix completed!")
