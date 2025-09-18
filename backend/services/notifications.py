from models.db import get_db
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_notification(user_id, title, message, notification_type, data=None):
    """
    Create a notification for a user (alias for send_notification for compatibility)
    
    Args:
        user_id (str): User ID to send notification to
        title (str): Notification title
        message (str): Notification message
        notification_type (str): Type of notification
        data (dict): Additional data for the notification
    
    Returns:
        bool: True if notification was created successfully
    """
    return send_notification(user_id, notification_type, f"{title}: {message}", data)

def send_notification(user_id, notification_type, message, data=None):
    """
    Send a notification to a user
    
    Args:
        user_id (str): User ID to send notification to
        notification_type (str): Type of notification
        message (str): Notification message
        data (dict): Additional data for the notification
    
    Returns:
        bool: True if notification was sent successfully
    """
    try:
        db = get_db()
        
        # Create notification record
        notification_data = {
            'user_id': user_id,
            'type': notification_type,
            'message': message,
            'data': data or {},
            'read': False,
            'created_at': datetime.utcnow()
        }
        
        # Insert notification into database
        result = db.notifications.insert_one(notification_data)
        
        if result.inserted_id:
            logger.info(f"📱 Notification sent to user {user_id}: {message}")
            
            # Here you would typically:
            # 1. Send push notification if user has mobile app
            # 2. Send email notification
            # 3. Send SMS notification
            # 4. Send in-app notification via WebSocket
            
            # For now, we'll just log the notification
            return True
        else:
            logger.error(f"❌ Failed to create notification for user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending notification: {e}")
        return False

def send_ride_notification(ride_id, notification_type, message, data=None):
    """
    Send notification related to a specific ride
    """
    try:
        db = get_db()
        
        # Get ride information
        ride = db.rides.find_one({'_id': ride_id})
        if not ride:
            logger.error(f"❌ Ride {ride_id} not found for notification")
            return False
        
        # Send notification to rider
        if 'rider_id' in ride:
            send_notification(
                ride['rider_id'],
                notification_type,
                message,
                data
            )
        
        # Send notification to driver if assigned
        if 'driver_id' in ride:
            send_notification(
                ride['driver_id'],
                notification_type,
                message,
                data
            )
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error sending ride notification: {e}")
        return False

def mark_notification_read(notification_id, user_id):
    """
    Mark a notification as read
    """
    try:
        db = get_db()
        
        result = db.notifications.update_one(
            {
                '_id': notification_id,
                'user_id': user_id
            },
            {
                '$set': {
                    'read': True,
                    'read_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Notification {notification_id} marked as read")
            return True
        else:
            logger.warning(f"⚠️ Notification {notification_id} not found or already read")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error marking notification as read: {e}")
        return False

def get_user_notifications(user_id, limit=50, unread_only=False):
    """
    Get notifications for a specific user
    """
    try:
        db = get_db()
        
        # Build query
        query = {'user_id': user_id}
        if unread_only:
            query['read'] = False
        
        # Get notifications
        notifications = list(db.notifications.find(query)
                           .sort('created_at', -1)
                           .limit(limit))
        
        # Format notifications for response
        formatted_notifications = []
        for notification in notifications:
            formatted_notifications.append({
                'id': str(notification['_id']),
                'type': notification['type'],
                'message': notification['message'],
                'data': notification.get('data', {}),
                'read': notification.get('read', False),
                'created_at': notification['created_at'].isoformat(),
                'read_at': notification.get('read_at', '').isoformat() if notification.get('read_at') else None
            })
        
        return formatted_notifications
        
    except Exception as e:
        logger.error(f"❌ Error getting user notifications: {e}")
        return []

def send_bulk_notification(user_ids, notification_type, message, data=None):
    """
    Send the same notification to multiple users
    """
    try:
        success_count = 0
        
        for user_id in user_ids:
            if send_notification(user_id, notification_type, message, data):
                success_count += 1
        
        logger.info(f"📱 Bulk notification sent to {success_count}/{len(user_ids)} users")
        return success_count
        
    except Exception as e:
        logger.error(f"❌ Error sending bulk notification: {e}")
        return 0

def send_system_notification(message, user_type=None):
    """
    Send system-wide notification to all users or specific user type
    """
    try:
        db = get_db()
        
        # Build query for users
        query = {}
        if user_type:
            query['user_type'] = user_type
        
        # Get user IDs
        users = list(db.users.find(query, {'_id': 1}))
        user_ids = [str(user['_id']) for user in users]
        
        # Send bulk notification
        return send_bulk_notification(
            user_ids,
            'system',
            message,
            {'system_notification': True}
        )
        
    except Exception as e:
        logger.error(f"❌ Error sending system notification: {e}")
        return 0

def cleanup_old_notifications(days_old=30):
    """
    Clean up old notifications to keep database clean
    """
    try:
        db = get_db()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        result = db.notifications.delete_many({
            'created_at': {'$lt': cutoff_date},
            'read': True  # Only delete read notifications
        })
        
        if result.deleted_count > 0:
            logger.info(f"🧹 Cleaned up {result.deleted_count} old notifications")
        
        return result.deleted_count
        
    except Exception as e:
        logger.error(f"❌ Error cleaning up old notifications: {e}")
        return 0
