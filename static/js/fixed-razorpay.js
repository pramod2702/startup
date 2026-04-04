/**
 * FIXED Razorpay Integration - Dynamic Pricing
 * Frontend JavaScript
 */

/**
 * Main payment function - accepts dynamic price
 * @param {number} price - Product price in rupees (can be decimal like 53.20)
 * @param {string} productName - Product name
 * @param {object} productData - Additional product data
 */
function payNow(price, productName, productData = {}) {
    console.log("=== FRONTEND: PAYNOW CALLED ===");
    console.log("Selected price:", price);
    console.log("Price type:", typeof price);
    console.log("Product name:", productName);
    console.log("Product data:", productData);
    
    // Validate price - ensure it's a positive number
    if (!price || isNaN(price) || price <= 0) {
        alert('Invalid price. Please try again.');
        return;
    }
    
    // Ensure price is treated as float, NOT int
    const priceAsFloat = parseFloat(price);
    console.log("Price as float:", priceAsFloat);
    console.log("Price * 100 (should be paise):", priceAsFloat * 100);
    
    // Show loading
    showLoading();
    
    // Send to backend - DO NOT use parseInt
    fetch('/api/create-order/', {  // FIXED: Use correct endpoint
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            amount: priceAsFloat,  // Send as float
            product_name: productName,
            product_data: productData
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("=== BACKEND RESPONSE ===");
        console.log("Backend data:", data);
        
        if (data.success) {
            console.log("Backend amount (paise):", data.order_data.amount);
            console.log("Backend amount (₹):", data.order_data.amount / 100);
            openRazorpay(data.order_data);
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
            hideLoading();
        }
    })
    .catch(error => {
        console.error('Payment error:', error);
        alert('Payment failed. Please try again.');
        hideLoading();
    });
}

/**
 * Open Razorpay with backend response
 * @param {object} data - Order data from backend
 */
function openRazorpay(data) {
    console.log("=== OPENING RAZORPAY ===");
    console.log("Using backend amount:", data.amount);
    console.log("Using backend order_id:", data.order_id);
    
    const options = {
        key: data.key,
        amount: data.amount,        // Use backend amount
        currency: data.currency,
        name: data.name,
        description: data.description,
        order_id: data.order_id,    // Use backend order_id
        image: data.image,
        handler: function (response) {
            console.log('Payment successful:', response);
            handlePaymentSuccess(response, data);
        },
        prefill: data.prefill || {},
        notes: data.notes || {},
        theme: {
            color: '#d4af37'
        },
        modal: {
            ondismiss: function() {
                console.log('Payment modal dismissed');
                hideLoading();
            }
        }
    };
    
    console.log("Final Razorpay options:", options);
    console.log("Amount that will be shown:", options.amount / 100);
    
    const rzp = new Razorpay(options);
    rzp.open();
}

/**
 * Handle successful payment
 */
function handlePaymentSuccess(response, orderData) {
    console.log('=== PAYMENT SUCCESS ===');
    console.log('Response:', response);
    
    // Verify payment with backend
    fetch('/api/verify-payment/', {  // FIXED: Use correct endpoint
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
            window.location.href = '/payment-success/?order_id=' + data.order_id;
        } else {
            alert('Payment verification failed: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Verification error:', error);
        alert('Payment verification failed. Please contact support.');
    })
    .finally(() => {
        hideLoading();
    });
}

/**
 * Loading states
 */
function showLoading() {
    const existing = document.getElementById('payment-loading');
    if (existing) existing.remove();
    
    const loading = document.createElement('div');
    loading.id = 'payment-loading';
    loading.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                    background: rgba(0,0,0,0.8); display: flex; justify-content: center; 
                    align-items: center; z-index: 9999;">
            <div style="background: white; padding: 30px; border-radius: 10px; text-align: center;">
                <div style="width: 50px; height: 50px; border: 3px solid #f3f3f3; 
                            border-top: 3px solid #d4af37; border-radius: 50%; 
                            animation: spin 1s linear infinite; margin: 0 auto 20px;"></div>
                <h3>Processing Payment...</h3>
                <p>Please wait while we create your order.</p>
            </div>
        </div>
        <style>
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    `;
    document.body.appendChild(loading);
}

function hideLoading() {
    const loading = document.getElementById('payment-loading');
    if (loading) loading.remove();
}

/**
 * Get CSRF token
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
 * Usage Examples:
 * 
 * Single product:
 * payNow(53.20, 'VICTNOW MUSE', {product_id: 5});
 * 
 * Cart purchase:
 * const cartTotal = calculateCartTotal();
 * payNow(cartTotal, 'Cart Purchase', {items: cartItems});
 * 
 * Trial pack:
 * payNow(2499, 'VICTNOW Trial Pack', {type: 'trial'});
 */
