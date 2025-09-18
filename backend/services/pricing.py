from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_fare(ride_data):
    """
    Calculate final fare for a completed ride
    
    Args:
        ride_data (dict): Ride information including distance, time, and type
    
    Returns:
        float: Final fare amount
    """
    try:
        # Base fare for different ride types
        base_fares = {
            'economy': 2.50,
            'comfort': 3.00,
            'premium': 4.50,
            'xl': 5.00
        }
        
        # Per kilometer rates
        per_km_rates = {
            'economy': 1.50,
            'comfort': 1.80,
            'premium': 2.50,
            'xl': 2.80
        }
        
        # Per minute rates (for time-based pricing)
        per_minute_rates = {
            'economy': 0.15,
            'comfort': 0.20,
            'premium': 0.30,
            'xl': 0.35
        }
        
        ride_type = ride_data.get('ride_type', 'economy')
        distance_km = ride_data.get('distance_km', 0)
        
        # Calculate time-based fare if ride duration is available
        time_fare = 0
        if 'started_at' in ride_data and 'completed_at' in ride_data:
            try:
                start_time = ride_data['started_at']
                end_time = ride_data['completed_at']
                
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                
                duration_minutes = (end_time - start_time).total_seconds() / 60
                time_fare = duration_minutes * per_minute_rates.get(ride_type, 0.15)
            except Exception as e:
                logger.warning(f"Could not calculate time-based fare: {e}")
                # Fallback to distance-based only
        
        # Calculate distance-based fare
        distance_fare = distance_km * per_km_rates.get(ride_type, 1.50)
        
        # Get base fare
        base_fare = base_fares.get(ride_type, 2.50)
        
        # Calculate total fare
        total_fare = base_fare + distance_fare + time_fare
        
        # Apply surge pricing if applicable
        surge_multiplier = get_surge_multiplier(ride_data)
        total_fare *= surge_multiplier
        
        # Apply any discounts
        discount_amount = get_discount_amount(ride_data)
        total_fare -= discount_amount
        
        # Ensure minimum fare
        min_fares = {
            'economy': 5.00,
            'comfort': 6.00,
            'premium': 8.00,
            'xl': 10.00
        }
        
        total_fare = max(total_fare, min_fares.get(ride_type, 5.00))
        
        # Round to 2 decimal places
        final_fare = round(total_fare, 2)
        
        logger.info(f"Calculated fare for ride {ride_data.get('_id')}: ${final_fare}")
        
        return final_fare
        
    except Exception as e:
        logger.error(f"❌ Error calculating fare: {e}")
        # Return estimated fare as fallback
        return ride_data.get('estimated_fare', 10.00)

def get_surge_multiplier(ride_data):
    """
    Calculate surge pricing multiplier based on demand and time
    """
    try:
        # Check if it's peak hours (rush hour)
        current_hour = datetime.utcnow().hour
        
        # Morning rush: 7-9 AM, Evening rush: 5-7 PM
        is_peak_hour = (7 <= current_hour <= 9) or (17 <= current_hour <= 19)
        
        # Check if it's weekend
        is_weekend = datetime.utcnow().weekday() >= 5
        
        # Base surge multiplier
        surge_multiplier = 1.0
        
        if is_peak_hour:
            surge_multiplier += 0.2  # 20% increase during peak hours
        
        if is_weekend:
            surge_multiplier += 0.1  # 10% increase on weekends
        
        # Check for special events or high demand areas
        # This would typically integrate with external APIs for real-time demand data
        
        return surge_multiplier
        
    except Exception as e:
        logger.error(f"Error calculating surge multiplier: {e}")
        return 1.0

def get_discount_amount(ride_data):
    """
    Calculate discount amount based on various factors
    """
    try:
        discount_amount = 0
        
        # Check if rider has any active promotions
        # This would typically check a promotions collection
        
        # Check if it's rider's first ride
        # This would check rider's total_rides count
        
        # Check for loyalty discounts
        # This would check rider's rating and ride count
        
        return discount_amount
        
    except Exception as e:
        logger.error(f"Error calculating discount: {e}")
        return 0

def estimate_fare(pickup_location, destination_location, ride_type, passengers=1):
    """
    Estimate fare before ride starts
    
    Args:
        pickup_location (dict): Pickup coordinates
        destination_location (dict): Destination coordinates
        ride_type (str): Type of ride
        passengers (int): Number of passengers
    
    Returns:
        dict: Fare estimate information
    """
    try:
        from utils.security import calculate_distance
        
        # Calculate distance
        distance_km = calculate_distance(
            pickup_location['lat'], pickup_location['lng'],
            destination_location['lat'], destination_location['lng']
        )
        
        # Base fare calculation
        base_fares = {
            'economy': 2.50,
            'comfort': 3.00,
            'premium': 4.50,
            'xl': 5.00
        }
        
        per_km_rates = {
            'economy': 1.50,
            'comfort': 1.80,
            'premium': 2.50,
            'xl': 2.80
        }
        
        base_fare = base_fares.get(ride_type, 2.50)
        per_km_rate = per_km_rates.get(ride_type, 1.50)
        
        # Calculate estimated fare
        distance_fare = distance_km * per_km_rate
        estimated_fare = base_fare + distance_fare
        
        # Apply passenger multiplier for XL rides
        if ride_type == 'xl' and passengers > 1:
            passenger_multiplier = 1 + (passengers - 1) * 0.1
            estimated_fare *= passenger_multiplier
        
        # Apply surge pricing
        surge_multiplier = get_surge_multiplier({})
        estimated_fare *= surge_multiplier
        
        # Round to 2 decimal places
        estimated_fare = round(estimated_fare, 2)
        
        # Calculate estimated time
        estimated_time_minutes = int(distance_km * 2) + 5  # Rough estimate
        
        return {
            'estimated_fare': estimated_fare,
            'distance_km': round(distance_km, 2),
            'estimated_time_minutes': estimated_time_minutes,
            'base_fare': base_fare,
            'per_km_rate': per_km_rate,
            'surge_multiplier': surge_multiplier
        }
        
    except Exception as e:
        logger.error(f"❌ Error estimating fare: {e}")
        return {
            'estimated_fare': 10.00,
            'distance_km': 0,
            'estimated_time_minutes': 10,
            'base_fare': 2.50,
            'per_km_rate': 1.50,
            'surge_multiplier': 1.0
        }
