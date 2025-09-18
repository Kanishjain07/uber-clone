// Driver Management JavaScript
class DriverManager {
    constructor() {
        this.isDriver = false;
        this.driverStatus = 'offline'; // offline, online, busy
        this.currentRide = null;
        this.earnings = 0;
        this.rating = 0;
        this.totalRides = 0;
        this.driverLocation = null;
        this.socket = null;
        this.locationWatcher = null;
        this.init();
    }

    init() {
        this.checkDriverStatus();
        this.setupEventListeners();
        this.initializeDriverDashboard();
        this.setupLocationTracking();
    }

    checkDriverStatus() {
        // Get current user from localStorage or authentication manager
        const authToken = localStorage.getItem('authToken');
        const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

        if (authToken && currentUser.user_type === 'driver') {
            this.isDriver = true;
            this.loadDriverData();
        }
    }

    setupEventListeners() {
        // Status toggle
        const onlineStatus = document.getElementById('onlineStatus');
        if (onlineStatus) {
            onlineStatus.addEventListener('change', (e) => {
                this.toggleDriverStatus(e.target.checked);
            });
        }

        // Ride action buttons
        const startRideBtn = document.getElementById('startRideBtn');
        if (startRideBtn) {
            startRideBtn.addEventListener('click', () => {
                this.startRide();
            });
        }

        const completeRideBtn = document.getElementById('completeRideBtn');
        if (completeRideBtn) {
            completeRideBtn.addEventListener('click', () => {
                this.completeRide();
            });
        }

        const cancelRideBtn = document.getElementById('cancelRideBtn');
        if (cancelRideBtn) {
            cancelRideBtn.addEventListener('click', () => {
                this.cancelRide();
            });
        }
    }

    initializeDriverDashboard() {
        if (this.isDriver) {
            this.updateDashboardUI();
            this.loadTodaysEarnings();
            this.loadRecentRides();
            this.initializeMap();
        }
    }

    async toggleDriverStatus(isOnline) {
        try {
            const api = window.apiHelper || new APIHelper();
            const status = isOnline ? 'online' : 'offline';

            const response = await api.request('/api/drivers/status', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                },
                body: JSON.stringify({ status })
            });

            if (response.success) {
                this.driverStatus = status;
                this.updateStatusDisplay();

                if (isOnline) {
                    this.startLocationTracking();
                } else {
                    this.stopLocationTracking();
                }
            }
        } catch (error) {
            console.error('Failed to update driver status:', error);
            this.showNotification('Failed to update status', 'error');
        }
    }

    updateStatusDisplay() {
        const statusText = document.getElementById('statusText');
        const onlineStatus = document.getElementById('onlineStatus');

        if (statusText) {
            statusText.textContent = this.driverStatus === 'online' ? 'Online' : 'Offline';
            statusText.className = this.driverStatus === 'online' ? 'status-online' : 'status-offline';
        }

        if (onlineStatus) {
            onlineStatus.checked = this.driverStatus === 'online';
        }
    }

    async loadDriverData() {
        try {
            const api = window.apiHelper || new APIHelper();
            const response = await api.request('/api/drivers/profile', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (response.success && response.data) {
                this.earnings = response.data.earnings || 0;
                this.rating = response.data.rating || 0;
                this.totalRides = response.data.total_rides || 0;
                this.driverStatus = response.data.status || 'offline';
            }
        } catch (error) {
            console.error('Failed to load driver data:', error);
        }
    }

    updateDashboardUI() {
        this.updateStatusDisplay();

        const totalRidesEl = document.getElementById('totalRides');
        const totalEarningsEl = document.getElementById('totalEarnings');

        if (totalRidesEl) totalRidesEl.textContent = this.totalRides;
        if (totalEarningsEl) totalEarningsEl.textContent = `$${this.earnings.toFixed(2)}`;
    }

    async loadTodaysEarnings() {
        try {
            const api = window.apiHelper || new APIHelper();
            const today = new Date().toISOString().split('T')[0];

            const response = await api.request(`/api/drivers/earnings?date=${today}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (response.success && response.data) {
                const todaysEarnings = response.data.total_earnings || 0;
                const todaysRides = response.data.total_rides || 0;

                const totalRidesEl = document.getElementById('totalRides');
                const totalEarningsEl = document.getElementById('totalEarnings');

                if (totalRidesEl) totalRidesEl.textContent = todaysRides;
                if (totalEarningsEl) totalEarningsEl.textContent = `$${todaysEarnings.toFixed(2)}`;
            }
        } catch (error) {
            console.error('Failed to load earnings:', error);
        }
    }

    async loadRecentRides() {
        try {
            const api = window.apiHelper || new APIHelper();
            const response = await api.request('/api/rides/history?limit=5', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (response.success && response.data) {
                this.displayRecentRides(response.data.rides || []);
            }
        } catch (error) {
            console.error('Failed to load recent rides:', error);
        }
    }

    displayRecentRides(rides) {
        const recentRidesList = document.getElementById('recentRidesList');
        if (!recentRidesList) return;

        if (rides.length === 0) {
            recentRidesList.innerHTML = '<p>No recent rides</p>';
            return;
        }

        recentRidesList.innerHTML = rides.map(ride => `
            <div class="ride-item">
                <div class="ride-info">
                    <p><strong>From:</strong> ${ride.pickup_address}</p>
                    <p><strong>To:</strong> ${ride.destination_address}</p>
                    <p><strong>Fare:</strong> $${ride.fare}</p>
                    <p><strong>Date:</strong> ${new Date(ride.created_at).toLocaleDateString()}</p>
                </div>
                <div class="ride-status ${ride.status}">${ride.status}</div>
            </div>
        `).join('');
    }

    initializeMap() {
        if (typeof google !== 'undefined' && google.maps) {
            const mapContainer = document.getElementById('map-container');
            if (mapContainer) {
                this.map = new google.maps.Map(mapContainer, {
                    center: { lat: 37.7749, lng: -122.4194 }, // San Francisco default
                    zoom: 13,
                    styles: [
                        {
                            featureType: 'poi',
                            elementType: 'labels',
                            stylers: [{ visibility: 'off' }]
                        }
                    ]
                });

                // Add driver marker
                this.driverMarker = new google.maps.Marker({
                    map: this.map,
                    title: 'Your Location',
                    icon: {
                        url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <circle cx="12" cy="12" r="8" fill="#007bff"/>
                                <circle cx="12" cy="12" r="3" fill="white"/>
                            </svg>
                        `),
                        scaledSize: new google.maps.Size(24, 24)
                    }
                });
            }
        }
    }

    setupLocationTracking() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.driverLocation = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    this.updateDriverLocationOnMap();
                },
                (error) => {
                    console.error('Error getting location:', error);
                }
            );
        }
    }

    startLocationTracking() {
        if (this.locationWatcher) {
            navigator.geolocation.clearWatch(this.locationWatcher);
        }

        this.locationWatcher = navigator.geolocation.watchPosition(
            (position) => {
                this.driverLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                this.updateDriverLocationOnMap();
                this.sendLocationUpdate();
            },
            (error) => {
                console.error('Location tracking error:', error);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 30000
            }
        );
    }

    stopLocationTracking() {
        if (this.locationWatcher) {
            navigator.geolocation.clearWatch(this.locationWatcher);
            this.locationWatcher = null;
        }
    }

    updateDriverLocationOnMap() {
        if (this.map && this.driverMarker && this.driverLocation) {
            this.driverMarker.setPosition(this.driverLocation);
            this.map.setCenter(this.driverLocation);
        }
    }

    async sendLocationUpdate() {
        if (!this.driverLocation) return;

        try {
            const api = window.apiHelper || new APIHelper();
            await api.request('/api/drivers/location', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                },
                body: JSON.stringify({
                    latitude: this.driverLocation.lat,
                    longitude: this.driverLocation.lng
                })
            });
        } catch (error) {
            console.error('Failed to update location:', error);
        }
    }

    async startRide() {
        if (!this.currentRide) return;

        try {
            const api = window.apiHelper || new APIHelper();
            const response = await api.request(`/api/rides/${this.currentRide._id}/start`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (response.success) {
                this.currentRide.status = 'started';
                this.updateCurrentRideDisplay();
                this.showNotification('Ride started!', 'success');
            }
        } catch (error) {
            console.error('Failed to start ride:', error);
            this.showNotification('Failed to start ride', 'error');
        }
    }

    async completeRide() {
        if (!this.currentRide) return;

        try {
            const api = window.apiHelper || new APIHelper();
            const response = await api.request(`/api/rides/${this.currentRide._id}/complete`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (response.success) {
                this.currentRide = null;
                this.updateCurrentRideDisplay();
                this.loadTodaysEarnings();
                this.showNotification('Ride completed!', 'success');
            }
        } catch (error) {
            console.error('Failed to complete ride:', error);
            this.showNotification('Failed to complete ride', 'error');
        }
    }

    async cancelRide() {
        if (!this.currentRide) return;

        try {
            const api = window.apiHelper || new APIHelper();
            const response = await api.request(`/api/rides/${this.currentRide._id}/cancel`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (response.success) {
                this.currentRide = null;
                this.updateCurrentRideDisplay();
                this.showNotification('Ride cancelled', 'info');
            }
        } catch (error) {
            console.error('Failed to cancel ride:', error);
            this.showNotification('Failed to cancel ride', 'error');
        }
    }

    updateCurrentRideDisplay() {
        const noRideMessage = document.getElementById('noRideMessage');
        const rideDetails = document.getElementById('rideDetails');

        if (!this.currentRide) {
            if (noRideMessage) noRideMessage.style.display = 'block';
            if (rideDetails) rideDetails.style.display = 'none';
            return;
        }

        if (noRideMessage) noRideMessage.style.display = 'none';
        if (rideDetails) rideDetails.style.display = 'block';

        // Update ride details
        const passengerName = document.getElementById('passengerName');
        const pickupLocation = document.getElementById('pickupLocation');
        const dropoffLocation = document.getElementById('dropoffLocation');
        const rideStatus = document.getElementById('rideStatus');

        if (passengerName) passengerName.textContent = this.currentRide.passenger_name || 'Unknown';
        if (pickupLocation) pickupLocation.textContent = this.currentRide.pickup_address || 'Unknown';
        if (dropoffLocation) dropoffLocation.textContent = this.currentRide.destination_address || 'Unknown';
        if (rideStatus) rideStatus.textContent = this.currentRide.status || 'Unknown';

        // Update button visibility
        const startBtn = document.getElementById('startRideBtn');
        const completeBtn = document.getElementById('completeRideBtn');

        if (startBtn) {
            startBtn.style.display = this.currentRide.status === 'accepted' ? 'block' : 'none';
        }
        if (completeBtn) {
            completeBtn.style.display = this.currentRide.status === 'started' ? 'block' : 'none';
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#dc3545' : type === 'success' ? '#28a745' : '#007bff'};
            color: white;
            padding: 12px 20px;
            border-radius: 5px;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        `;

        // Add to page
        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize driver manager when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.driverManager = new DriverManager();
});

// Initialize on window load as backup
window.addEventListener('load', () => {
    if (!window.driverManager) {
        window.driverManager = new DriverManager();
    }
});