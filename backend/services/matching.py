from models.db import get_db
from utils.security import calculate_distance
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_nearest_drivers(pickup_location, ride_type, limit=10, max_distance_km=10):
    """
    Find multiple nearest available drivers for a ride request
    
    Args:
        pickup_location (dict): Pickup coordinates {'lat': float, 'lng': float}
        ride_type (str): Type of ride (economy, comfort, premium, xl)
        limit (int): Maximum number of drivers to return
        max_distance_km (int): Maximum distance to search for drivers
    
    Returns:
        list: List of driver information
    """
    try:
        db = get_db()
        
        # Find available drivers within the specified radius
        available_drivers = list(db.drivers.find({
            'is_online': True,
            'current_ride_id': None,
            'current_location': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [pickup_location['lng'], pickup_location['lat']]
                    },
                    '$maxDistance': max_distance_km * 1000  # Convert km to meters
                }
            }
        }).limit(limit))
        
        if not available_drivers:
            logger.info("No available drivers found within range")
            return []
        
        # Filter drivers by vehicle type compatibility
        compatible_drivers = filter_drivers_by_ride_type(available_drivers, ride_type)
        
        # Calculate distances and add to driver data
        for driver in compatible_drivers:
            if driver.get('current_location'):
                distance = calculate_distance(
                    pickup_location['lat'], pickup_location['lng'],
                    driver['current_location']['lat'], driver['current_location']['lng']
                )
                driver['distance_km'] = distance
        
        # Sort by distance
        compatible_drivers.sort(key=lambda x: x.get('distance_km', float('inf')))
        
        logger.info(f"Found {len(compatible_drivers)} compatible drivers")
        return compatible_drivers
        
    except Exception as e:
        logger.error(f"❌ Error finding nearest drivers: {e}")
        return []

def find_nearest_driver(pickup_location, ride_type, max_distance_km=10):
    """
    Find the nearest available driver for a ride request
    
    Args:
        pickup_location (dict): Pickup coordinates {'lat': float, 'lng': float}
        ride_type (str): Type of ride (economy, comfort, premium, xl)
        max_distance_km (int): Maximum distance to search for drivers
    
    Returns:
        dict: Driver information or None if no driver found
    """
    try:
        db = get_db()
        
        # Find available drivers within the specified radius
        available_drivers = list(db.drivers.find({
            'is_online': True,
            'current_ride_id': None,
            'current_location': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [pickup_location['lng'], pickup_location['lat']]
                    },
                    '$maxDistance': max_distance_km * 1000  # Convert km to meters
                }
            }
        }).limit(20))
        
        if not available_drivers:
            logger.info("No available drivers found within range")
            return None
        
        # Filter drivers by vehicle type compatibility
        compatible_drivers = filter_drivers_by_ride_type(available_drivers, ride_type)
        
        if not compatible_drivers:
            logger.info("No compatible drivers found for ride type")
            return None
        
        # Find the closest driver
        closest_driver = find_closest_driver(compatible_drivers, pickup_location)
        
        if closest_driver:
            logger.info(f"Found driver {closest_driver['_id']} at distance {closest_driver.get('distance_km', 0):.2f}km")
        
        return closest_driver
        
    except Exception as e:
        logger.error(f"❌ Error finding nearest drivers: {e}")
        return None

def filter_drivers_by_ride_type(drivers, ride_type):
    """
    Filter drivers based on ride type compatibility
    """
    compatible_drivers = []
    
    for driver in drivers:
        vehicle_type = driver.get('vehicle_type', 'sedan')
        
        # Check if driver's vehicle is compatible with ride type
        if is_vehicle_compatible(vehicle_type, ride_type):
            compatible_drivers.append(driver)
    
    return compatible_drivers

def is_vehicle_compatible(vehicle_type, ride_type):
    """
    Check if a vehicle type is compatible with a ride type
    """
    compatibility_matrix = {
        'economy': ['sedan', 'hatchback', 'compact'],
        'comfort': ['sedan', 'suv', 'luxury'],
        'premium': ['luxury', 'suv'],
        'xl': ['xl', 'suv', 'van']
    }
    
    return vehicle_type in compatibility_matrix.get(ride_type, [])

def find_closest_driver(drivers, pickup_location):
    """
    Find the driver closest to the pickup location
    """
    if not drivers:
        return None
    
    closest_driver = None
    min_distance = float('inf')
    
    for driver in drivers:
        driver_location = driver.get('current_location')
        if not driver_location or 'lat' not in driver_location or 'lng' not in driver_location:
            continue
            
        # Calculate distance between pickup and driver
        try:
            distance = calculate_distance(
                float(pickup_location['lat']), float(pickup_location['lng']),
                float(driver_location['lat']), float(driver_location['lng'])
            )
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error calculating distance: {e}")
            continue
        
        # Add some randomization to avoid always picking the same driver
        # Add a small random factor (±10%) to the distance
        import random
        random_factor = 1 + (random.random() - 0.5) * 0.2
        adjusted_distance = distance * random_factor
        
        if adjusted_distance < min_distance:
            min_distance = adjusted_distance
            closest_driver = driver
            closest_driver['distance_km'] = distance
    
    return closest_driver

def get_driver_eta(driver, pickup_location):
    """
    Calculate estimated time of arrival for a driver
    """
    try:
        driver_location = driver.get('current_location')
        if not driver_location:
            return 5  # Default 5 minutes
        
        # Calculate distance
        distance_km = calculate_distance(
            pickup_location['lat'], pickup_location['lng'],
            driver_location['lat'], driver_location['lng']
        )
        
        # Estimate time based on distance (assuming average speed of 30 km/h in city)
        # Add some buffer time for traffic
        estimated_minutes = int((distance_km / 30) * 60) + 2
        
        return max(estimated_minutes, 3)  # Minimum 3 minutes
        
    except Exception as e:
        logger.error(f"Error calculating driver ETA: {e}")
        return 5  # Default fallback

def find_drivers_in_area(center_location, radius_km=5, limit=50):
    """
    Find all drivers in a specific area
    """
    try:
        db = get_db()
        
        drivers = list(db.drivers.find({
            'is_online': True,
            'current_location': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [center_location['lng'], center_location['lat']]
                    },
                    '$maxDistance': radius_km * 1000
                }
            }
        }).limit(limit))
        
        return drivers
        
    except Exception as e:
        logger.error(f"❌ Error finding drivers in area: {e}")
        return []

def update_driver_availability(driver_id, is_available):
    """
    Update driver availability status
    """
    try:
        db = get_db()
        
        result = db.drivers.update_one(
            {'user_id': driver_id},
            {
                '$set': {
                    'is_online': is_available,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
        
    except Exception as e:
        logger.error(f"❌ Error updating driver availability: {e}")
        return False
