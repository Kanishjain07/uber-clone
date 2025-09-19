// Authentication JavaScript
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.isAuthenticated = false;
        this.init();
    }

    init() {
        this.setupModalEventListeners();
        this.setupFormSubmissions();
        this.checkAuthStatus();
    }

    setupModalEventListeners() {
        // Login button
        const loginBtn = document.getElementById('loginBtn');
        if (loginBtn) {
            loginBtn.addEventListener('click', () => {
                this.showModal('loginModal');
            });
        }

        // Register button
        const registerBtn = document.getElementById('registerBtn');
        if (registerBtn) {
            registerBtn.addEventListener('click', () => {
                this.showModal('registerModal');
            });
        }

        // Close buttons
        const closeButtons = document.querySelectorAll('.close');
        closeButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.hideAllModals();
            });
        });

        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.hideAllModals();
            }
        });

        // Escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideAllModals();
            }
        });
    }

    setupFormSubmissions() {
        // Login form
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleLogin();
            });
        }

        // Register form
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleRegister();
            });
        }

        // Switch between login and register
        const showRegisterLink = document.getElementById('showRegister');
        if (showRegisterLink) {
            showRegisterLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.hideAllModals();
                this.showModal('registerModal');
            });
        }

        const showLoginLink = document.getElementById('showLogin');
        if (showLoginLink) {
            showLoginLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.hideAllModals();
                this.showModal('loginModal');
            });
        }
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';

            // Focus on first input
            const firstInput = modal.querySelector('input, select');
            if (firstInput) {
                firstInput.focus();
            }
        }
    }

    showRegisterModal(userType = null) {
        this.showModal('registerModal');

        // Pre-select user type if provided
        if (userType) {
            const userTypeSelect = document.querySelector('#registerModal select');
            if (userTypeSelect) {
                userTypeSelect.value = userType;
            }
        }
    }

    hideAllModals() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.style.display = 'none';
        });
        document.body.style.overflow = 'auto';
    }

    async handleLogin() {
        const form = document.getElementById('loginForm');
        const formData = new FormData(form);
        const email = formData.get('email') || form.querySelector('input[type="email"]').value;
        const password = formData.get('password') || form.querySelector('input[type="password"]').value;

        if (!email || !password) {
            this.showNotification('Please fill in all fields', 'error');
            return;
        }

        try {
            // Show loading state
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.classList.add('loading');
            submitBtn.textContent = 'Logging in...';

            // Simulate API call
            const response = await this.loginUser(email, password);

            if (response.success) {
                this.showNotification('Login successful!', 'success');
                this.hideAllModals();
                this.updateUIAfterAuth(response.user);
                
                // Reset form
                form.reset();
            } else {
                this.showNotification(response.message || 'Login failed', 'error');
            }

        } catch (error) {
            this.showNotification('Login failed. Please try again.', 'error');
        } finally {
            // Reset button state
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.classList.remove('loading');
            submitBtn.textContent = 'Login';
        }
    }

    async handleRegister() {
        const form = document.getElementById('registerForm');
        const formData = new FormData(form);

        // Get form values
        const first_name = formData.get('first_name');
        const last_name = formData.get('last_name');
        const email = formData.get('email');
        const phone = formData.get('phone');
        const password = formData.get('password');
        const confirmPassword = formData.get('confirmPassword');
        const user_type = formData.get('user_type');

        // Validation
        if (!first_name || !last_name || !email || !phone || !password || !confirmPassword || !user_type) {
            this.showNotification('Please fill in all fields', 'error');
            return;
        }

        // Phone number validation
        const phoneRegex = /^\+?[\d\s\-\(\)]+$/;
        if (!phoneRegex.test(phone)) {
            this.showNotification('Please enter a valid phone number', 'error');
            return;
        }

        if (password !== confirmPassword) {
            this.showNotification('Passwords do not match', 'error');
            return;
        }

        // Password strength validation to match backend requirements
        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
        if (!passwordRegex.test(password)) {
            this.showNotification('Password must be at least 8 characters with uppercase, lowercase, number, and special character', 'error');
            return;
        }

        try {
            // Show loading state
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.classList.add('loading');
            submitBtn.textContent = 'Creating Account...';

            // Simulate API call
            const response = await this.registerUser({
                first_name,
                last_name,
                email,
                phone,
                password,
                user_type
            });

            if (response.success) {
                this.showNotification('Account created successfully!', 'success');
                this.hideAllModals();
                this.updateUIAfterAuth(response.user);

                // Redirect drivers to driver dashboard
                if (user_type === 'driver') {
                    setTimeout(() => {
                        window.location.href = 'driver.html';
                    }, 1500);
                }

                // Reset form
                form.reset();
            } else {
                this.showNotification(response.message || 'Registration failed', 'error');
            }

        } catch (error) {
            this.showNotification('Registration failed. Please try again.', 'error');
        } finally {
            // Reset button state
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.classList.remove('loading');
            submitBtn.textContent = 'Sign Up';
        }
    }

    async loginUser(email, password) {
        try {
            const api = window.apiHelper || new APIHelper();
            const response = await api.request('/api/v1/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });
            if (response.success && response.data && response.data.user) {
                // Store tokens and user info
                const user = response.data.user;
                user.token = response.data.access_token;
                user.refreshToken = response.data.refresh_token;
                return { success: true, user };
            } else {
                return {
                    success: false,
                    message: response.data?.error || 'Login failed'
                };
            }
        } catch (error) {
            return {
                success: false,
                message: error.message || 'Login failed'
            };
        }
    }

    async registerUser(userData) {
        try {
            const api = window.apiHelper || new APIHelper();
            // Prepare payload for backend
            const payload = {
                email: userData.email,
                password: userData.password,
                user_type: userData.user_type,
                first_name: userData.first_name,
                last_name: userData.last_name,
                phone: userData.phone,
            };
            // If driver, add vehicle info (can be extended later)
            if (userData.user_type === 'driver') {
                payload.vehicle_info = userData.vehicle_info || {
                    make: 'Toyota',
                    model: 'Camry',
                    year: '2020',
                    license_plate: 'ABC123',
                    vehicle_type: 'sedan'
                };
            }

            // Debug: Log the payload being sent
            console.log('Registration payload:', payload);

            const response = await api.request('/api/v1/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            if (response.success && response.data && response.data.user) {
                // Store tokens and user info
                const user = response.data.user;
                user.token = response.data.access_token;
                user.refreshToken = response.data.refresh_token;
                return { success: true, user };
            } else {
                return {
                    success: false,
                    message: response.data?.error || 'Registration failed'
                };
            }
        } catch (error) {
            return {
                success: false,
                message: error.message || 'Registration failed'
            };
        }
    }

    updateUIAfterAuth(user) {
        this.currentUser = user;
        this.isAuthenticated = true;

        // Store user data in localStorage
        localStorage.setItem('authToken', user.token);
        localStorage.setItem('userData', JSON.stringify(user));

        // Update navigation
        this.updateNavigation();

        // Update app state if available
        if (window.app) {
            window.app.currentUser = user;
            window.app.isAuthenticated = true;
            window.app.updateUIForAuthenticatedUser();
        }

        // Show welcome message
        this.showNotification(`Welcome, ${user.name}!`, 'success');
    }

    updateNavigation() {
        const navAuth = document.querySelector('.nav-auth');
        if (navAuth && this.currentUser) {
            navAuth.innerHTML = `
                <span class="user-name">Hi, ${this.currentUser.name}</span>
                <button class="btn btn-outline" id="logoutBtn">Logout</button>
            `;
            
            // Add logout event listener
            const logoutBtn = document.getElementById('logoutBtn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', () => {
                    this.logout();
                });
            }
        }
    }

    logout() {
        // Clear user data
        this.currentUser = null;
        this.isAuthenticated = false;
        localStorage.removeItem('authToken');
        localStorage.removeItem('userData');

        // Update navigation
        const navAuth = document.querySelector('.nav-auth');
        if (navAuth) {
            navAuth.innerHTML = `
                <button class="btn btn-outline" id="loginBtn">Login</button>
                <button class="btn btn-primary" id="registerBtn">Sign Up</button>
            `;
            
            // Re-add event listeners
            const loginBtn = navAuth.querySelector('#loginBtn');
            const registerBtn = navAuth.querySelector('#registerBtn');
            
            if (loginBtn) {
                loginBtn.addEventListener('click', () => {
                    this.showModal('loginModal');
                });
            }
            
            if (registerBtn) {
                registerBtn.addEventListener('click', () => {
                    this.showModal('registerModal');
                });
            }
        }

        // Update app state if available
        if (window.app) {
            window.app.currentUser = null;
            window.app.isAuthenticated = false;
        }

        this.showNotification('Logged out successfully', 'info');
    }

    checkAuthStatus() {
        const token = localStorage.getItem('authToken');
        const userData = localStorage.getItem('userData');

        if (token && userData) {
            try {
                this.currentUser = JSON.parse(userData);
                this.isAuthenticated = true;
                this.updateNavigation();
            } catch (error) {
                // Invalid data, clear it
                localStorage.removeItem('authToken');
                localStorage.removeItem('userData');
            }
        }
    }

    showNotification(message, type = 'info') {
        // Use app notification if available, otherwise create our own
        if (window.app && window.app.showNotification) {
            window.app.showNotification(message, type);
        } else {
            // Fallback notification
            this.createNotification(message, type);
        }
    }

    createNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close">&times;</button>
        `;

        document.body.appendChild(notification);

        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Auto hide after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);

        // Close button functionality
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        });
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Method to check if user is authenticated
    isUserAuthenticated() {
        return this.isAuthenticated;
    }

    // Method to get current user
    getCurrentUser() {
        return this.currentUser;
    }

    // Method to check if user is a driver
    isDriver() {
        return this.currentUser && this.currentUser.userType === 'driver';
    }

    // Method to check if user is a rider
    isRider() {
        return this.currentUser && this.currentUser.userType === 'rider';
    }

    // Method to refresh auth token
    async refreshToken() {
        // This would typically make an API call to refresh the token
        const token = localStorage.getItem('authToken');
        if (token) {
            // Simulate token refresh
            await new Promise(resolve => setTimeout(resolve, 1000));
            return true;
        }
        return false;
    }
}

// Initialize auth manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.authManager = new AuthManager();
});

// Add additional styles for auth-specific elements
const authStyles = `
    <style>
        .user-name {
            color: #667eea;
            font-weight: 500;
            margin-right: 1rem;
        }
        
        .modal input:invalid,
        .modal select:invalid {
            border-color: #dc3545;
        }
        
        .modal input:valid,
        .modal select:valid {
            border-color: #28a745;
        }
        
        .form-error {
            color: #dc3545;
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }
        
        .password-strength {
            margin-top: 0.5rem;
            font-size: 0.875rem;
        }
        
        .password-strength.weak { color: #dc3545; }
        .password-strength.medium { color: #ffc107; }
        .password-strength.strong { color: #28a745; }
    </style>
`;

document.head.insertAdjacentHTML('beforeend', authStyles);
