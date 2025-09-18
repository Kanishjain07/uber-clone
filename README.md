# 🚗 Uber Clone - Full Stack Application

A complete Uber clone application built with modern web technologies, featuring real-time ride booking, driver matching, and location services.

## ✨ Features

### 🚶‍♂️ For Riders
- **User Registration & Authentication**: Secure JWT-based login system
- **Ride Booking**: Request rides with pickup and destination locations
- **Real-time Tracking**: Live driver location and ETA updates
- **Fare Estimation**: Transparent pricing with distance calculation
- **Ride History**: Complete ride history and receipts
- **Driver Rating**: Rate drivers after completed rides
- **Multiple Ride Types**: Standard, premium, and shared ride options

### 🚗 For Drivers
- **Driver Registration**: Complete profile setup with vehicle information
- **Ride Requests**: Receive and accept nearby ride requests
- **Navigation**: Built-in navigation and route optimization
- **Earnings Tracking**: Monitor daily and weekly earnings
- **Status Management**: Go online/offline and manage availability
- **Real-time Updates**: Live ride status and passenger information

### 🔧 Technical Features
- **Real-time Communication**: WebSocket support for live updates
- **Location Services**: Google Maps integration for mapping and navigation
- **Responsive Design**: Mobile-first design that works on all devices
- **Secure Authentication**: JWT tokens with refresh mechanism
- **Database**: MongoDB with optimized queries and indexing
- **API-First**: RESTful API architecture with comprehensive endpoints

## 🏗️ Architecture

```
uber-clone/
├── frontend/                 # Vanilla JavaScript Frontend
│   ├── index.html           # Main application page
│   ├── css/                 # Stylesheets
│   ├── js/                  # JavaScript modules
│   └── package.json         # Frontend dependencies
├── backend/                  # Flask Backend
│   ├── app.py              # Main Flask application
│   ├── api/                # API route handlers
│   ├── models/             # Database models and utilities
│   ├── services/           # Business logic services
│   ├── sockets/            # WebSocket event handlers
│   ├── utils/              # Utility functions
│   └── requirements.txt    # Python dependencies
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites
- **Node.js** (v14+) for frontend development server
- **Python** (3.8+) for backend
- **MongoDB** (4.4+) for database
- **Google Maps API Key** (for location services)

### 1. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

The frontend will be available at `http://localhost:8080`

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your configuration
# (See backend/README.md for details)

# Start backend server
python app.py
# OR use the runner script:
python run.py
```

The backend will be available at `http://localhost:5000`

### 3. Database Setup

Ensure MongoDB is running on your system. The application will automatically create the required collections and indexes on first run.

## 🔑 Configuration

### Frontend Configuration
The frontend is pre-configured with your Google Maps API key. No additional configuration is required for basic functionality.

### Backend Configuration
Create a `.env` file in the backend directory:

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
FLASK_ENV=development

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/uber_clone

# Google Maps API
GOOGLE_MAPS_API_KEY=AIzaSyDqs1yX9nhlPP28-l062NeVEGV_9Ub9gYg

# Optional: Payment Configuration
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
```

## 📱 Frontend Features

### Core Components
- **Authentication System**: Login/register modals with form validation
- **Map Integration**: Google Maps with location services and autocomplete
- **Ride Booking**: Intuitive ride request form with fare estimation
- **Real-time Updates**: Live ride status and driver tracking
- **Responsive Design**: Mobile-optimized interface

### JavaScript Modules
- **`app.js`**: Main application logic and UI management
- **`auth.js`**: Authentication handling and user management
- **`api.js`**: HTTP client for backend communication
- **`map.js`**: Google Maps integration and location services
- **`ride.js`**: Ride management and status updates
- **`driver.js`**: Driver-specific functionality
- **`socket.js`**: WebSocket client for real-time communication

## 🔌 Backend Features

### API Endpoints
- **Authentication**: User registration, login, profile management
- **Rides**: Complete ride lifecycle management
- **Riders**: Rider-specific operations and preferences
- **Drivers**: Driver management and status updates
- **Real-time**: WebSocket events for live updates

### Services
- **Matching**: Intelligent driver-rider matching algorithm
- **Pricing**: Dynamic fare calculation with surge pricing
- **Notifications**: In-app notification system
- **Validation**: Input validation and sanitization utilities

### Database Collections
- **users**: User accounts and basic information
- **riders**: Rider profiles and preferences
- **drivers**: Driver profiles and vehicle information
- **rides**: Complete ride records and status
- **payments**: Payment transactions and history
- **notifications**: User notifications and alerts
- **driver_locations**: Real-time location tracking

## 🌐 API Documentation

### Authentication Endpoints
```
POST /api/auth/register     # User registration
POST /api/auth/login        # User login
POST /api/auth/refresh      # Refresh token
GET  /api/auth/profile      # Get user profile
PUT  /api/auth/profile      # Update profile
```

### Ride Endpoints
```
POST /api/rides/request           # Request new ride
POST /api/rides/{id}/accept       # Driver accepts ride
POST /api/rides/{id}/start        # Start ride
POST /api/rides/{id}/complete     # Complete ride
POST /api/rides/{id}/cancel       # Cancel ride
GET  /api/rides/{id}              # Get ride details
GET  /api/rides/history           # Get ride history
```

### WebSocket Events
- **Driver Events**: `driver_connect`, `update_location`, `ride_request`
- **Rider Events**: `rider_connect`, `request_ride`, `update_location`

## 🧪 Testing

### Frontend Testing
```bash
cd frontend
# Open in browser and test functionality manually
# Or use browser developer tools for debugging
```

### Backend Testing
```bash
cd backend
# Run with pytest (if tests are implemented)
python -m pytest tests/
```

## 🚀 Deployment

### Frontend Deployment
- Build and deploy to any static hosting service
- Configure CORS settings for production backend
- Update API endpoints for production URLs

### Backend Deployment
- Use production WSGI server (Gunicorn, uWSGI)
- Set production environment variables
- Configure MongoDB with authentication
- Set up proper CORS origins
- Use HTTPS in production

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Bcrypt for secure password storage
- **Input Validation**: Comprehensive input sanitization
- **CORS Protection**: Configurable cross-origin resource sharing
- **Rate Limiting**: Protection against abuse
- **Secure Headers**: Security-focused HTTP headers

## 🛠️ Development

### Code Style
- **Frontend**: Modern JavaScript with ES6+ features
- **Backend**: PEP 8 compliant Python code
- **Database**: MongoDB best practices with proper indexing

### Project Structure
- **Modular Architecture**: Clear separation of concerns
- **Service Layer**: Business logic separated from API handlers
- **Utility Functions**: Reusable helper functions
- **Configuration Management**: Environment-based configuration

## 📚 Learning Resources

This project demonstrates:
- **Full-stack Development**: Frontend and backend integration
- **Real-time Applications**: WebSocket implementation
- **API Design**: RESTful API architecture
- **Database Design**: MongoDB schema design and optimization
- **Authentication Systems**: JWT-based security
- **Location Services**: Google Maps API integration
- **Modern JavaScript**: ES6+ features and modular code
- **Flask Framework**: Python web development

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for educational purposes only. Please respect the terms of service for any third-party APIs used.

## 🆘 Support

- **Frontend Issues**: Check browser console for errors
- **Backend Issues**: Check server logs and MongoDB connection
- **API Issues**: Verify endpoint URLs and authentication
- **Database Issues**: Ensure MongoDB is running and accessible

## 🎯 Next Steps

- **Payment Integration**: Add Stripe or other payment gateways
- **Push Notifications**: Implement mobile push notifications
- **Analytics**: Add user behavior and ride analytics
- **Admin Panel**: Create admin dashboard for monitoring
- **Mobile App**: Develop native mobile applications
- **Testing**: Add comprehensive test coverage
- **CI/CD**: Set up automated testing and deployment

---

**Happy Coding! 🚗💻**
