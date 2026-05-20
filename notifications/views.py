# notifications/views.py - ADD SOCKET NOTIFICATION
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .models import Notification
from .serializers import NotificationSerializer
import requests
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver

# Function to send notification to Node.js socket server
def send_to_socket_server(event, data):
    """Send notification to Node.js socket server"""
    try:
        response = requests.post(
            'http://localhost:5000/emit',
            json={'event': event, 'data': data},
            timeout=2,
            headers={'Content-Type': 'application/json'}
        )
        print(f"✅ Socket notification sent: {response.status_code}")
    except Exception as e:
        print(f"❌ Socket notification failed: {e}")

# Signal to auto-send notification when created
@receiver(post_save, sender=Notification)
def notify_on_notification_created(sender, instance, created, **kwargs):
    if created:
        # Send to socket server in background
        thread = threading.Thread(
            target=send_to_socket_server,
            args=('admin:newNotification', {
                'title': instance.title,
                'message': instance.message,
                'notificationType': instance.notification_type,
                'data': {
                    'notification_id': instance.id,
                    'user_id': instance.user.id if instance.user else None
                },
                'timestamp': instance.created_at.isoformat()
            })
        )
        thread.start()
        print(f"🚀 Live notification sent: {instance.title}")

# =========================
# 1. GET ADMIN NOTIFICATIONS
# =========================
class GetAdminNotificationsView(ListAPIView):
    """Get all notifications for admin"""
    permission_classes = [IsAdminUser]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')[:100]


# =========================
# 2. MARK SINGLE NOTIFICATION AS READ
# =========================
class MarkNotificationReadView(GenericAPIView):
    """Mark a single notification as read"""
    permission_classes = [IsAdminUser]

    def post(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({'message': 'Notification marked as read'}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)


# =========================
# 3. MARK ALL NOTIFICATIONS AS READ
# =========================
class MarkAllNotificationsReadView(GenericAPIView):
    """Mark all notifications as read"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            updated = Notification.objects.filter(
                user=request.user, is_read=False).update(is_read=True)
            return Response({'message': f'{updated} notifications marked as read'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# 4. DELETE SINGLE NOTIFICATION
# =========================
class DeleteNotificationView(GenericAPIView):
    """PERMANENTLY delete a single notification"""
    permission_classes = [IsAdminUser]

    def delete(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id, user=request.user)
            notification_id_deleted = notification.id
            notification.delete()
            print(f"✅ Deleted notification: {notification_id_deleted}")
            return Response({
                'message': 'Notification permanently deleted',
                'deleted_id': notification_id_deleted
            }, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            print(f"❌ Notification {notification_id} not found")
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"❌ Error deleting: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# 5. CLEAR ALL NOTIFICATIONS
# =========================
class ClearAllNotificationsView(GenericAPIView):
    """PERMANENTLY delete ALL notifications for current admin"""
    permission_classes = [IsAdminUser]

    def delete(self, request):
        try:
            count = Notification.objects.filter(user=request.user).count()
            deleted_count = Notification.objects.filter(
                user=request.user).delete()[0]
            print(f"✅ Deleted {deleted_count} notifications for {request.user.username}")
            return Response({
                'message': f'{deleted_count} notifications permanently deleted',
                'deleted_count': deleted_count
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"❌ Error clearing all: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# 6. CREATE NOTIFICATION (Helper function)
# =========================
def create_notification(user, title, message, notification_type='info'):
    """Create a notification and send real-time alert"""
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type
    )
    return notification


# =========================
# 7. TEST ENDPOINT
# =========================
class TestClearAllView(GenericAPIView):
    """Test endpoint to verify clear-all functionality"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({"message": "Clear-all endpoint is accessible!"}, status=status.HTTP_200_OK)


# =========================
# 8. TEST SOCKET NOTIFICATION
# =========================
class TestSocketNotificationView(GenericAPIView):
    """Test endpoint to send a test notification"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        # Create a test notification
        notification = create_notification(
            user=request.user,
            title="🧪 Test Notification",
            message="This is a test notification from Django!",
            notification_type='info'
        )
        
        return Response({
            'message': 'Test notification sent!',
            'notification_id': notification.id
        }, status=status.HTTP_200_OK)
        # notifications/views.py - Add this endpoint
class CreateNotificationView(GenericAPIView):
    """Create a new notification"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            notification = Notification.objects.create(
                user=request.user,
                title=request.data.get('title'),
                message=request.data.get('message'),
                notification_type=request.data.get('notification_type', 'info')
            )
            serializer = NotificationSerializer(notification)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)