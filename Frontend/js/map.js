// Leaflet Map Integration JavaScript
class MapManager {
    constructor() {
        this.map = null;
        this.markers = [];
        this.currentLocation = null;
        this.routeControl = null;
        this.init();
    }

    init() {
        this.setupMapElements();
        this.setupLocationServices();
        this.setupEventListeners();
    }

    setupMapElements() {
        // Wait for Leaflet to be available
        if (typeof L === 'undefined') {
            setTimeout(() => this.setupMapElements(), 100);
            return;
        }

        // Initialize Leaflet map
        this.initializeMap();
    }

    initializeMap() {
        const mapContainer = document.getElementById('map-container');
        if (!mapContainer) {
            console.error('Map container not found');
            return;
        }

        // Default center (New York City)
        const defaultCenter = [40.7128, -74.0060];

        // Create Leaflet map instance
        this.map = L.map('map-container').setView(defaultCenter, 13);

        // Add OpenStreetMap tile layer (free!)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }).addTo(this.map);

        // Get user's current location
        this.getCurrentLocation();
    }

    setupLocationServices() {
        // Check if geolocation is supported
        if (navigator.geolocation) {
            this.getCurrentLocation();
        } else {
            console.warn('Geolocation is not supported by this browser');
        }
    }

    getCurrentLocation() {
        if (!navigator.geolocation) return;

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const pos = [position.coords.latitude, position.coords.longitude];

                this.currentLocation = pos;
                this.centerMapOnLocation(pos);
                this.addCurrentLocationMarker(pos);

                // Update pickup field with current location
                this.reverseGeocode(pos, 'pickup');
            },
            (error) => {
                console.error('Error getting location:', error);
                // Fallback to default location (New York City)
                this.centerMapOnLocation([40.7128, -74.0060]);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            }
        );
    }

    centerMapOnLocation(location) {
        if (this.map) {
            this.map.setView(location, 15);
        }
    }

    addCurrentLocationMarker(location) {
        if (!this.map) return;

        // Remove existing current location marker
        this.markers = this.markers.filter(marker => {
            if (marker.type === 'current') {
                this.map.removeLayer(marker);
                return false;
            }
            return true;
        });

        // Create custom icon for current location
        const currentLocationIcon = L.divIcon({
            html: `<div style="
                width: 20px;
                height: 20px;
                background-color: #667eea;
                border: 3px solid white;
                border-radius: 50%;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            "></div>`,
            className: 'current-location-marker',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });

        const marker = L.marker(location, { icon: currentLocationIcon })
            .addTo(this.map)
            .bindPopup('Your Location')
            .openPopup();

        marker.type = 'current';
        this.markers.push(marker);
    }

    addLocationMarker(location, type, title) {
        if (!this.map) return;

        // Remove existing markers of this type
        this.markers = this.markers.filter(marker => {
            if (marker.type === type) {
                this.map.removeLayer(marker);
                return false;
            }
            return true;
        });

        // Create custom icons for pickup and destination
        const pickupIcon = L.divIcon({
            html: `<div style="
                width: 30px;
                height: 30px;
                background-color: #28a745;
                border: 2px solid white;
                border-radius: 50% 50% 50% 0;
                transform: rotate(-45deg);
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            "><div style="
                width: 8px;
                height: 8px;
                background-color: white;
                border-radius: 50%;
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(45deg);
            "></div></div>`,
            className: 'pickup-marker',
            iconSize: [30, 30],
            iconAnchor: [15, 30]
        });

        const destinationIcon = L.divIcon({
            html: `<div style="
                width: 30px;
                height: 30px;
                background-color: #dc3545;
                border: 2px solid white;
                border-radius: 50% 50% 50% 0;
                transform: rotate(-45deg);
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            "><div style="
                width: 8px;
                height: 8px;
                background-color: white;
                border-radius: 50%;
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(45deg);
            "></div></div>`,
            className: 'destination-marker',
            iconSize: [30, 30],
            iconAnchor: [15, 30]
        });

        const icon = type === 'pickup' ? pickupIcon : destinationIcon;
        const marker = L.marker(location, { icon })
            .addTo(this.map)
            .bindPopup(title || (type === 'pickup' ? 'Pickup Location' : 'Destination'));

        marker.type = type;
        this.markers.push(marker);

        // Fit map to show all markers
        this.fitMapToMarkers();

        // If both pickup and destination are set, show route
        if (this.shouldShowRoute()) {
            this.showRoute();
        }
    }

    shouldShowRoute() {
        const pickupInput = document.getElementById('pickup');
        const destinationInput = document.getElementById('destination');

        return pickupInput && destinationInput && pickupInput.value && destinationInput.value;
    }

    async showRoute() {
        const pickupInput = document.getElementById('pickup');
        const destinationInput = document.getElementById('destination');

        if (!pickupInput || !destinationInput || !pickupInput.value || !destinationInput.value) return;

        try {
            const pickupLocation = await this.geocodeAddress(pickupInput.value);
            const destinationLocation = await this.geocodeAddress(destinationInput.value);

            if (pickupLocation && destinationLocation) {
                this.calculateRoute(pickupLocation, destinationLocation);
            }
        } catch (error) {
            console.error('Error showing route:', error);
        }
    }

    async geocodeAddress(address) {
        try {
            // Using Nominatim (free OpenStreetMap geocoding service)
            const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`);
            const data = await response.json();

            if (data.length > 0) {
                return [parseFloat(data[0].lat), parseFloat(data[0].lon)];
            }
            return null;
        } catch (error) {
            console.error('Geocoding error:', error);
            return null;
        }
    }

    async calculateRoute(origin, destination) {
        try {
            // Clear existing route
            if (this.routeControl) {
                this.map.removeControl(this.routeControl);
            }

            // Use Leaflet Routing Machine with free OSRM routing
            if (typeof L.Routing !== 'undefined') {
                this.routeControl = L.Routing.control({
                    waypoints: [
                        L.latLng(origin[0], origin[1]),
                        L.latLng(destination[0], destination[1])
                    ],
                    routeWhileDragging: false,
                    addWaypoints: false,
                    createMarker: function() { return null; }, // Don't create default markers
                    lineOptions: {
                        styles: [{ color: '#667eea', weight: 4, opacity: 0.8 }]
                    }
                }).addTo(this.map);

                this.routeControl.on('routesfound', (e) => {
                    const routes = e.routes;
                    const summary = routes[0].summary;
                    this.updateRouteInfo(summary);
                });
            } else {
                // Fallback: simple straight line
                const polyline = L.polyline([origin, destination], {
                    color: '#667eea',
                    weight: 4,
                    opacity: 0.8
                }).addTo(this.map);

                this.map.fitBounds(polyline.getBounds());

                // Calculate simple distance
                const distance = this.map.distance(origin, destination);
                this.updateRouteInfo({
                    totalDistance: distance,
                    totalTime: distance / 1000 * 60 // Rough estimate: 1km per minute
                });
            }
        } catch (error) {
            console.error('Route calculation error:', error);
        }
    }

    updateRouteInfo(summary) {
        // Create or update route info display
        let routeInfo = document.getElementById('route-info');
        if (!routeInfo) {
            routeInfo = document.createElement('div');
            routeInfo.id = 'route-info';
            routeInfo.className = 'route-info';
            routeInfo.style.cssText = `
                background: white;
                padding: 1rem;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-top: 1rem;
                text-align: center;
            `;

            const mapContainer = document.getElementById('map-container');
            if (mapContainer && mapContainer.parentNode) {
                mapContainer.parentNode.insertBefore(routeInfo, mapContainer.nextSibling);
            }
        }

        const distance = summary.totalDistance ? (summary.totalDistance / 1000).toFixed(1) : 'N/A';
        const duration = summary.totalTime ? Math.round(summary.totalTime / 60) : 'N/A';
        const fare = summary.totalDistance ? this.calculateEstimatedFare(summary.totalDistance) : '$0.00';

        routeInfo.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                <div>
                    <strong>Distance</strong><br>
                    ${distance} km
                </div>
                <div>
                    <strong>Duration</strong><br>
                    ${duration} min
                </div>
                <div>
                    <strong>Estimated Fare</strong><br>
                    ${fare}
                </div>
            </div>
        `;
    }

    calculateEstimatedFare(distanceMeters) {
        // Simple fare calculation (base fare + per km rate)
        const baseFare = 2.50;
        const perKmRate = 1.25;
        const distanceKm = distanceMeters / 1000;

        const estimatedFare = baseFare + (distanceKm * perKmRate);
        return `$${estimatedFare.toFixed(2)}`;
    }

    fitMapToMarkers() {
        if (!this.map || this.markers.length === 0) return;

        const group = new L.featureGroup(this.markers);
        this.map.fitBounds(group.getBounds().pad(0.1));
    }

    async reverseGeocode(location, fieldType) {
        try {
            const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${location[0]}&lon=${location[1]}`);
            const data = await response.json();

            if (data.display_name) {
                const input = document.getElementById(fieldType);
                if (input) {
                    input.value = data.display_name;
                }
                return data.display_name;
            }
        } catch (error) {
            console.error('Reverse geocoding error:', error);
        }
        return null;
    }

    setupEventListeners() {
        // Listen for form changes to update map
        const pickupInput = document.getElementById('pickup');
        const destinationInput = document.getElementById('destination');

        if (pickupInput) {
            pickupInput.addEventListener('change', async () => {
                if (pickupInput.value) {
                    const location = await this.geocodeAddress(pickupInput.value);
                    if (location) {
                        this.addLocationMarker(location, 'pickup', pickupInput.value);
                    }
                }
            });
        }

        if (destinationInput) {
            destinationInput.addEventListener('change', async () => {
                if (destinationInput.value) {
                    const location = await this.geocodeAddress(destinationInput.value);
                    if (location) {
                        this.addLocationMarker(location, 'destination', destinationInput.value);
                    }
                }
            });
        }
    }

    removeRouteInfo() {
        const routeInfo = document.getElementById('route-info');
        if (routeInfo) {
            routeInfo.remove();
        }
    }

    // Public methods for external use
    getMap() {
        return this.map;
    }

    getCurrentLocation() {
        return this.currentLocation;
    }

    clearMap() {
        // Clear all markers
        this.markers.forEach(marker => {
            if (this.map) {
                this.map.removeLayer(marker);
            }
        });
        this.markers = [];

        // Clear route
        if (this.routeControl && this.map) {
            this.map.removeControl(this.routeControl);
            this.routeControl = null;
        }

        // Remove route info
        this.removeRouteInfo();
    }

    // Method for driver location updates
    updateDriverLocation(driverId, location, rideId) {
        if (!this.map) return;

        // Remove existing driver marker
        this.markers = this.markers.filter(marker => {
            if (marker.type === 'driver' && marker.driverId === driverId) {
                this.map.removeLayer(marker);
                return false;
            }
            return true;
        });

        // Add new driver marker
        const driverIcon = L.divIcon({
            html: `<div style="
                width: 25px;
                height: 25px;
                background-color: #ffc107;
                border: 2px solid white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            ">🚗</div>`,
            className: 'driver-marker',
            iconSize: [25, 25],
            iconAnchor: [12, 12]
        });

        const marker = L.marker([location.lat, location.lng], { icon: driverIcon })
            .addTo(this.map)
            .bindPopup(`Driver: ${driverId}`);

        marker.type = 'driver';
        marker.driverId = driverId;
        marker.rideId = rideId;
        this.markers.push(marker);
    }

    // Method to update map when ride type changes
    updateMapForRideType(rideType) {
        console.log('Map updated for ride type:', rideType);
    }
}

// Initialize map manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait for Leaflet to load
    if (typeof L !== 'undefined') {
        window.mapManager = new MapManager();
    } else {
        // Retry after a short delay
        setTimeout(() => {
            if (typeof L !== 'undefined') {
                window.mapManager = new MapManager();
            }
        }, 1000);
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MapManager;
}