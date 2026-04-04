# Generated manually for stock management

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fragrances', '0016_product_stock_quantity_product_stock_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='stock_status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('in_stock', 'In Stock'),
                    ('out_of_stock', 'Out of Stock'),
                    ('limited', 'Limited Stock')
                ],
                default='in_stock'
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='stock_quantity',
            field=models.PositiveIntegerField(
                default=10,
                help_text='Number of items in stock'
            ),
        ),
    ]
