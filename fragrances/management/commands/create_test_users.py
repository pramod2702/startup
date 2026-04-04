from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from fragrances.models import UserProfile
import json

class Command(BaseCommand):
    help = 'Create test users for the perfume website'

    def handle(self, *args, **options):
        # Test users data
        test_users = [
            {
                'username': 'admin',
                'email': 'admin@victnow.com',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
                'phone_number': '9876543210'
            },
            {
                'username': 'john',
                'email': 'john@example.com',
                'password': 'john123',
                'first_name': 'John',
                'last_name': 'Doe',
                'is_staff': False,
                'is_superuser': False,
                'phone_number': '9876543211'
            },
            {
                'username': 'jane',
                'email': 'jane@example.com',
                'password': 'jane123',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'is_staff': False,
                'is_superuser': False,
                'phone_number': '9876543212'
            },
            {
                'username': 'mike',
                'email': 'mike@example.com',
                'password': 'mike123',
                'first_name': 'Mike',
                'last_name': 'Johnson',
                'is_staff': False,
                'is_superuser': False,
                'phone_number': '9876543213'
            }
        ]

        self.stdout.write('Creating test users...')
        
        for user_data in test_users:
            username = user_data['username']
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'User {username} already exists, skipping...')
                continue
            
            # Create Django User
            user = User.objects.create_user(
                username=username,
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_staff=user_data['is_staff'],
                is_superuser=user_data['is_superuser']
            )
            
            # Create or get UserProfile
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'phone_number': user_data['phone_number'],
                    'country_code': '+91',
                    'login_method': 'standard',
                    'is_verified': True,
                    'successful_logins': 0
                }
            )
            
            if not created:
                self.stdout.write(f'UserProfile for {username} already exists, updating...')
                profile.phone_number = user_data['phone_number']
                profile.login_method = 'standard'
                profile.is_verified = True
                profile.save()
            
            self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
        
        self.stdout.write(self.style.SUCCESS('Test users created successfully!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('Admin - Username: admin, Password: admin123')
        self.stdout.write('User 1 - Username: john, Password: john123')
        self.stdout.write('User 2 - Username: jane, Password: jane123')
        self.stdout.write('User 3 - Username: mike, Password: mike123')
