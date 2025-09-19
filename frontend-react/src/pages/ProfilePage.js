import React from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  Grid,
  TextField,
  Button,
  Avatar,
} from '@mui/material';
import { Person } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

function ProfilePage() {
  const { user } = useAuth();

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
          <Avatar sx={{ width: 80, height: 80, mr: 3 }}>
            <Person sx={{ fontSize: 40 }} />
          </Avatar>
          <Box>
            <Typography variant="h4" gutterBottom>
              {user?.first_name} {user?.last_name}
            </Typography>
            <Typography variant="subtitle1" color="textSecondary">
              {user?.user_type === 'rider' ? 'Rider' : 'Driver'} Account
            </Typography>
          </Box>
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="First Name"
              value={user?.first_name || ''}
              disabled
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Last Name"
              value={user?.last_name || ''}
              disabled
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Email"
              value={user?.email || ''}
              disabled
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Phone"
              value={user?.phone || ''}
              disabled
            />
          </Grid>
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              <Button variant="contained">
                Edit Profile
              </Button>
              <Button variant="outlined">
                Change Password
              </Button>
            </Box>
          </Grid>
        </Grid>

        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            Account Status
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Email Verified: {user?.email_verified ? '✅ Yes' : '❌ No'}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Phone Verified: {user?.phone_verified ? '✅ Yes' : '❌ No'}
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
}

export default ProfilePage;