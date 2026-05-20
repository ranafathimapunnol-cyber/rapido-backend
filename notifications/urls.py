# notifications/urls.py - ADD test endpoint
from django.urls import path
from .views import (
    GetAdminNotificationsView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
    DeleteNotificationView,
    ClearAllNotificationsView,
    TestClearAllView,
    TestSocketNotificationView,  
    CreateNotificationView
)

urlpatterns = [
    path('admin/', GetAdminNotificationsView.as_view(), name='admin-notifications'),
    path('mark-read/<int:notification_id>/', MarkNotificationReadView.as_view(), name='mark-read'),
    path('mark-all-read/', MarkAllNotificationsReadView.as_view(), name='mark-all-read'),
    path('delete/<int:notification_id>/', DeleteNotificationView.as_view(), name='delete-notification'),
    path('clear-all/', ClearAllNotificationsView.as_view(), name='clear-all'),
    path('test-clear-all/', TestClearAllView.as_view(), name='test-clear-all'),
    path('test-socket/', TestSocketNotificationView.as_view(), name='test-socket'), 
    path('create/', CreateNotificationView.as_view(), name='create-notification'),

]