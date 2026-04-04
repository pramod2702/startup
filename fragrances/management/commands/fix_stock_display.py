from django.core.management.base import BaseCommand
from fragrances.models import Product

class Command(BaseCommand):
    help = 'Fix stock display to only show Out of Stock badge'

    def handle(self, *args, **options):
        self.stdout.write('Fixing stock display...')
        
        products = Product.objects.all()
        
        for product in products:
            # Set all products to out of stock for testing
            product.stock_status = 'out_of_stock'
            product.stock_quantity = 0
            product.save()
            self.stdout.write(f'Updated: {product.name} - Out of Stock')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {products.count()} products to Out of Stock!'))
        
        # Now update one product to in stock for testing
        if products.exists():
            test_product = products.first()
            test_product.stock_status = 'in_stock'
            test_product.stock_quantity = 15
            test_product.save()
            self.stdout.write(f'Test product updated: {test_product.name} - In Stock ({test_product.stock_quantity} available)')
