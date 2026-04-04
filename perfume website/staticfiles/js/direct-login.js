/**
 * Direct Mobile Login Integration
 * Integrates with login button to provide instant authentication and admin integration
 */

class DirectMobileLogin {
    constructor() {
        this.baseURL = window.location.origin;
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupLoginButton();
    }

    bindEvents() {
        // Listen for login button clicks
        const loginBtn = document.getElementById('loginBtn');
        if (loginBtn) {
            loginBtn.addEventListener('click', (e) => this.handleLoginClick(e));
        }

        // Listen for phone input changes
        const phoneInput = document.getElementById('phoneNumber');
        if (phoneInput) {
            phoneInput.addEventListener('input', (e) => this.handlePhoneInput(e));
        }
    }

    setupLoginButton() {
        const loginBtn = document.getElementById('loginBtn');
        if (loginBtn) {
            // Add loading state classes
            loginBtn.classList.add('direct-login-enabled');
            
            // Store original button text
            loginBtn.dataset.originalText = loginBtn.querySelector('#btnText').innerHTML;
        }
    }

    handleLoginClick(event) {
        event.preventDefault();
        
        const loginBtn = document.getElementById('loginBtn');
        const btnText = document.getElementById('btnText');
        const phoneNumber = document.getElementById('phoneNumber')?.value?.trim();
        
        if (!phoneNumber) {
            this.showError('Please enter your mobile number');
            return;
        }

        if (!this.validatePhoneNumber(phoneNumber)) {
            this.showError('Please enter a valid 10-digit mobile number');
            return;
        }

        // Show loading state
        this.setLoadingState(true);

        // Start direct login process
        this.performDirectLogin(phoneNumber);
    }

    handlePhoneInput(event) {
        const phoneNumber = event.target.value.trim();
        const loginBtn = document.getElementById('loginBtn');
        const btnText = document.getElementById('btnText');

        // Enable/disable button based on input
        if (phoneNumber.length >= 10 && this.validatePhoneNumber(phoneNumber)) {
            loginBtn.disabled = false;
            loginBtn.classList.remove('disabled');
            btnText.innerHTML = '<i class="fas fa-sign-in-alt"></i> Quick Login';
        } else {
            loginBtn.disabled = true;
            loginBtn.classList.add('disabled');
            btnText.innerHTML = '<i class="fas fa-mobile-alt"></i> Enter Mobile Number';
        }
    }

    validatePhoneNumber(phoneNumber) {
        // Remove all non-digit characters
        const cleanNumber = phoneNumber.replace(/\D/g, '');
        return cleanNumber.length === 10;
    }

    async performDirectLogin(phoneNumber) {
        try {
            const response = await fetch(`${this.baseURL}/api/direct-mobile-login/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    mobile_number: phoneNumber,
                    country_code: '+91'
                })
            });

            const result = await response.json();

            if (result.success) {
                this.handleLoginSuccess(result);
            } else {
                this.handleLoginError(result.error || 'Login failed');
            }
        } catch (error) {
            console.error('Direct login error:', error);
            this.handleLoginError('Network error. Please try again.');
        } finally {
            this.setLoadingState(false);
        }
    }

    handleLoginSuccess(result) {
        const loginBtn = document.getElementById('loginBtn');
        const btnText = document.getElementById('btnText');

        // Show success state
        btnText.innerHTML = '<i class="fas fa-check-circle"></i> Login Successful!';
        loginBtn.classList.add('success');

        // Store user data in localStorage
        localStorage.setItem('userData', JSON.stringify(result.user));
        localStorage.setItem('isLoggedIn', 'true');
        localStorage.setItem('loginTime', new Date().toISOString());

        // Show success message
        this.showSuccess(`Welcome back, ${result.user.full_name}!`);

        // Redirect after delay
        setTimeout(() => {
            if (result.redirect_url) {
                window.location.href = result.redirect_url;
            } else {
                window.location.href = '/';
            }
        }, 1500);

        // Track login event
        this.trackLoginEvent(result.user);
    }

    handleLoginError(error) {
        const loginBtn = document.getElementById('loginBtn');
        const btnText = document.getElementById('btnText');

        // Show error state
        btnText.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Login Failed';
        loginBtn.classList.add('error');

        // Show error message
        this.showError(error);

        // Reset button after delay
        setTimeout(() => {
            this.resetButton();
        }, 3000);
    }

    setLoadingState(loading) {
        const loginBtn = document.getElementById('loginBtn');
        const btnText = document.getElementById('btnText');

        if (loading) {
            loginBtn.disabled = true;
            loginBtn.classList.add('loading');
            btnText.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
        } else {
            loginBtn.disabled = false;
            loginBtn.classList.remove('loading');
        }
    }

    resetButton() {
        const loginBtn = document.getElementById('loginBtn');
        const btnText = document.getElementById('btnText');

        loginBtn.disabled = false;
        loginBtn.classList.remove('loading', 'success', 'error');
        
        const phoneNumber = document.getElementById('phoneNumber')?.value?.trim();
        if (phoneNumber && this.validatePhoneNumber(phoneNumber)) {
            btnText.innerHTML = '<i class="fas fa-sign-in-alt"></i> Quick Login';
        } else {
            btnText.innerHTML = loginBtn.dataset.originalText || '<i class="fas fa-paper-plane"></i> Verify OTP';
        }
    }

    showSuccess(message) {
        // Create success notification
        this.createNotification(message, 'success');
    }

    showError(error) {
        // Create error notification
        this.createNotification(error, 'error');
    }

    createNotification(message, type) {
        // Remove existing notifications
        const existing = document.querySelector('.direct-login-notification');
        if (existing) {
            existing.remove();
        }

        // Create new notification
        const notification = document.createElement('div');
        notification.className = `direct-login-notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
                <span>${message}</span>
            </div>
        `;

        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#28a745' : '#dc3545'};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 9999;
            max-width: 300px;
            animation: slideIn 0.3s ease-out;
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }

    trackLoginEvent(userData) {
        // Track login event for analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'login', {
                'event_category': 'Authentication',
                'event_label': 'Mobile Direct Login',
                'user_id': userData.id,
                'login_method': userData.login_method,
                'device_type': userData.device_type
            });
        }

        // Track in localStorage for admin dashboard
        const loginEvents = JSON.parse(localStorage.getItem('loginEvents') || '[]');
        loginEvents.push({
            timestamp: new Date().toISOString(),
            user_id: userData.id,
            username: userData.username,
            login_method: userData.login_method,
            device_type: userData.device_type,
            browser: userData.browser,
            ip_address: userData.ip_address
        });
        localStorage.setItem('loginEvents', JSON.stringify(loginEvents));
    }

    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // Public method to check login status
    isLoggedIn() {
        return localStorage.getItem('isLoggedIn') === 'true';
    }

    // Public method to get current user
    getCurrentUser() {
        const userData = localStorage.getItem('userData');
        return userData ? JSON.parse(userData) : null;
    }

    // Public method to logout
    logout() {
        localStorage.removeItem('userData');
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('loginTime');
        window.location.href = '/login/';
    }

    // Add CSS animations
    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }

            .direct-login-enabled {
                transition: all 0.3s ease;
            }

            .direct-login-enabled:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            }

            .direct-login-enabled.loading {
                background: linear-gradient(135deg, #6c757d, #5a6268) !important;
                cursor: not-allowed;
            }

            .direct-login-enabled.success {
                background: linear-gradient(135deg, #28a745, #20c997) !important;
            }

            .direct-login-enabled.error {
                background: linear-gradient(135deg, #dc3545, #c82333) !important;
            }

            .direct-login-enabled.disabled {
                background: linear-gradient(135deg, #6c757d, #5a6268) !important;
                cursor: not-allowed;
                opacity: 0.6;
            }

            .notification-content {
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .notification-content i {
                font-size: 18px;
            }
        `;
        document.head.appendChild(style);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.directLogin = new DirectMobileLogin();
    window.directLogin.addStyles();
});

// Make available globally
window.DirectMobileLogin = DirectMobileLogin;
