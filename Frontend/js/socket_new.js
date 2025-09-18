// Socket.IO Integration JavaScript
class SocketManager {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.eventListeners = new Map();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.connect();
    }

    setupEventListeners() {
        // Listen for authentication changes
        if (window.authManager) {
            // Check periodically for auth changes
            setInterval(() => {
                this.checkAuthAndReconnect();
            }, 10000);
        }

        // Listen for page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Page hidden - could pause some operations
            } else {
                // Page visible - resume operations
                if (!this.isConnected) {
                    this.connect();
                }
            }
        });

        // Listen for online/offline events
        window.addEventListener('online', () => {
            this.handleOnline();
        });

        window.addEventListener('offline', () => {
            this.handleOffline();
        });
    }

    connect() {
        try {
            const serverUrl = this.getServerURL();
            console.log('Connecting to Socket.IO server:', serverUrl);
            console.log('Socket.IO library available:', typeof io !== 'undefined');

            // Create Socket.IO connection
            this.socket = io(serverUrl, {
                transports: ['websocket', 'polling'],
                timeout: 10000,
                reconnection: true,
                reconnectionAttempts: this.maxReconnectAttempts,
                reconnectionDelay: 1000
            });

            this.setupSocketEventHandlers();

        } catch (error) {
            console.error('Failed to create Socket.IO connection:', error);
            this.scheduleReconnect();
        }
    }

    getServerURL() {
        // Use MongoDB-enabled backend with Socket.IO support
        return 'http://localhost:5000';
    }

    setupSocketEventHandlers() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('Socket.IO connection established');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.authenticate();
            this.emit('connected');
        });

        this.socket.on('disconnect', (reason) => {
            console.log('Socket.IO connection closed:', reason);
            this.isConnected = false;
            this.emit('disconnected', { reason });
        });

        this.socket.on('connect_error', (error) => {
            console.error('Socket.IO connection error:', error);
            this.isConnected = false;
        });

        // Custom events
        this.socket.on('connected', (data) => {
            console.log('Server confirmed connection:', data);
        });

        this.socket.on('authenticated', (data) => {
            console.log('Authentication response:', data);
        });

        this.socket.on('pong', (data) => {
            console.log('Pong received:', data);
            this.handlePong(data);
        });

        // Ride-related events
        this.socket.on('ride_update', (data) => {
            this.handleRideUpdate(data);
        });

        this.socket.on('driver_location', (data) => {
            this.handleDriverLocation(data);
        });

        this.socket.on('ride_request', (data) => {
            this.handleRideRequest(data);
        });

        this.socket.on('notification', (data) => {
            this.handleNotification(data);
        });
    }

    handleRideUpdate(payload) {
        const { rideId, status, driverInfo, eta } = payload;

        // Update ride status if ride manager exists
        if (window.rideManager) {
            window.rideManager.updateRideStatus(rideId, status, driverInfo, eta);
        }

        // Show notification
        this.showNotification(`Ride ${status}: ${eta || ''}`, 'info');
    }

    handleDriverLocation(payload) {
        const { driverId, location, rideId } = payload;

        // Update driver location on map if map manager exists
        if (window.mapManager) {
            window.mapManager.updateDriverLocation(driverId, location, rideId);
        }
    }

    handleRideRequest(payload) {
        const { requestId, pickup, destination, distance, estimatedFare } = payload;

        // Show ride request to driver if driver manager exists
        if (window.driverManager && window.driverManager.isDriverOnline()) {
            window.driverManager.receiveRideRequest({
                id: requestId,
                pickup,
                destination,
                distance,
                estimatedFare,
                timestamp: new Date().toISOString()
            });
        }
    }

    handleNotification(payload) {
        const { message, type, title } = payload;

        // Show notification
        this.showNotification(message, type, title);
    }

    handlePong(data) {
        // Handle pong response
        this.lastPongTime = Date.now();
    }

    checkAuthAndReconnect() {
        // Check if user is authenticated and reconnect if needed
        if (window.authManager && window.authManager.isUserAuthenticated() && !this.isConnected) {
            console.log('User authenticated but socket disconnected, attempting reconnect');
            this.connect();
        }
    }

    authenticate() {
        // Send authentication message if user is logged in
        if (window.authManager && window.authManager.isUserAuthenticated() && this.isConnected) {
            const user = window.authManager.getCurrentUser();
            this.socket.emit('authenticate', {
                userId: user.id,
                userType: user.userType,
                token: localStorage.getItem('authToken')
            });
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.emit('reconnect_failed');
            return;
        }

        this.reconnectAttempts++;
        const delay = 1000 * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);

        setTimeout(() => {
            if (!this.isConnected) {
                this.connect();
            }
        }, delay);
    }

    // Send methods
    send(eventName, data) {
        if (this.isConnected && this.socket) {
            this.socket.emit(eventName, data);
        } else {
            console.warn('Socket not connected, cannot send:', eventName, data);
        }
    }

    sendPing() {
        this.send('ping', { timestamp: Date.now() });
    }

    // Public methods for external use
    sendRideRequest(rideDetails) {
        this.send('ride_request', rideDetails);
    }

    updateDriverLocation(location) {
        this.send('driver_location', location);
    }

    acceptRide(rideId) {
        this.send('accept_ride', { rideId });
    }

    declineRide(rideId) {
        this.send('decline_ride', { rideId });
    }

    startRide(rideId) {
        this.send('start_ride', { rideId });
    }

    completeRide(rideId) {
        this.send('complete_ride', { rideId });
    }

    cancelRide(rideId, reason) {
        this.send('cancel_ride', { rideId, reason });
    }

    // Event system
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.eventListeners.has(event)) {
            const callbacks = this.eventListeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Error in event callback:', error);
                }
            });
        }
    }

    // Connection management
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }

    reconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
        this.connect();
    }

    // Utility methods
    isSocketConnected() {
        return this.isConnected && this.socket && this.socket.connected;
    }

    getConnectionStatus() {
        if (!this.socket) return 'disconnected';
        return this.socket.connected ? 'connected' : 'disconnected';
    }

    showNotification(message, type = 'info', title = '') {
        // Use app notification if available
        if (window.app && window.app.showNotification) {
            window.app.showNotification(message, type);
        } else {
            // Fallback notification
            console.log(`${type.toUpperCase()}: ${title ? title + ' - ' : ''}${message}`);
        }
    }

    // Handle online/offline events
    handleOnline() {
        console.log('Network connection restored');
        if (!this.isConnected) {
            this.connect();
        }
    }

    handleOffline() {
        console.log('Network connection lost');
        this.isConnected = false;
    }

    // Cleanup
    destroy() {
        this.disconnect();
        this.eventListeners.clear();

        if (this.socket) {
            this.socket.removeAllListeners();
            this.socket = null;
        }
    }
}

// Initialize socket manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait for io to be available
    if (typeof io !== 'undefined') {
        window.socketManager = new SocketManager();
    } else {
        console.error('Socket.IO library not loaded');
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.socketManager) {
        window.socketManager.destroy();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SocketManager;
}