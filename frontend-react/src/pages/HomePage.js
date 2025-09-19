import React from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  Paper,
} from '@mui/material';
import { DirectionsCar, Person, Security, Speed } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function HomePage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const features = [
    {
      icon: <DirectionsCar sx={{ fontSize: 40 }} />,
      title: 'Quick Rides',
      description: 'Get a ride in minutes with our network of drivers',
    },
    {
      icon: <Security sx={{ fontSize: 40 }} />,
      title: 'Safe & Secure',
      description: 'Background-checked drivers and secure payment options',
    },
    {
      icon: <Speed sx={{ fontSize: 40 }} />,
      title: 'Fast Matching',
      description: 'Advanced algorithm to match you with nearby drivers',
    },
    {
      icon: <Person sx={{ fontSize: 40 }} />,
      title: 'Professional Drivers',
      description: 'Experienced and professional drivers at your service',
    },
  ];

  return (
    <Box>
      {/* Hero Section */}
      <Paper
        sx={{
          backgroundImage: 'linear-gradient(135deg, #000000 0%, #434343 100%)',
          color: 'white',
          py: 8,
          textAlign: 'center',
        }}
      >
        <Container maxWidth="md">
          <Typography variant="h2" component="h1" gutterBottom>
            Get a ride, anytime, anywhere
          </Typography>
          <Typography variant="h5" sx={{ mb: 4, opacity: 0.9 }}>
            The modern way to move around the city
          </Typography>
          {!user && (
            <Box sx={{ gap: 2, display: 'flex', justifyContent: 'center' }}>
              <Button
                variant="contained"
                size="large"
                sx={{
                  backgroundColor: 'white',
                  color: 'black',
                  '&:hover': { backgroundColor: '#f0f0f0' }
                }}
                onClick={() => navigate('/register')}
              >
                Get Started
              </Button>
              <Button
                variant="outlined"
                size="large"
                sx={{
                  borderColor: 'white',
                  color: 'white',
                  '&:hover': { borderColor: '#f0f0f0', backgroundColor: 'rgba(255,255,255,0.1)' }
                }}
                onClick={() => navigate('/login')}
              >
                Sign In
              </Button>
            </Box>
          )}
          {user && (
            <Button
              variant="contained"
              size="large"
              sx={{
                backgroundColor: 'white',
                color: 'black',
                '&:hover': { backgroundColor: '#f0f0f0' }
              }}
              onClick={() => navigate('/dashboard')}
            >
              Go to Dashboard
            </Button>
          )}
        </Container>
      </Paper>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography variant="h3" textAlign="center" gutterBottom>
          Why Choose Our Service?
        </Typography>
        <Typography
          variant="h6"
          textAlign="center"
          color="textSecondary"
          sx={{ mb: 6 }}
        >
          Experience the future of transportation
        </Typography>

        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card
                sx={{
                  height: '100%',
                  textAlign: 'center',
                  transition: 'transform 0.2s',
                  '&:hover': { transform: 'translateY(-4px)' },
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ color: 'primary.main', mb: 2 }}>
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" gutterBottom>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* CTA Section */}
      <Box sx={{ backgroundColor: '#f5f5f5', py: 6 }}>
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          <Typography variant="h4" gutterBottom>
            Ready to get started?
          </Typography>
          <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
            Join thousands of riders and drivers in our community
          </Typography>
          <Box sx={{ gap: 2, display: 'flex', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/register?type=rider')}
            >
              Become a Rider
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('/register?type=driver')}
            >
              Become a Driver
            </Button>
          </Box>
        </Container>
      </Box>
    </Box>
  );
}

export default HomePage;