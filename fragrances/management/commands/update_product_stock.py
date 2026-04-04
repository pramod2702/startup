from django.core.management.base import BaseCommand
from fragrances.models import Product
import random

class Command(BaseCommand):
    help = 'Update existing products with stock status and quantity'

    def handle(self, *args, **options):
        self.stdout.write('Updating product stock data...')
        
        products = Product.objects.all()
        stock_statuses = ['in_stock', 'in_stock', 'limited', 'out_of_stock']
        
        updated_count = 0
        
        for product in products:
            # Randomly assign stock status
            stock_status = random.choice(stock_statuses)
            
            # Set quantity based on status
            if stock_status == 'in_stock':
                stock_quantity = random.randint(10, 50)
            elif stock_status == 'limited':
                stock_quantity = random.randint(1, 5)
            else:
                stock_quantity = 0
            
            # Update product
            product.stock_status = stock_status
            product.stock_quantity = stock_quantity
            product.save()
            
            updated_count += 1
            self.stdout.write(f'Updated: {product.name} - {product.get_stock_display()}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} products with stock data!'))
