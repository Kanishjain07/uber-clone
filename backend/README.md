# Uber Clone Backend

A full-stack Uber clone backend built with Flask, featuring real-time communication, user authentication, ride management, and more.

## Features

- **User Authentication**: JWT-based authentication for riders and drivers
- **Real-time Communication**: WebSocket support for live updates
- **Ride Management**: Complete ride lifecycle from request to completion
- **Driver Matching**: Intelligent driver-rider matching algorithm
- **Fare Calculation**: Dynamic pricing with surge and discount support
- **Location Services**: Real-time location tracking and updates
- **Payment Integration**: Ready for payment gateway integration
- **Notifications**: In-app notification system

## Tech Stack

- **Framework**: Flask
- **Database**: MongoDB with PyMongo
- **Real-time**: Flask-SocketIO with Eventlet
- **Authentication**: Flask-JWT-Extended
- **CORS**: Flask-CORS
- **Validation**: Custom validation utilities
- **Async**: Eventlet/Gevent for WebSocket support

## Prerequisites

- Python 3.8+
- MongoDB 4.4+
- pip (Python package manager)

## Installation

1. **Clone the repository**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
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

5. **Start MongoDB**
   Make sure MongoDB is running on your system.

6. **Run the application**
   ```bash
   python app.py
   ```

The backend will start on `http://localhost:5000`

## API Endpoints

### Authentication (`/api/auth`)
- `POST /register` - User registration (rider/driver)
- `POST /login` - User login
- `POST /refresh` - Refresh access token
- `GET /profile` - Get user profile
- `PUT /profile` - Update user profile
- `POST /change-password` - Change password
- `POST /logout` - Logout user

### Rides (`/api/rides`)
- `POST /request` - Request a new ride
- `POST /<ride_id>/accept` - Driver accepts ride
- `POST /<ride_id>/start` - Driver starts ride
- `POST /<ride_id>/complete` - Driver completes ride
- `POST /<ride_id>/cancel` - Cancel ride
- `GET /<ride_id>` - Get ride details
- `GET /history` - Get ride history

### Riders (`/api/riders`)
- `GET /profile` - Get rider profile
- `PUT /location` - Update rider location
- `GET /rides/active` - Get active ride
- `GET /rides/available-drivers` - Find nearby drivers
- `PUT /profile` - Update rider profile

### Drivers (`/api/drivers`)
- `GET /profile` - Get driver profile
- `PUT /status` - Update online/offline status
- `PUT /location` - Update driver location
- `GET /available-rides` - Get available ride requests
- `GET /earnings` - Get earnings and statistics
- `PUT /profile` - Update driver profile

## WebSocket Events

### Driver Events
- `driver_connect` - Driver connects to system
- `driver_disconnect` - Driver disconnects
- `update_location` - Update driver location
- `ride_request` - New ride request
- `accept_ride` - Accept ride request
- `start_ride` - Start ride
- `complete_ride` - Complete ride

### Rider Events
- `rider_connect` - Rider connects to system
- `rider_disconnect` - Rider disconnects
- `request_ride` - Request new ride
- `cancel_ride` - Cancel ride
- `update_location` - Update rider location
- `rate_driver` - Rate driver after ride
- `join_ride_room` - Join ride-specific room

## Database Collections

- **users**: User accounts and basic information
- **riders**: Rider-specific profiles and preferences
- **drivers**: Driver profiles, vehicle info, and status
- **rides**: Complete ride information and status
- **payments**: Payment records and transactions
- **notifications**: User notifications and alerts
- **driver_locations**: Real-time driver location tracking

## Configuration

The application uses environment variables for configuration. Key settings include:

- **SECRET_KEY**: Flask secret key for sessions
- **JWT_SECRET_KEY**: Secret key for JWT tokens
- **MONGO_URI**: MongoDB connection string
- **GOOGLE_MAPS_API_KEY**: Google Maps API key for location services
- **FLASK_ENV**: Environment (development/production/testing)

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Style
The project follows PEP 8 style guidelines.

### Logging
Logs are written to `logs/app.log` by default. Set `LOG_LEVEL` environment variable to control verbosity.

## Production Deployment

1. Set `FLASK_ENV=production`
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Set secure `SECRET_KEY` and `JWT_SECRET_KEY`
4. Configure MongoDB with authentication
5. Set up proper CORS origins
6. Use HTTPS in production
7. Set up monitoring and logging

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running
   - Check `MONGO_URI` in `.env` file

2. **JWT Token Errors**
   - Verify `JWT_SECRET_KEY` is set
   - Check token expiration settings

3. **WebSocket Connection Issues**
   - Ensure Eventlet is installed
   - Check CORS configuration

4. **Google Maps API Errors**
   - Verify API key is valid
   - Check API key restrictions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational purposes only.

## Support

For issues and questions, please check the troubleshooting section or create an issue in the repository.
