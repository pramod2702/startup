from django.core.management.base import BaseCommand
from fragrances.models import TrialPack, CorporateOrder, UserActivity
from django.contrib.auth.models import User
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Create sample orders for test users'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample orders for test users...')
        
        # Get test users
        test_users = User.objects.filter(username__in=['admin', 'john', 'jane', 'mike'])
        
        for user in test_users:
            self.stdout.write(f'\nCreating orders for user: {user.username}')
            
            # Create trial packs for this user
            for i in range(2):
                trial_pack, created = TrialPack.objects.get_or_create(
                    user=user,
                    trial_pack_name=f'VICTNOW {random.choice(["FORGE", "MUSE", "NEXUS"])} Trial',
                    defaults={
                        'name': user.get_full_name() or user.username,
                        'email': user.email,
                        'amount': random.choice([299, 399, 499]),
                        'order_status': random.choice(['pending', 'processing', 'delivered']),
                        'phone': '9876543210',
                        'address': f'{user.username} Address',
                        'city': 'Test City',
                        'state': 'Test State',
                        'postal_code': '123456',
                        'created_at': timezone.now() - timezone.timedelta(days=random.randint(1, 30))
                    }
                )
                if created:
                    self.stdout.write(f'  ✓ Created TrialPack: {trial_pack.trial_pack_name} - {trial_pack.order_status}')
            
            # Create corporate orders for this user
            for i in range(1):
                corp_order, created = CorporateOrder.objects.get_or_create(
                    user=user,
                    order_id=f'CORP-{user.username.upper()}-{random.randint(100, 999)}',
                    defaults={
                        'name': user.get_full_name() or user.username,
                        'email': user.email,
                        'company_name': f'{user.username.title()} Corporation',
                        'fragrance_type': random.choice(['victnow_forge', 'victnow_muse', 'victnow_nexus']),
                        'quantity': random.randint(10, 100),
                        'unit_price': random.choice([2999, 3999, 1999]),
                        'status': random.choice(['pending', 'processing', 'delivered']),
                        'shipping_address': f'Corporate Address for {user.username}',
                        'created_at': timezone.now() - timezone.timedelta(days=random.randint(1, 30))
                    }
                )
                if created:
                    self.stdout.write(f'  ✓ Created CorporateOrder: {corp_order.order_id} - {corp_order.status}')
            
            # Create user activities
            for i in range(3):
                activity_type = random.choice(['trial_pack_created', 'corporate_order_created', 'login'])
                UserActivity.objects.create(
                    user=user,
                    activity_type=activity_type,
                    description=f'Sample {activity_type} activity',
                    created_at=timezone.now() - timezone.timedelta(hours=random.randint(1, 72))
                )
        
        self.stdout.write(self.style.SUCCESS('\nSuccessfully created sample orders for test users!'))
        self.stdout.write('\nTest users and their orders:')
        for user in test_users:
            trial_count = TrialPack.objects.filter(user=user).count()
            corp_count = CorporateOrder.objects.filter(user=user).count()
            self.stdout.write(f'  {user.username}: {trial_count} trial packs, {corp_count} corporate orders')
