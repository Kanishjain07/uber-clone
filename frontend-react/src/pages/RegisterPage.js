import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  Link,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
} from '@mui/material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function RegisterPage() {
  const navigate = useNavigate();
  const { register, error } = useAuth();
  const [searchParams] = useSearchParams();
  const defaultUserType = searchParams.get('type') || 'rider';

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone: '',
    user_type: defaultUserType,
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    // Add vehicle info for drivers
    const submitData = { ...formData };
    if (formData.user_type === 'driver') {
      submitData.vehicle_info = {
        make: 'Toyota',
        model: 'Camry',
        year: '2020',
        license_plate: 'ABC123',
        vehicle_type: 'standard',
      };
    }

    const result = await register(submitData);

    if (result.success) {
      navigate('/dashboard');
    }

    setLoading(false);
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" textAlign="center" gutterBottom>
          Sign Up
        </Typography>
        <Typography variant="body1" textAlign="center" color="textSecondary" sx={{ mb: 3 }}>
          Create your account to get started.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
          <TextField
            margin="normal"
            required
            fullWidth
            id="first_name"
            label="First Name"
            name="first_name"
            value={formData.first_name}
            onChange={handleChange}
          />
          <TextField
            margin="normal"
            required
            fullWidth
            id="last_name"
            label="Last Name"
            name="last_name"
            value={formData.last_name}
            onChange={handleChange}
          />
          <TextField
            margin="normal"
            required
            fullWidth
            id="email"
            label="Email Address"
            name="email"
            autoComplete="email"
            value={formData.email}
            onChange={handleChange}
          />
          <TextField
            margin="normal"
            required
            fullWidth
            name="password"
            label="Password"
            type="password"
            id="password"
            value={formData.password}
            onChange={handleChange}
          />
          <TextField
            margin="normal"
            required
            fullWidth
            id="phone"
            label="Phone Number"
            name="phone"
            placeholder="+1234567890"
            value={formData.phone}
            onChange={handleChange}
          />

          <FormControl sx={{ mt: 2, mb: 2 }}>
            <FormLabel id="user-type-label">I want to:</FormLabel>
            <RadioGroup
              row
              aria-labelledby="user-type-label"
              name="user_type"
              value={formData.user_type}
              onChange={handleChange}
            >
              <FormControlLabel value="rider" control={<Radio />} label="Request Rides" />
              <FormControlLabel value="driver" control={<Radio />} label="Drive for Rides" />
            </RadioGroup>
          </FormControl>

          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={loading}
          >
            {loading ? 'Creating Account...' : 'Sign Up'}
          </Button>
          <Box textAlign="center">
            <Link
              component="button"
              variant="body2"
              onClick={() => navigate('/login')}
            >
              Already have an account? Sign In
            </Link>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
}

export default RegisterPage;