// Dynamic Razorpay Payment Integration
// Frontend JavaScript

/**
 * Initialize payment with dynamic price
 * @param {number} price - Product price in rupees (can be decimal like 53.20)
 * @param {string} productName - Product name
 * @param {object} productData - Additional product data
 */
function payNow(price, productName, productData = {}) {
    console.log('=== DYNAMIC RAZORPAY PAYMENT INITIATED ===');
    console.log('Product Price (₹):', price);
    console.log('Price type:', typeof price);
    console.log('Product Name:', productName);
    console.log('Product Data:', productData);
    
    // Validate price - ensure it's a positive number
    if (!price || isNaN(price) || price <= 0) {
        alert('Invalid price. Please try again.');
        return;
    }
    
    // Ensure price is treated as float, not int
    const priceAsFloat = parseFloat(price);
    console.log('Price as float:', priceAsFloat);
    console.log('Price * 100 (should be paise):', priceAsFloat * 100);
    
    // Show loading state
    showPaymentLoading();
    
    // Send price to backend to create Razorpay order
    fetch('/api/create-razorpay-order/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            amount: priceAsFloat,  // Send as float, not int
            product_name: productName,
            product_data: productData
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Backend Response:', data);
        
        if (data.success) {
            // Open Razorpay checkout with dynamic amount from backend
            openRazorpayCheckout(data.order_data);
        } else {
            alert('Error creating payment order: ' + (data.error || 'Unknown error'));
            hidePaymentLoading();
        }
    })
    .catch(error => {
        console.error('Payment Error:', error);
        alert('Payment initialization failed. Please try again.');
        hidePaymentLoading();
    });
}

/**
 * Open Razorpay checkout with backend order data
 * @param {object} orderData - Order data from backend
 */
function openRazorpayCheckout(orderData) {
    console.log('=== OPENING RAZORPAY CHECKOUT ===');
    console.log('Backend order data:', orderData);
    
    const options = {
        key: orderData.key,
        amount: orderData.amount, // Amount from backend in paise
        currency: orderData.currency,
        name: orderData.name,
        description: orderData.description,
        order_id: orderData.order_id, // Order ID from backend
        image: orderData.image,
        handler: function (response) {
            console.log('Payment Successful:', response);
            handlePaymentSuccess(response, orderData);
        },
        prefill: {
            name: orderData.prefill?.name || '',
            email: orderData.prefill?.email || '',
            contact: orderData.prefill?.contact || ''
        },
        notes: orderData.notes || {},
        theme: {
            color: '#d4af37'
        },
        modal: {
            ondismiss: function() {
                console.log('Razorpay modal closed');
                hidePaymentLoading();
            },
            escape: true,
            handleback: true,
            backdropclose: true
        }
    };
    
    console.log('=== FINAL RAZORPAY OPTIONS ===');
    console.log('Key:', options.key);
    console.log('Amount (paise):', options.amount);
    console.log('Amount (₹):', options.amount / 100);
    console.log('Currency:', options.currency);
    console.log('Order ID:', options.order_id);
    console.log('Description:', options.description);
    console.log('=====================================');
    
    const rzp = new Razorpay(options);
    rzp.open();
}

/**
 * Handle successful payment
 * @param {object} response - Razorpay response
 * @param {object} orderData - Original order data
 */
function handlePaymentSuccess(response, orderData) {
    console.log('Processing payment success...');
    
    // Send payment details to backend for verification and order creation
    fetch('/api/verify-razorpay-payment/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
            order_data: orderData
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Payment Successful! Order ID: ' + data.order_id);
            window.location.href = data.redirect_url || '/payment-success/';
        } else {
            alert('Payment verification failed: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Verification Error:', error);
        alert('Payment verification failed. Please contact support.');
    })
    .finally(() => {
        hidePaymentLoading();
    });
}

/**
 * Show loading state during payment processing
 */
function showPaymentLoading() {
    // Create or show loading overlay
    let loadingDiv = document.getElementById('payment-loading');
    if (!loadingDiv) {
        loadingDiv = document.createElement('div');
        loadingDiv.id = 'payment-loading';
        loadingDiv.innerHTML = `
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                        background: rgba(0,0,0,0.8); display: flex; justify-content: center; 
                        align-items: center; z-index: 9999;">
                <div style="background: white; padding: 30px; border-radius: 10px; text-align: center;">
                    <div style="width: 50px; height: 50px; border: 3px solid #f3f3f3; 
                                border-top: 3px solid #d4af37; border-radius: 50%; 
                                animation: spin 1s linear infinite; margin: 0 auto 20px;"></div>
                    <h3>Processing Payment...</h3>
                    <p>Please wait while we initialize your payment.</p>
                </div>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        `;
        document.body.appendChild(loadingDiv);
    }
    loadingDiv.style.display = 'flex';
}

/**
 * Hide loading state
 */
function hidePaymentLoading() {
    const loadingDiv = document.getElementById('payment-loading');
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
}

/**
 * Get CSRF token from cookies
 * @param {string} name - Cookie name
 * @returns {string} CSRF token
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Usage Example:
 * 
 * For single product:
 * payNow(2499, 'VICTNOW MUSE', {product_id: 5, quantity: 1});
 * 
 * For cart:
 * const cartTotal = calculateCartTotal();
 * payNow(cartTotal, 'Cart Purchase', {items: cartItems});
 * 
 * For trial pack:
 * payNow(2499, 'VICTNOW Trial Pack', {type: 'trial_pack'});
 */
