# Uber Clone Frontend

A modern, responsive frontend for a ride-sharing application built with vanilla JavaScript, HTML, and CSS.

## Features

- 🚗 **Ride Booking**: Request rides with pickup and destination
- 🗺️ **Interactive Maps**: Google Maps integration with location services
- 👤 **User Authentication**: Login/Register system
- 🚘 **Driver Dashboard**: Driver management and ride acceptance
- 📱 **Responsive Design**: Mobile-first approach
- ⚡ **Real-time Updates**: WebSocket integration for live updates

## Setup

### Option 1: Using npm (Recommended for development)

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start development server:
   ```bash
   npm start
   ```

3. Open your browser to `http://localhost:3000`

### Option 2: Direct file opening

Simply open `index.html` in your web browser. Note that some features (like Google Maps) may require a local server.

## Project Structure

```
frontend/
├── index.html          # Main HTML file
├── css/
│   └── style.css      # Main stylesheet
├── js/
│   ├── app.js         # Main application logic
│   ├── auth.js        # Authentication system
│   ├── api.js         # API helper functions
│   ├── map.js         # Google Maps integration
│   ├── ride.js        # Ride management
│   ├── driver.js      # Driver dashboard
│   └── socket.js      # WebSocket integration
└── assets/            # Images and icons
```

## Configuration

### Google Maps API

To use the map functionality, you'll need a Google Maps API key:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Maps JavaScript API and Places API
4. Create credentials (API key)
5. Add your API key to the map.js file or set it in localStorage

### Backend Connection

Update the API base URL in `js/api.js` to point to your backend server.

## Development

- **HTML**: Semantic markup with accessibility features
- **CSS**: Modern CSS with Flexbox/Grid, custom properties, and responsive design
- **JavaScript**: ES6+ classes, async/await, and modular architecture

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## License

MIT License - see LICENSE file for details
