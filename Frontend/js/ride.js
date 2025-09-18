// Ride Management JavaScript
class RideManager {
    constructor() {
        this.currentRide = null;
        this.rideStatus = 'idle'; // idle, searching, matched, enroute, completed, cancelled
        this.driverInfo = null;
        this.rideTimer = null;
        this.rideStartTime = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupRideForm();
        this.checkExistingRide();
    }

    setupEventListeners() {
        // Ride type change
        const rideTypeSelect = document.getElementById('rideType');
        if (rideTypeSelect) {
            rideTypeSelect.addEventListener('change', (e) => {
                this.handleRideTypeChange(e.target.value);
            });
        }

        // Passenger count change
        const passengersSelect = document.getElementById('passengers');
        if (passengersSelect) {
            passengersSelect.addEventListener('change', (e) => {
                this.handlePassengerChange(e.target.value);
            });
        }

        // Find ride button
        const findRideBtn = document.getElementById('findRideBtn');
        if (findRideBtn) {
            findRideBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.requestRide();
            });
        }
    }

    setupRideForm() {
        // Add real-time validation and suggestions
        const pickupInput = document.getElementById('pickup');
        const destinationInput = document.getElementById('destination');

        if (pickupInput) {
            pickupInput.addEventListener('focus', () => {
                this.showLocationSuggestions('pickup');
            });
        }

        if (destinationInput) {
            destinationInput.addEventListener('focus', () => {
                this.showLocationSuggestions('destination');
            });
        }
    }

    showLocationSuggestions(fieldType) {
        // This would integrate with the map manager for location suggestions
        if (window.mapManager) {
            console.log(`Showing location suggestions for ${fieldType}`);
        }
    }

    handleRideTypeChange(rideType) {
        // Update pricing and estimated time based on ride type
        this.updateRideEstimates();
        
        // Update map styling if needed
        if (window.mapManager) {
            window.mapManager.updateMapForRideType(rideType);
        }

        // Store selection for ride request
        this.currentRideType = rideType;
    }

    handlePassengerChange(passengerCount) {
        // Update ride estimates based on passenger count
        this.updateRideEstimates();
        
        // Store selection for ride request
        this.currentPassengerCount = passengerCount;
    }

    updateRideEstimates() {
        // This would recalculate estimates when ride parameters change
        // For now, we'll just log the change
        const rideType = document.getElementById('rideType')?.value || 'economy';
        const passengers = document.getElementById('passengers')?.value || '1';
        
        console.log(`Ride estimates updated: ${rideType} ride for ${passengers} passenger(s)`);
    }

    async requestRide() {
        // Validate form inputs
        if (!this.validateRideRequest()) {
            return;
        }

        // Check if user is authenticated
        if (!this.isUserAuthenticated()) {
            this.showNotification('Please login to request a ride', 'warning');
            return;
        }

        try {
            // Show loading state
            this.showRideRequestLoading();

            // Get ride details
            const rideDetails = this.getRideDetails();

            // Make API request
            const response = await this.submitRideRequest(rideDetails);

            if (response.success) {
                this.handleRideRequestSuccess(response.data);
            } else {
                this.handleRideRequestError(response.message);
            }

        } catch (error) {
            console.error('Ride request error:', error);
            this.handleRideRequestError('Failed to request ride. Please try again.');
        } finally {
            this.hideRideRequestLoading();
        }
    }

    validateRideRequest() {
        const pickup = document.getElementById('pickup')?.value?.trim();
        const destination = document.getElementById('destination')?.value?.trim();
        const rideType = document.getElementById('rideType')?.value;
        const passengers = document.getElementById('passengers')?.value;

        if (!pickup) {
            this.showNotification('Please enter pickup location', 'error');
            return false;
        }

        if (!destination) {
            this.showNotification('Please enter destination', 'error');
            return false;
        }

        if (pickup === destination) {
            this.showNotification('Pickup and destination cannot be the same', 'error');
            return false;
        }

        if (!rideType) {
            this.showNotification('Please select ride type', 'error');
            return false;
        }

        if (!passengers) {
            this.showNotification('Please select number of passengers', 'error');
            return false;
        }

        return true;
    }

    isUserAuthenticated() {
        return window.authManager && window.authManager.isUserAuthenticated();
    }

    getRideDetails() {
        return {
            pickup: document.getElementById('pickup').value.trim(),
            destination: document.getElementById('destination').value.trim(),
            rideType: document.getElementById('rideType').value,
            passengers: parseInt(document.getElementById('passengers').value),
            timestamp: new Date().toISOString(),
            userId: window.authManager?.getCurrentUser()?.id
        };
    }

    async submitRideRequest(rideDetails) {
        // Use API helper if available, otherwise simulate
        if (window.api) {
            return await window.api.smartRequest('/rides/request', {
                method: 'POST',
                body: rideDetails
            });
        } else {
            // Simulate API call
            return await this.simulateRideRequest(rideDetails);
        }
    }

    async simulateRideRequest(rideDetails) {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Simulate successful ride request
        return {
            success: true,
            data: {
                rideId: 'ride_' + Date.now(),
                status: 'searching',
                estimatedTime: '3-5 minutes',
                estimatedFare: this.calculateEstimatedFare(rideDetails),
                timestamp: new Date().toISOString()
            }
        };
    }

    calculateEstimatedFare(rideDetails) {
        // Simple fare calculation
        const baseFare = 2.50;
        const perMileRate = 1.50;
        
        // Estimate distance (in real app, this would come from map calculations)
        const estimatedDistance = 2.5; // miles
        
        const fare = baseFare + (estimatedDistance * perMileRate);
        
        // Apply ride type multiplier
        const multipliers = {
            economy: 1.0,
            comfort: 1.3,
            premium: 1.8
        };
        
        return (fare * multipliers[rideDetails.rideType]).toFixed(2);
    }

    handleRideRequestSuccess(rideData) {
        // Store ride information
        this.currentRide = rideData;
        this.rideStatus = 'searching';
        this.rideStartTime = new Date();

        // Update UI
        this.showRideStatus('searching');
        this.showDriverSearching();
        this.startRideTimer();

        // Show success notification
        this.showNotification('Ride request submitted! Searching for drivers...', 'success');

        // Simulate driver matching process
        this.simulateDriverMatching();
    }

    handleRideRequestError(message) {
        this.showNotification(message, 'error');
    }

    showRideRequestLoading() {
        const findRideBtn = document.getElementById('findRideBtn');
        if (findRideBtn) {
            findRideBtn.classList.add('loading');
            findRideBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Finding Ride...';
            findRideBtn.disabled = true;
        }
    }

    hideRideRequestLoading() {
        const findRideBtn = document.getElementById('findRideBtn');
        if (findRideBtn) {
            findRideBtn.classList.remove('loading');
            findRideBtn.innerHTML = '<i class="fas fa-search"></i> Find Ride';
            findRideBtn.disabled = false;
        }
    }

    showRideStatus(status) {
        // Create or update ride status display
        let statusDisplay = document.getElementById('ride-status-display');
        if (!statusDisplay) {
            statusDisplay = document.createElement('div');
            statusDisplay.id = 'ride-status-display';
            statusDisplay.className = 'ride-status-display';
            statusDisplay.style.cssText = `
                background: white;
                padding: 1.5rem;
                border-radius: 16px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                margin-top: 2rem;
                text-align: center;
            `;
            
            const rideForm = document.querySelector('.ride-form');
            if (rideForm) {
                rideForm.parentNode.insertBefore(statusDisplay, rideForm.nextSibling);
            }
        }

        const statusMessages = {
            searching: '🔍 Searching for drivers...',
            matched: '✅ Driver found!',
            enroute: '🚗 Driver is on the way',
            completed: '🎉 Ride completed!',
            cancelled: '❌ Ride cancelled'
        };

        statusDisplay.innerHTML = `
            <h3>${statusMessages[status] || 'Processing...'}</h3>
            <div id="ride-details"></div>
        `;
    }

    showDriverSearching() {
        const detailsContainer = document.getElementById('ride-details');
        if (detailsContainer) {
            detailsContainer.innerHTML = `
                <div style="margin: 1rem 0;">
                    <div class="loading-spinner"></div>
                    <p>Finding the best driver for you...</p>
                </div>
            `;
        }
    }

    startRideTimer() {
        this.rideTimer = setInterval(() => {
            this.updateRideTimer();
        }, 1000);
    }

    updateRideTimer() {
        if (!this.rideStartTime) return;

        const elapsed = Math.floor((new Date() - this.rideStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;

        const detailsContainer = document.getElementById('ride-details');
        if (detailsContainer && this.rideStatus === 'searching') {
            const existingTimer = detailsContainer.querySelector('.ride-timer');
            if (existingTimer) {
                existingTimer.textContent = `Searching for ${minutes}:${seconds.toString().padStart(2, '0')}`;
            }
        }
    }

    simulateDriverMatching() {
        // Simulate driver matching process
        setTimeout(() => {
            this.matchDriver();
        }, 3000 + Math.random() * 4000); // Random delay between 3-7 seconds
    }

    matchDriver() {
        // Simulate driver match
        this.driverInfo = {
            id: 'driver_' + Date.now(),
            name: this.getRandomDriverName(),
            rating: (4.5 + Math.random() * 0.5).toFixed(1),
            vehicle: this.getRandomVehicle(),
            photo: this.getRandomDriverPhoto(),
            eta: '3-5 minutes'
        };

        this.rideStatus = 'matched';
        this.showRideStatus('matched');
        this.showDriverInfo();
        this.showRideActions();

        // Simulate driver arrival
        setTimeout(() => {
            this.driverArrived();
        }, 2000 + Math.random() * 3000);
    }

    getRandomDriverName() {
        const names = ['John', 'Sarah', 'Mike', 'Emma', 'David', 'Lisa', 'Alex', 'Maria'];
        return names[Math.floor(Math.random() * names.length)];
    }

    getRandomVehicle() {
        const vehicles = ['Toyota Camry', 'Honda Civic', 'Ford Focus', 'Nissan Altima', 'Chevrolet Malibu'];
        return vehicles[Math.floor(Math.random() * vehicles.length)];
    }

    getRandomDriverPhoto() {
        // Placeholder for driver photo
        return 'https://via.placeholder.com/60x60/667eea/ffffff?text=DR';
    }

    showDriverInfo() {
        const detailsContainer = document.getElementById('ride-details');
        if (detailsContainer && this.driverInfo) {
            detailsContainer.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; gap: 1rem; margin: 1rem 0;">
                    <img src="${this.driverInfo.photo}" alt="Driver" style="width: 60px; height: 60px; border-radius: 50%;">
                    <div style="text-align: left;">
                        <h4 style="margin: 0 0 0.5rem 0;">${this.driverInfo.name}</h4>
                        <p style="margin: 0 0 0.25rem 0; color: #666;">
                            ⭐ ${this.driverInfo.rating} • ${this.driverInfo.vehicle}
                        </p>
                        <p style="margin: 0; color: #667eea; font-weight: 500;">
                            ETA: ${this.driverInfo.eta}
                        </p>
                    </div>
                </div>
            `;
        }
    }

    showRideActions() {
        const statusDisplay = document.getElementById('ride-status-display');
        if (statusDisplay) {
            const actionsDiv = document.createElement('div');
            actionsDiv.style.cssText = 'margin-top: 1rem; display: flex; gap: 1rem; justify-content: center;';
            
            actionsDiv.innerHTML = `
                <button class="btn btn-outline" onclick="window.rideManager.contactDriver()">
                    <i class="fas fa-phone"></i> Contact Driver
                </button>
                <button class="btn btn-outline" onclick="window.rideManager.cancelRide()">
                    <i class="fas fa-times"></i> Cancel Ride
                </button>
            `;
            
            statusDisplay.appendChild(actionsDiv);
        }
    }

    driverArrived() {
        this.rideStatus = 'enroute';
        this.showRideStatus('enroute');
        
        // Update driver info to show "arrived"
        const detailsContainer = document.getElementById('ride-details');
        if (detailsContainer) {
            const etaElement = detailsContainer.querySelector('p:last-child');
            if (etaElement) {
                etaElement.innerHTML = '<span style="color: #28a745;">✅ Driver has arrived!</span>';
            }
        }

        // Simulate ride completion
        setTimeout(() => {
            this.completeRide();
        }, 5000 + Math.random() * 5000);
    }

    completeRide() {
        this.rideStatus = 'completed';
        this.showRideStatus('completed');
        
        // Stop timer
        if (this.rideTimer) {
            clearInterval(this.rideTimer);
            this.rideTimer = null;
        }

        // Show completion details
        this.showRideCompletion();
        
        // Reset after delay
        setTimeout(() => {
            this.resetRide();
        }, 5000);
    }

    showRideCompletion() {
        const detailsContainer = document.getElementById('ride-details');
        if (detailsContainer) {
            const rideDuration = this.rideStartTime ? 
                Math.floor((new Date() - this.rideStartTime) / 1000 / 60) : 0;
            
            detailsContainer.innerHTML = `
                <div style="margin: 1rem 0;">
                    <h4 style="color: #28a745; margin-bottom: 1rem;">Ride Completed Successfully!</h4>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; text-align: center;">
                        <div>
                            <strong>Duration</strong><br>
                            ${rideDuration} minutes
                        </div>
                        <div>
                            <strong>Driver</strong><br>
                            ${this.driverInfo?.name || 'Unknown'}
                        </div>
                    </div>
                    <div style="margin-top: 1rem;">
                        <button class="btn btn-primary" onclick="window.rideManager.rateDriver()">
                            <i class="fas fa-star"></i> Rate Driver
                        </button>
                    </div>
                </div>
            `;
        }
    }

    contactDriver() {
        // Simulate contacting driver
        this.showNotification('Connecting you to driver...', 'info');
        
        // In real app, this would initiate a call or chat
        setTimeout(() => {
            this.showNotification('Driver contacted successfully', 'success');
        }, 1000);
    }

    cancelRide() {
        if (confirm('Are you sure you want to cancel this ride?')) {
            this.rideStatus = 'cancelled';
            this.showRideStatus('cancelled');
            
            // Stop timer
            if (this.rideTimer) {
                clearInterval(this.rideTimer);
                this.rideTimer = null;
            }
            
            this.showNotification('Ride cancelled successfully', 'info');
            
            // Reset after delay
            setTimeout(() => {
                this.resetRide();
            }, 3000);
        }
    }

    rateDriver() {
        // Show rating modal
        this.showRatingModal();
    }

    showRatingModal() {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'block';
        
        modal.innerHTML = `
            <div class="modal-content">
                <span class="close" onclick="this.parentElement.parentElement.remove()">&times;</span>
                <h2>Rate Your Driver</h2>
                <div style="text-align: center; margin: 2rem 0;">
                    <div class="rating-stars" style="font-size: 2rem;">
                        ${'★'.repeat(5)}
                    </div>
                    <p>How was your ride with ${this.driverInfo?.name || 'your driver'}?</p>
                </div>
                <button class="btn btn-primary" onclick="this.parentElement.parentElement.remove(); window.rideManager.showNotification('Thank you for your feedback!', 'success')">
                    Submit Rating
                </button>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    resetRide() {
        // Clear ride status display
        const statusDisplay = document.getElementById('ride-status-display');
        if (statusDisplay) {
            statusDisplay.remove();
        }

        // Reset form
        const form = document.querySelector('.ride-form');
        if (form) {
            form.reset();
        }

        // Clear map if available
        if (window.mapManager) {
            window.mapManager.clearMap();
        }

        // Reset internal state
        this.currentRide = null;
        this.rideStatus = 'idle';
        this.driverInfo = null;
        this.rideStartTime = null;
    }

    checkExistingRide() {
        // Check if there's an existing ride in localStorage
        const existingRide = localStorage.getItem('currentRide');
        if (existingRide) {
            try {
                const rideData = JSON.parse(existingRide);
                // Check if ride is still valid (not too old)
                const rideTime = new Date(rideData.timestamp);
                const now = new Date();
                const timeDiff = (now - rideTime) / 1000 / 60; // minutes
                
                if (timeDiff < 60) { // Ride is less than 1 hour old
                    this.currentRide = rideData;
                    this.rideStatus = rideData.status;
                    this.showRideStatus(rideData.status);
                } else {
                    // Clear old ride data
                    localStorage.removeItem('currentRide');
                }
            } catch (error) {
                console.error('Error parsing existing ride:', error);
                localStorage.removeItem('currentRide');
            }
        }
    }

    showNotification(message, type = 'info') {
        // Use app notification if available
        if (window.app && window.app.showNotification) {
            window.app.showNotification(message, type);
        } else {
            // Fallback notification
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    // Public methods for external use
    getCurrentRide() {
        return this.currentRide;
    }

    getRideStatus() {
        return this.rideStatus;
    }

    getDriverInfo() {
        return this.driverInfo;
    }
}

// Initialize ride manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.rideManager = new RideManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RideManager;
}
