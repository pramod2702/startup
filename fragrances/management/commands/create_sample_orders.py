from django.core.management.base import BaseCommand
from fragrances.models import TrialPack, CorporateOrder, UserActivity
from django.contrib.auth.models import User
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Create sample orders for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample orders...')
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        # Create sample TrialPack orders
        trial_packs_data = [
            {
                'name': 'John Doe',
                'email': 'john@example.com',
                'trial_pack_name': 'VICTNOW FORGE Trial',
                'amount': 299.00,
                'order_status': 'delivered'
            },
            {
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'trial_pack_name': 'VICTNOW MUSE Trial',
                'amount': 399.00,
                'order_status': 'processing'
            },
            {
                'name': 'Mike Johnson',
                'email': 'mike@example.com',
                'trial_pack_name': 'VICTNOW NEXUS Trial',
                'amount': 499.00,
                'order_status': 'pending'
            }
        ]
        
        for data in trial_packs_data:
            trial_pack, created = TrialPack.objects.get_or_create(
                email=data['email'],
                trial_pack_name=data['trial_pack_name'],
                defaults={
                    'user': user,
                    'name': data['name'],
                    'amount': data['amount'],
                    'order_status': data['order_status'],
                    'phone': '9876543210',
                    'address': 'Test Address',
                    'city': 'Test City',
                    'state': 'Test State',
                    'postal_code': '123456'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created TrialPack: {trial_pack.trial_pack_name}'))
            else:
                self.stdout.write(f'TrialPack already exists: {trial_pack.trial_pack_name}')
        
        # Create sample CorporateOrder orders
        corporate_orders_data = [
            {
                'order_id': 'CORP001',
                'company_name': 'ABC Corporation',
                'email': 'contact@abc.com',
                'fragrance_type': 'victnow_forge',
                'quantity': 50,
                'unit_price': 2999.00,
                'status': 'delivered'
            },
            {
                'order_id': 'CORP002',
                'company_name': 'XYZ Industries',
                'email': 'orders@xyz.com',
                'fragrance_type': 'victnow_muse',
                'quantity': 25,
                'unit_price': 3999.00,
                'status': 'processing'
            },
            {
                'order_id': 'CORP003',
                'company_name': 'DEF Limited',
                'email': 'info@def.com',
                'fragrance_type': 'victnow_nexus',
                'quantity': 100,
                'unit_price': 1999.00,
                'status': 'pending'
            }
        ]
        
        for data in corporate_orders_data:
            corporate_order, created = CorporateOrder.objects.get_or_create(
                order_id=data['order_id'],
                defaults={
                    'user': user,
                    'name': data['company_name'],
                    'email': data['email'],
                    'company_name': data['company_name'],
                    'fragrance_type': data['fragrance_type'],
                    'quantity': data['quantity'],
                    'unit_price': data['unit_price'],
                    'status': data['status'],
                    'shipping_address': 'Corporate Address'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created CorporateOrder: {corporate_order.order_id}'))
            else:
                self.stdout.write(f'CorporateOrder already exists: {corporate_order.order_id}')
        
        # Create sample user activities
        activities_data = [
            {
                'activity_type': 'trial_pack_created',
                'description': 'Trial pack order created'
            },
            {
                'activity_type': 'corporate_order_created',
                'description': 'Corporate order created'
            },
            {
                'activity_type': 'login',
                'description': 'User logged in'
            }
        ]
        
        for data in activities_data:
            activity = UserActivity.objects.create(
                user=user,
                activity_type=data['activity_type'],
                description=data['description']
            )
            self.stdout.write(self.style.SUCCESS(f'Created Activity: {activity.activity_type}'))
        
        self.stdout.write(self.style.SUCCESS('Sample orders created successfully!'))
