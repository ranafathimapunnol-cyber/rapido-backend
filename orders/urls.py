# orders/urls.py - UPDATED FOR GENERIC VIEWS
from django.urls import path
from .views import (
    CreateOrderView,
    MyOrdersView,
    OrderDetailView,
    UpdateOrderStatusView,
    AdminOrdersView,
    AdminOrderDetailView,
    AdminUpdateOrderStatusView,
    AdminCancelOrderView,
    AdminDeleteOrderView,
)

urlpatterns = [
    # User endpoints
    path('create/', CreateOrderView.as_view(), name='create-order'),
    path('my-orders/', MyOrdersView.as_view(), name='my-orders'),
    path('<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/update/', UpdateOrderStatusView.as_view(),
         name='update-order-status'),

    # Admin endpoints
    path('', AdminOrdersView.as_view(), name='admin-orders'),
    path('admin/', AdminOrdersView.as_view(), name='admin-orders-alias'),
    path('admin/<int:order_id>/', AdminOrderDetailView.as_view(),
         name='admin-order-detail'),
    path('<int:order_id>/status/', AdminUpdateOrderStatusView.as_view(),
         name='admin-update-status'),
    path('<int:order_id>/cancel/',
         AdminCancelOrderView.as_view(), name='cancel-order'),
    path('delete/<int:pk>/', AdminDeleteOrderView.as_view(), name='delete-order'),
]
