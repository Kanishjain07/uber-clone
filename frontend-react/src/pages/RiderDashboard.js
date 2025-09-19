import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  LocationOn,
  History,
  Payment,
  DirectionsCar,
  LocalTaxi,
  Navigation,
  Timer,
  AttachMoney,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

function RiderDashboard() {
  const { user } = useAuth();
  const [openBooking, setOpenBooking] = useState(false);
  const [rideData, setRideData] = useState({
    pickup_address: '',
    pickup_latitude: '',
    pickup_longitude: '',
    destination_address: '',
    destination_latitude: '',
    destination_longitude: '',
    vehicle_type: 'standard',
    passenger_count: 1,
  });
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [currentRide, setCurrentRide] = useState(null);

  // Mock location data for demo purposes
  const mockLocations = [
    { name: 'Connaught Place', lat: 28.6139, lng: 77.2090 },
    { name: 'India Gate', lat: 28.5244, lng: 77.1855 },
    { name: 'Red Fort', lat: 28.6562, lng: 77.2410 },
    { name: 'Lotus Temple', lat: 28.5535, lng: 77.2588 },
    { name: 'Qutub Minar', lat: 28.5244, lng: 77.1855 },
  ];

  const handleLocationSelect = (field, location) => {
    setRideData(prev => ({
      ...prev,
      [`${field}_address`]: location.name,
      [`${field}_latitude`]: location.lat,
      [`${field}_longitude`]: location.lng,
    }));
  };

  const handleEstimate = async () => {
    if (!rideData.pickup_latitude || !rideData.destination_latitude) {
      setError('Please select both pickup and destination locations');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/v1/rides/estimate', {
        pickup_latitude: parseFloat(rideData.pickup_latitude),
        pickup_longitude: parseFloat(rideData.pickup_longitude),
        pickup_address: rideData.pickup_address,
        destination_latitude: parseFloat(rideData.destination_latitude),
        destination_longitude: parseFloat(rideData.destination_longitude),
        destination_address: rideData.destination_address,
        vehicle_type: rideData.vehicle_type,
      });

      setEstimate(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to get ride estimate');
    } finally {
      setLoading(false);
    }
  };

  const handleRequestRide = async () => {
    if (!estimate) {
      setError('Please get an estimate first');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/v1/rides/request', {
        pickup_latitude: parseFloat(rideData.pickup_latitude),
        pickup_longitude: parseFloat(rideData.pickup_longitude),
        pickup_address: rideData.pickup_address,
        destination_latitude: parseFloat(rideData.destination_latitude),
        destination_longitude: parseFloat(rideData.destination_longitude),
        destination_address: rideData.destination_address,
        vehicle_type: rideData.vehicle_type,
        passenger_count: rideData.passenger_count,
      });

      setCurrentRide(response.data.ride);
      setSuccess('Ride requested successfully! Looking for nearby drivers...');
      setOpenBooking(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to request ride');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Welcome back, {user?.first_name}!
      </Typography>
      <Typography variant="subtitle1" color="textSecondary" gutterBottom>
        Ready for your next ride?
      </Typography>

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Current Ride Status */}
        {currentRide && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3, mb: 3, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
              <Typography variant="h6" gutterBottom>
                Current Ride Status: {currentRide.status}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                <Chip
                  icon={<Navigation />}
                  label={`From: ${currentRide.pickup_location.address}`}
                  size="small"
                />
                <Chip
                  icon={<LocationOn />}
                  label={`To: ${currentRide.destination_location.address}`}
                  size="small"
                />
                <Chip
                  icon={<AttachMoney />}
                  label={`$${currentRide.estimated_fare}`}
                  size="small"
                />
              </Box>
            </Paper>
          </Grid>
        )}

        {/* Main Ride Request */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Book a Ride
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button
                variant="contained"
                size="large"
                startIcon={<DirectionsCar />}
                onClick={() => setOpenBooking(true)}
                sx={{ py: 2 }}
                disabled={!!currentRide}
              >
                {currentRide ? 'Ride in Progress' : 'Request a Ride Now'}
              </Button>
              <Typography variant="body2" color="textSecondary" textAlign="center">
                Quick and reliable rides in your city
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<LocationOn />}
                fullWidth
              >
                Saved Places
              </Button>
              <Button
                variant="outlined"
                startIcon={<History />}
                fullWidth
              >
                Ride History
              </Button>
              <Button
                variant="outlined"
                startIcon={<Payment />}
                fullWidth
              >
                Payment Methods
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {currentRide
                ? `Current ride: ${currentRide.pickup_location.address} → ${currentRide.destination_location.address}`
                : 'No recent rides found. Book your first ride to get started!'
              }
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Ride Booking Dialog */}
      <Dialog open={openBooking} onClose={() => setOpenBooking(false)} maxWidth="md" fullWidth>
        <DialogTitle>Book Your Ride</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
            {/* Pickup Location */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Pickup Location
              </Typography>
              <TextField
                fullWidth
                value={rideData.pickup_address}
                placeholder="Select pickup location"
                InputProps={{ readOnly: true }}
                sx={{ mb: 1 }}
              />
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {mockLocations.map((location, index) => (
                  <Chip
                    key={index}
                    label={location.name}
                    onClick={() => handleLocationSelect('pickup', location)}
                    variant={rideData.pickup_address === location.name ? 'filled' : 'outlined'}
                    color={rideData.pickup_address === location.name ? 'primary' : 'default'}
                    size="small"
                  />
                ))}
              </Box>
            </Box>

            {/* Destination Location */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Destination
              </Typography>
              <TextField
                fullWidth
                value={rideData.destination_address}
                placeholder="Select destination"
                InputProps={{ readOnly: true }}
                sx={{ mb: 1 }}
              />
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {mockLocations.map((location, index) => (
                  <Chip
                    key={index}
                    label={location.name}
                    onClick={() => handleLocationSelect('destination', location)}
                    variant={rideData.destination_address === location.name ? 'filled' : 'outlined'}
                    color={rideData.destination_address === location.name ? 'primary' : 'default'}
                    size="small"
                  />
                ))}
              </Box>
            </Box>

            {/* Get Estimate Button */}
            <Button
              variant="outlined"
              onClick={handleEstimate}
              disabled={loading || !rideData.pickup_address || !rideData.destination_address}
              startIcon={loading ? <CircularProgress size={20} /> : <Timer />}
            >
              Get Estimate
            </Button>

            {/* Ride Estimate */}
            {estimate && (
              <Card sx={{ bgcolor: 'background.default' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Ride Estimate
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <Box textAlign="center">
                        <Typography variant="h5" color="primary">
                          ${estimate.estimated_fare}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Estimated Fare
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={4}>
                      <Box textAlign="center">
                        <Typography variant="h5" color="primary">
                          {estimate.distance_km} km
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Distance
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={4}>
                      <Box textAlign="center">
                        <Typography variant="h5" color="primary">
                          {estimate.estimated_duration_minutes} min
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Duration
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenBooking(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleRequestRide}
            disabled={loading || !estimate}
            startIcon={loading ? <CircularProgress size={20} /> : <LocalTaxi />}
          >
            Request Ride
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default RiderDashboard;