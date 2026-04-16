from .models import Cart

def cart_count(request):
    """
    Context processor to provide cart count to all templates
    """
    if request.user.is_authenticated:
        cart_count = Cart.get_cart_count(request.user)
    else:
        cart_count = 0
    
    return {
        'cart_count': cart_count
    }
