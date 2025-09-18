// Main App JavaScript
class UberCloneApp {
    constructor() {
        this.currentUser = null;
        this.isAuthenticated = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupMobileMenu();
        this.setupSmoothScrolling();
        this.setupScrollEffects();
        this.checkAuthStatus();
        this.restoreSelectedRideType();
    }

    setupEventListeners() {
        // Setup ride dropdown
        this.setupRideDropdown();

        // Book ride button (now opens dropdown)
        const bookRideBtn = document.getElementById('bookRideBtn');
        if (bookRideBtn) {
            bookRideBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleRideDropdown();
            });
        }

        // Become driver button
        const becomeDriverBtn = document.getElementById('becomeDriverBtn');
        if (becomeDriverBtn) {
            becomeDriverBtn.addEventListener('click', () => {
                // Show registration modal and pre-select driver
                if (window.authManager) {
                    window.authManager.showRegisterModal('driver');
                } else {
                    // Fallback: show register modal directly
                    const registerModal = document.getElementById('registerModal');
                    if (registerModal) {
                        registerModal.style.display = 'block';
                        // Pre-select driver option
                        const userTypeSelect = registerModal.querySelector('select');
                        if (userTypeSelect) {
                            userTypeSelect.value = 'driver';
                        }
                    }
                }
            });
        }

        // Find ride button
        const findRideBtn = document.getElementById('findRideBtn');
        if (findRideBtn) {
            findRideBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleRideRequest();
            });
        }

        // Contact form
        const contactForm = document.getElementById('contactForm');
        if (contactForm) {
            contactForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleContactForm();
            });
        }

        // Window scroll event for navbar effects
        window.addEventListener('scroll', () => {
            this.handleScroll();
        });

        // Window resize event
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    setupMobileMenu() {
        const hamburger = document.querySelector('.hamburger');
        const navMenu = document.querySelector('.nav-menu');
        const navAuth = document.querySelector('.nav-auth');

        if (hamburger) {
            hamburger.addEventListener('click', () => {
                hamburger.classList.toggle('active');
                navMenu.classList.toggle('mobile');
                navAuth.classList.toggle('mobile');

                // Animate hamburger
                this.toggleHamburger(hamburger);
            });
        }

        // Close mobile menu when clicking on a link
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('active');
                navMenu.classList.remove('mobile');
                navAuth.classList.remove('mobile');
                this.resetHamburger(hamburger);
            });
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!hamburger.contains(e.target) &&
                !navMenu.contains(e.target) &&
                !navAuth.contains(e.target) &&
                navMenu.classList.contains('mobile')) {
                hamburger.classList.remove('active');
                navMenu.classList.remove('mobile');
                navAuth.classList.remove('mobile');
                this.resetHamburger(hamburger);
            }
        });
    }

    toggleHamburger(hamburger) {
        const spans = hamburger.querySelectorAll('span');
        if (hamburger.classList.contains('active')) {
            spans[0].style.transform = 'rotate(-45deg) translate(-5px, 6px)';
            spans[1].style.opacity = '0';
            spans[2].style.transform = 'rotate(45deg) translate(-5px, -6px)';
        } else {
            this.resetHamburger(hamburger);
        }
    }

    resetHamburger(hamburger) {
        const spans = hamburger.querySelectorAll('span');
        spans.forEach(span => {
            span.style.transform = 'none';
            span.style.opacity = '1';
        });
    }

    setupSmoothScrolling() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                this.scrollToSection(targetId);
            });
        });
    }

    scrollToSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            const offsetTop = section.offsetTop - 80; // Account for fixed navbar
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
    }

    setupScrollEffects() {
        // Add fade-in animation to elements when they come into view
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                }
            });
        }, observerOptions);

        // Observe all sections and cards
        const sections = document.querySelectorAll('section');
        const cards = document.querySelectorAll('.service-card, .stat');
        
        sections.forEach(section => observer.observe(section));
        cards.forEach(card => observer.observe(card));
    }

    handleScroll() {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }

    handleResize() {
        // Handle mobile menu state on resize
        const hamburger = document.querySelector('.hamburger');
        const navMenu = document.querySelector('.nav-menu');
        const navAuth = document.querySelector('.nav-auth');

        if (window.innerWidth > 768) {
            hamburger.classList.remove('active');
            navMenu.classList.remove('mobile');
            navAuth.classList.remove('mobile');
            this.resetHamburger(hamburger);
        }
    }

    async handleRideRequest() {
        const pickup = document.getElementById('pickup').value;
        const destination = document.getElementById('destination').value;
        const rideType = document.getElementById('rideType').value;
        const passengers = document.getElementById('passengers').value;

        if (!pickup || !destination) {
            this.showNotification('Please enter both pickup and destination locations', 'error');
            return;
        }

        if (!this.isAuthenticated) {
            this.showNotification('Please login to book a ride', 'warning');
            return;
        }

        try {
            // Show loading state
            const findRideBtn = document.getElementById('findRideBtn');
            findRideBtn.classList.add('loading');
            findRideBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Finding Ride...';

            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 2000));

            // Show success message
            this.showNotification('Ride request sent! Finding nearby drivers...', 'success');
            
            // Reset form
            document.getElementById('pickup').value = '';
            document.getElementById('destination').value = '';
            document.getElementById('rideType').value = 'economy';
            document.getElementById('passengers').value = '1';

        } catch (error) {
            this.showNotification('Failed to request ride. Please try again.', 'error');
        } finally {
            // Reset button state
            const findRideBtn = document.getElementById('findRideBtn');
            findRideBtn.classList.remove('loading');
            findRideBtn.innerHTML = '<i class="fas fa-search"></i> Find Ride';
        }
    }

    async handleContactForm() {
        const form = document.getElementById('contactForm');
        const formData = new FormData(form);
        
        try {
            // Show loading state
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.classList.add('loading');
            submitBtn.textContent = 'Sending...';

            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1500));

            // Show success message
            this.showNotification('Message sent successfully! We\'ll get back to you soon.', 'success');
            
            // Reset form
            form.reset();

        } catch (error) {
            this.showNotification('Failed to send message. Please try again.', 'error');
        } finally {
            // Reset button state
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.classList.remove('loading');
            submitBtn.textContent = 'Send Message';
        }
    }

    checkAuthStatus() {
        // Check if user is logged in (check localStorage or session)
        const token = localStorage.getItem('authToken');
        if (token) {
            this.isAuthenticated = true;
            this.currentUser = JSON.parse(localStorage.getItem('userData'));
            this.updateUIForAuthenticatedUser();
        }
    }

    updateUIForAuthenticatedUser() {
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
        localStorage.removeItem('authToken');
        localStorage.removeItem('userData');
        this.isAuthenticated = false;
        this.currentUser = null;
        
        // Reload page to reset UI
        window.location.reload();
    }

    // Ride Dropdown Methods
    setupRideDropdown() {
        // Handle dropdown item clicks
        const dropdownItems = document.querySelectorAll('.dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const rideType = item.getAttribute('data-ride-type');
                this.selectRideType(rideType);
            });
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const dropdown = document.querySelector('.ride-dropdown');
            if (dropdown && !dropdown.contains(e.target)) {
                this.closeRideDropdown();
            }
        });
    }

    toggleRideDropdown() {
        const dropdownBtn = document.getElementById('bookRideBtn');
        const dropdownMenu = document.getElementById('rideDropdown');

        if (dropdownMenu.classList.contains('active')) {
            this.closeRideDropdown();
        } else {
            this.openRideDropdown();
        }
    }

    openRideDropdown() {
        const dropdownBtn = document.getElementById('bookRideBtn');
        const dropdownMenu = document.getElementById('rideDropdown');

        dropdownBtn.classList.add('active');
        dropdownMenu.classList.add('active');
    }

    closeRideDropdown() {
        const dropdownBtn = document.getElementById('bookRideBtn');
        const dropdownMenu = document.getElementById('rideDropdown');

        dropdownBtn.classList.remove('active');
        dropdownMenu.classList.remove('active');
    }

    selectRideType(rideType) {
        // Check if user is authenticated
        if (!this.isAuthenticated) {
            this.closeRideDropdown();
            this.showNotification('Please login to book a ride', 'warning');
            // Show login modal
            if (window.authManager) {
                window.authManager.showLoginModal();
            } else {
                // Fallback: show login modal directly
                const loginModal = document.getElementById('loginModal');
                if (loginModal) {
                    loginModal.style.display = 'block';
                }
            }
            return;
        }

        // User is authenticated, proceed with ride booking
        this.closeRideDropdown();
        this.proceedWithRideBooking(rideType);
    }

    proceedWithRideBooking(rideType) {
        // Store selected ride type
        localStorage.setItem('selectedRideType', rideType);

        // Update UI to show selected ride type
        const rideTypeSelect = document.getElementById('rideType');
        if (rideTypeSelect) {
            rideTypeSelect.value = rideType;
        }

        // Scroll to booking section
        this.scrollToSection('ride-booking');

        // Show success message
        const rideTypeNames = {
            'economy': 'Economy',
            'comfort': 'Comfort',
            'premium': 'Premium',
            'pool': 'Pool'
        };

        this.showNotification(`${rideTypeNames[rideType]} ride selected. Please enter your pickup and destination.`, 'success');

        // Update map for ride type if map manager exists
        if (window.mapManager) {
            window.mapManager.updateMapForRideType(rideType);
        }
    }

    restoreSelectedRideType() {
        // Restore previously selected ride type from localStorage
        const selectedRideType = localStorage.getItem('selectedRideType');
        if (selectedRideType) {
            const rideTypeSelect = document.getElementById('rideType');
            if (rideTypeSelect) {
                rideTypeSelect.value = selectedRideType;
            }
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close">&times;</button>
        `;

        // Add to page
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

    // Utility method to format currency
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    // Utility method to format time
    formatTime(date) {
        return new Intl.DateTimeFormat('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        }).format(date);
    }

    // Method to show loading state
    showLoading(element) {
        element.classList.add('loading');
        element.disabled = true;
    }

    // Method to hide loading state
    hideLoading(element) {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new UberCloneApp();
});

// Add notification styles to head
const notificationStyles = `
    <style>
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            padding: 1rem;
            min-width: 300px;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            z-index: 10000;
        }
        
        .notification.show {
            transform: translateX(0);
        }
        
        .notification-content {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .notification-success {
            border-left: 4px solid #28a745;
        }
        
        .notification-error {
            border-left: 4px solid #dc3545;
        }
        
        .notification-warning {
            border-left: 4px solid #ffc107;
        }
        
        .notification-info {
            border-left: 4px solid #17a2b8;
        }
        
        .notification-close {
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background: none;
            border: none;
            font-size: 1.2rem;
            cursor: pointer;
            color: #666;
        }
        
        .notification-close:hover {
            color: #333;
        }
        
        .navbar.scrolled {
            background: rgba(255, 255, 255, 0.98);
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
        }
        
        .hamburger.active span:nth-child(1) {
            transform: rotate(-45deg) translate(-5px, 6px);
        }
        
        .hamburger.active span:nth-child(2) {
            opacity: 0;
        }
        
        .hamburger.active span:nth-child(3) {
            transform: rotate(45deg) translate(-5px, -6px);
        }
        
        @media (max-width: 768px) {
            .nav-menu.active,
            .nav-auth.active {
                display: flex;
                flex-direction: column;
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: white;
                padding: 1rem;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            
            .nav-menu.active {
                top: 100%;
            }
            
            .nav-auth.active {
                top: calc(100% + 200px);
            }
        }
    </style>
`;

document.head.insertAdjacentHTML('beforeend', notificationStyles);
