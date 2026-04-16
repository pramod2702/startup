from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import Order, CorporateOrder, ContactMessage, Newsletter, UserProfile, TrialPack

@staff_member_required
def admin_stats_api(request):
    """API endpoint for admin dashboard statistics"""
    try:
        # Get date ranges
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        
        # Order statistics
        total_orders = Order.objects.count()
        bulk_orders = CorporateOrder.objects.count()
        trial_packs = TrialPack.objects.count()
        shipped_orders = Order.objects.filter(order_status='shipped').count() + \
                         CorporateOrder.objects.filter(status='shipped').count()
        
        # Revenue calculation
        total_revenue = Order.objects.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        bulk_revenue = CorporateOrder.objects.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        trial_revenue = TrialPack.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        revenue = total_revenue + bulk_revenue + trial_revenue
        
        # Monthly comparison
        this_month_orders = Order.objects.filter(created_at__gte=this_month_start).count()
        last_month_orders = Order.objects.filter(
            created_at__gte=last_month_start,
            created_at__lt=this_month_start
        ).count()
        
        # Recent activity
        recent_orders = Order.objects.select_related('product').order_by('-created_at')[:5]
        recent_bulk_orders = CorporateOrder.objects.order_by('-created_at')[:5]
        recent_trial_packs = TrialPack.objects.order_by('-created_at')[:3]
        recent_messages = ContactMessage.objects.order_by('-created_at')[:3]
        
        # Activity list
        activities = []
        
        # Add recent orders to activity
        for order in recent_orders:
            activities.append({
                'icon': 'fa-shopping-cart',
                'title': f'New order #{order.id} - {order.product.name}',
                'time': format_time_ago(order.created_at),
                'type': 'order'
            })
        
        # Add recent bulk orders
        for order in recent_bulk_orders:
            activities.append({
                'icon': 'fa-truck',
                'title': f'Bulk order {order.order_id} - {order.company_name}',
                'time': format_time_ago(order.created_at),
                'type': 'bulk_order'
            })
        
        # Add recent trial packs
        for order in recent_trial_packs:
            activities.append({
                'icon': 'fa-vial',
                'title': f'Trial pack #{order.id} - {order.name}',
                'time': format_time_ago(order.created_at),
                'type': 'trial_pack'
            })
        
        # Add recent messages
        for message in recent_messages:
            activities.append({
                'icon': 'fa-envelope',
                'title': f'Message from {message.name}: {message.subject}',
                'time': format_time_ago(message.created_at),
                'type': 'message'
            })
        
        # Sort activities by time
        activities.sort(key=lambda item: item['time'], reverse=True)
        activities = activities[:10]  # Keep only latest 10
        
        # Order status distribution
        order_status_data = Order.objects.values('order_status').annotate(count=Count('id'))
        status_distribution = {item['order_status']: item['count'] for item in order_status_data}
        
        # Sales data for chart (last 6 months)
        sales_data = []
        labels = []
        for i in range(6):
            month_start = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_orders = Order.objects.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            )
            
            month_revenue = month_orders.aggregate(total=Sum('total_amount'))['total'] or 0
            month_count = month_orders.count()
            
            sales_data.append({
                'revenue': float(month_revenue),
                'orders': month_count
            })
            labels.append(month_start.strftime('%b'))
        
        sales_data.reverse()
        labels.reverse()
        
        return JsonResponse({
            'success': True,
            'data': {
                'total_orders': total_orders,
                'bulk_orders': bulk_orders,
                'trial_packs': trial_packs,
                'shipped_orders': shipped_orders,
                'revenue': float(revenue),
                'this_month_orders': this_month_orders,
                'last_month_orders': last_month_orders,
                'activities': activities,
                'status_distribution': status_distribution,
                'sales_data': sales_data,
                'chart_labels': labels
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def format_time_ago(dt):
    """Format datetime as 'X time ago'"""
    now = timezone.now()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return dt.strftime('%Y-%m-%d %H:%M')

def admin_dashboard_custom(request):
    """Custom admin dashboard view"""
    return render(request, 'admin/admin_dashboard.html', {
        'title': 'Admin Dashboard',
        'site_header': 'VICTNOW Admin Panel',
        'site_title': 'VICTNOW Administration',
    })
