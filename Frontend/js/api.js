// API Helper JavaScript
class APIHelper {
    constructor() {
        this.baseURL = 'http://localhost:8080'; // Default backend URL
        this.timeout = 10000; // 10 seconds timeout
        this.init();
    }

    init() {
        // Use MongoDB-enabled backend for development
        this.baseURL = 'http://localhost:5000';
        console.log('API BaseURL set to:', this.baseURL);
    }

    // Get authentication token from localStorage
    getAuthToken() {
        return localStorage.getItem('authToken');
    }

    // Get default headers for API requests
    getDefaultHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };

        const token = this.getAuthToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    }

    // Generic HTTP request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            method: options.method || 'GET',
            headers: {
                ...this.getDefaultHeaders(),
                ...options.headers
            },
            timeout: this.timeout,
            ...options
        };

        // Add body for POST, PUT, PATCH requests
        if (['POST', 'PUT', 'PATCH'].includes(config.method) && options.body) {
            config.body = JSON.stringify(options.body);
        }

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);

            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            // Handle different response statuses
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return { success: true, data };

        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            
            if (error.message.includes('401')) {
                // Unauthorized - redirect to login
                this.handleUnauthorized();
            }
            
            throw error;
        }
    }

    // GET request
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        
        return this.request(url, { method: 'GET' });
    }

    // POST request
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: data
        });
    }

    // PUT request
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: data
        });
    }

    // PATCH request
    async patch(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: data
        });
    }

    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // Handle unauthorized responses
    handleUnauthorized() {
        // Clear stored auth data
        localStorage.removeItem('authToken');
        localStorage.removeItem('userData');
        
        // Redirect to login or show login modal
        if (window.authManager) {
            window.authManager.showModal('loginModal');
        }
        
        // Show notification
        if (window.app) {
            window.app.showNotification('Session expired. Please login again.', 'warning');
        }
    }

    // Upload file with progress tracking
    async uploadFile(endpoint, file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();
        
        return new Promise((resolve, reject) => {
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable && onProgress) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    onProgress(percentComplete);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve({ success: true, data: response });
                    } catch (error) {
                        resolve({ success: true, data: xhr.responseText });
                    }
                } else {
                    reject(new Error(`Upload failed with status: ${xhr.status}`));
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });

            xhr.open('POST', `${this.baseURL}${endpoint}`);
            
            // Add auth header if available
            const token = this.getAuthToken();
            if (token) {
                xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            }

            xhr.send(formData);
        });
    }

    // Retry failed requests
    async retryRequest(requestFn, maxRetries = 3, delay = 1000) {
        let lastError;
        
        for (let i = 0; i < maxRetries; i++) {
            try {
                return await requestFn();
            } catch (error) {
                lastError = error;
                
                if (i < maxRetries - 1) {
                    await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
                }
            }
        }
        
        throw lastError;
    }

    // Batch multiple requests
    async batchRequests(requests) {
        const promises = requests.map(request => request());
        return Promise.allSettled(promises);
    }

    // Mock API responses for development/testing
    getMockResponse(endpoint, method = 'GET') {
        const mockData = {
            '/auth/login': {
                POST: {
                    success: true,
                    data: {
                        user: {
                            id: '1',
                            name: 'Demo User',
                            email: 'demo@example.com',
                            userType: 'rider'
                        },
                        token: 'mock-jwt-token-' + Date.now()
                    }
                }
            },
            '/auth/register': {
                POST: {
                    success: true,
                    data: {
                        user: {
                            id: Date.now().toString(),
                            name: 'New User',
                            email: 'newuser@example.com',
                            userType: 'rider'
                        },
                        token: 'mock-jwt-token-' + Date.now()
                    }
                }
            },
            '/rides/nearby': {
                GET: {
                    success: true,
                    data: {
                        drivers: [
                            {
                                id: '1',
                                name: 'John Driver',
                                rating: 4.8,
                                vehicle: 'Toyota Camry',
                                distance: '0.5 miles',
                                eta: '3 min'
                            },
                            {
                                id: '2',
                                name: 'Sarah Driver',
                                rating: 4.9,
                                vehicle: 'Honda Civic',
                                distance: '0.8 miles',
                                eta: '5 min'
                            }
                        ]
                    }
                }
            },
            '/rides/estimate': {
                POST: {
                    success: true,
                    data: {
                        estimate: {
                            distance: '2.3 miles',
                            duration: '8 min',
                            price: 12.50,
                            currency: 'USD'
                        }
                    }
                }
            }
        };

        return mockData[endpoint]?.[method] || { success: false, message: 'Endpoint not found' };
    }

    // Use mock data in development
    async mockRequest(endpoint, options = {}) {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000));
        
        const mockResponse = this.getMockResponse(endpoint, options.method);
        
        if (mockResponse.success) {
            return mockResponse;
        } else {
            throw new Error(mockResponse.message || 'Mock request failed');
        }
    }

    // Check if we should use mock data
    shouldUseMock() {
        return window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' ||
               window.location.search.includes('mock=true');
    }

    // Wrapper method that decides between real API and mock
    async smartRequest(endpoint, options = {}) {
        if (this.shouldUseMock()) {
            return this.mockRequest(endpoint, options);
        } else {
            return this.request(endpoint, options);
        }
    }

    // Health check endpoint
    async healthCheck() {
        try {
            const response = await this.get('/health');
            return response.success;
        } catch (error) {
            return false;
        }
    }

    // Get API status
    async getAPIStatus() {
        try {
            const response = await this.get('/status');
            return response.data;
        } catch (error) {
            return {
                status: 'offline',
                message: 'API is not responding',
                timestamp: new Date().toISOString()
            };
        }
    }

    // Rate limiting helper
    createRateLimiter(maxRequests = 10, timeWindow = 60000) {
        const requests = [];
        
        return () => {
            const now = Date.now();
            requests.push(now);
            
            // Remove old requests outside the time window
            while (requests.length > 0 && requests[0] < now - timeWindow) {
                requests.shift();
            }
            
            return requests.length <= maxRequests;
        };
    }

    // Cache responses
    createCache(ttl = 300000) { // 5 minutes default
        const cache = new Map();
        
        return {
            get: (key) => {
                const item = cache.get(key);
                if (item && Date.now() - item.timestamp < ttl) {
                    return item.data;
                }
                cache.delete(key);
                return null;
            },
            set: (key, data) => {
                cache.set(key, {
                    data,
                    timestamp: Date.now()
                });
            },
            clear: () => cache.clear()
        };
    }
}

// Initialize API helper when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.api = new APIHelper();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIHelper;
}
