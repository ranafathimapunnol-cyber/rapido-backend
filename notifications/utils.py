import requests
import json

SOCKET_SERVER_URL = "http://localhost:3002"


def send_notification_to_admin(user, notification_type, title, message, data=None):
    """
    Send real-time notification from user to admin via Socket.IO

    Args:
        user: Django user object
        notification_type: 'new_order', 'new_message', 'payment', etc.
        title: Notification title
        message: Notification message
        data: Dictionary with extra data (order_id, etc.)

    Returns:
        bool: True if sent successfully, False otherwise
    """
    # First, save to database
    try:
        from .models import Notification
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {}
        )
        print(f"✅ Notification saved to DB: {notification.id}")
    except Exception as e:
        print(f"⚠️ Could not save to DB: {e}")

    # Send to Socket.IO server
    payload = {
        'userId': user.id,
        'userName': user.username,
        'notificationType': notification_type,
        'title': title,
        'message': message,
        'data': data or {}
    }

    try:
        response = requests.post(
            f"{SOCKET_SERVER_URL}/api/notify-admin",
            json=payload,
            timeout=2
        )
        if response.status_code == 200:
            print(f"✅ Real-time notification sent to admin")
            return True
        else:
            print(f"⚠️ Socket server responded with: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"⚠️ Socket.IO server not running. Start it with: cd ~/Desktop/E-commerceShoes/socket-server && npm run dev")
        return False
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")
        return False


def send_update_to_user(user_id, title, message, data=None):
    """
    Send update from admin to specific user

    Args:
        user_id: ID of the user to send update to
        title: Notification title
        message: Notification message
        data: Dictionary with extra data

    Returns:
        bool: True if sent successfully, False otherwise
    """
    payload = {
        'userId': user_id,
        'title': title,
        'message': message,
        'data': data or {}
    }

    try:
        response = requests.post(
            f"{SOCKET_SERVER_URL}/api/notify-user",
            json=payload,
            timeout=2
        )
        if response.status_code == 200:
            print(f"✅ Update sent to user {user_id}")
            return True
        else:
            print(f"⚠️ Socket server responded with: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"⚠️ Socket.IO server not running")
        return False
    except Exception as e:
        print(f"❌ Failed to send user update: {e}")
        return False


def get_unread_count(user):
    """Get unread notification count for a user"""
    if not user.is_authenticated:
        return 0

    try:
        from .models import Notification
        if user.is_staff:
            return Notification.objects.filter(is_read=False).count()
        else:
            return Notification.objects.filter(user=user, is_read=False).count()
    except:
        return 0
