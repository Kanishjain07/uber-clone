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
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  TrendingUp,
  Schedule,
  LocationOn,
  DirectionsCar,
  CheckCircle,
  PlayArrow,
  Stop,
  AttachMoney,
  Navigation,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

function DriverDashboard() {
  const { user } = useAuth();
  const [isOnline, setIsOnline] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [driverStatus, setDriverStatus] = useState(null);
  const [availableRides, setAvailableRides] = useState([]);
  const [selectedRide, setSelectedRide] = useState(null);
  const [activeRide, setActiveRide] = useState(null);

  useEffect(() => {
    if (user?.user_type === 'driver') {
      fetchDriverStatus();
    }
  }, [user]);

  useEffect(() => {
    let interval;
    if (isOnline && !activeRide) {
      interval = setInterval(fetchAvailableRides, 5000); // Check every 5 seconds
    }
    return () => clearInterval(interval);
  }, [isOnline, activeRide]);

  const fetchDriverStatus = async () => {
    try {
      const response = await axios.get('/api/v1/drivers/status');
      setDriverStatus(response.data);
      setIsOnline(response.data.is_online);
    } catch (err) {
      console.error('Failed to fetch driver status:', err);
    }
  };

  const fetchAvailableRides = async () => {
    if (!isOnline) return;

    try {
      const response = await axios.get('/api/v1/drivers/available-rides');
      setAvailableRides(response.data.available_rides || []);
    } catch (err) {
      console.error('Failed to fetch available rides:', err);
    }
  };

  const handleToggleOnline = async () => {
    setLoading(true);
    setError('');

    try {
      if (isOnline) {
        await axios.post('/api/v1/drivers/offline');
        setIsOnline(false);
        setAvailableRides([]);
        setSuccess('You are now offline');
      } else {
        // Mock location for going online
        await axios.post('/api/v1/drivers/online', {
          latitude: 28.6200,
          longitude: 77.2100,
        });
        setIsOnline(true);
        setSuccess('You are now online and ready to accept rides!');
        fetchAvailableRides();
      }
      fetchDriverStatus();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update status');
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptRide = async (rideId) => {
    setLoading(true);
    setError('');

    try {
      await axios.post(`/api/v1/rides/${rideId}/accept`);
      setActiveRide(availableRides.find(ride => ride.ride_id === rideId));
      setAvailableRides(prev => prev.filter(ride => ride.ride_id !== rideId));
      setSelectedRide(null);
      setSuccess('Ride accepted! Navigate to pickup location.');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to accept ride');
    } finally {
      setLoading(false);
    }
  };

  const handleStartRide = async () => {
    if (!activeRide) return;

    setLoading(true);
    setError('');

    try {
      await axios.post(`/api/v1/rides/${activeRide.ride_id}/start`);
      setActiveRide(prev => ({ ...prev, status: 'in_progress' }));
      setSuccess('Ride started! Drive safely to destination.');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start ride');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteRide = async () => {
    if (!activeRide) return;

    setLoading(true);
    setError('');

    try {
      await axios.post(`/api/v1/rides/${activeRide.ride_id}/complete`, {
        final_fare: activeRide.estimated_fare,
      });
      setActiveRide(null);
      setSuccess('Ride completed successfully! Payment processed.');
      fetchDriverStatus();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to complete ride');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Driver Dashboard
      </Typography>
      <Typography variant="subtitle1" color="textSecondary" gutterBottom>
        Welcome, {user?.first_name}! Manage your driving activity here.
      </Typography>

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Active Ride Status */}
        {activeRide && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3, mb: 3, bgcolor: 'success.light', color: 'success.contrastText' }}>
              <Typography variant="h6" gutterBottom>
                Active Ride - {activeRide.rider_name}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap', mb: 2 }}>
                <Chip
                  icon={<Navigation />}
                  label={`From: ${activeRide.pickup_address}`}
                  size="small"
                />
                <Chip
                  icon={<LocationOn />}
                  label={`To: ${activeRide.destination_address}`}
                  size="small"
                />
                <Chip
                  icon={<AttachMoney />}
                  label={`$${activeRide.estimated_fare}`}
                  size="small"
                />
              </Box>
              <Box sx={{ display: 'flex', gap: 2 }}>
                {!activeRide.status || activeRide.status === 'accepted' ? (
                  <Button
                    variant="contained"
                    startIcon={<PlayArrow />}
                    onClick={handleStartRide}
                    disabled={loading}
                  >
                    Start Ride
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    startIcon={<CheckCircle />}
                    onClick={handleCompleteRide}
                    disabled={loading}
                  >
                    Complete Ride
                  </Button>
                )}
              </Box>
            </Paper>
          </Grid>
        )}

        {/* Online Status */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Driver Status
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={isOnline}
                  onChange={handleToggleOnline}
                  disabled={loading}
                />
              }
              label={isOnline ? 'Online - Ready for rides' : 'Offline'}
            />
            <Box sx={{ mt: 2 }}>
              <Button
                variant={isOnline ? 'outlined' : 'contained'}
                fullWidth
                startIcon={loading ? <CircularProgress size={20} /> : <DirectionsCar />}
                onClick={handleToggleOnline}
                disabled={loading}
              >
                {loading ? 'Updating...' : (isOnline ? 'Go Offline' : 'Go Online')}
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Today's Summary
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography variant="body2">
                Rides Completed: <strong>{driverStatus?.today_rides || 0}</strong>
              </Typography>
              <Typography variant="body2">
                Earnings: <strong>${driverStatus?.today_earnings || '0.00'}</strong>
              </Typography>
              <Typography variant="body2">
                Rating: <strong>{driverStatus?.rating || '5.0'} ⭐</strong>
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Available Rides */}
        {isOnline && !activeRide && (
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Available Rides ({availableRides.length})
              </Typography>
              {availableRides.length === 0 ? (
                <Typography variant="body2" color="textSecondary">
                  No rides available nearby. Stay online to receive ride requests!
                </Typography>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {availableRides.slice(0, 3).map((ride) => (
                    <Card key={ride.ride_id} variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Box>
                            <Typography variant="subtitle1">
                              {ride.rider_name}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              {ride.pickup_address} → {ride.destination_address}
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                              <Chip label={`${ride.distance_to_pickup_km} km away`} size="small" />
                              <Chip label={`$${ride.estimated_fare}`} size="small" color="primary" />
                              <Chip label={`${ride.eta_to_pickup_minutes} min`} size="small" />
                            </Box>
                          </Box>
                          <Button
                            variant="contained"
                            onClick={() => handleAcceptRide(ride.ride_id)}
                            disabled={loading}
                          >
                            Accept
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
            </Paper>
          </Grid>
        )}

        {/* Quick Actions */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<TrendingUp />}
                fullWidth
              >
                View Earnings
              </Button>
              <Button
                variant="outlined"
                startIcon={<Schedule />}
                fullWidth
              >
                Set Schedule
              </Button>
              <Button
                variant="outlined"
                startIcon={<LocationOn />}
                fullWidth
              >
                Update Location
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Recent Trips */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Performance Summary
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {driverStatus?.total_rides || 0}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Total Rides
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    ${driverStatus?.total_earnings || '0.00'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Total Earnings
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {driverStatus?.rating || '5.0'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Rating
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {isOnline ? 'ONLINE' : 'OFFLINE'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Status
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default DriverDashboard;