# orders/views.py - CONVERTED TO GENERIC VIEWS (ALL FEATURES PRESERVED)
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .models import Order, OrderItem
from products.models import Product
from .serializers import OrderSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


import requests 
import json

User = get_user_model()


# =========================
# 1. CREATE ORDER (USER) - WITH SOCKET.IO EMISSION
# =========================
class CreateOrderView(GenericAPIView):
    """Create new order with stock deduction and duplicate prevention"""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def emit_socket_event(self, event_name, data):
        """Emit event to Socket.IO server"""
        try:
            # Your Socket.IO server URL (adjust port if needed)
            socket_url = 'http://localhost:5000'  # Change to your Socket.IO server
            
            # Send event to Socket.IO server
            response = requests.post(f'{socket_url}/emit-event', json={
                'event': event_name,
                'data': data
            })
            
            if response.status_code == 200:
                print(f"✅ Socket.IO event '{event_name}' emitted")
            else:
                print(f"⚠️ Socket.IO emission failed: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Socket.IO connection error: {e}")

    def post(self, request):
        try:
            data = request.data
            items = data.get('items', [])
            total_price = data.get('total_price')
            shipping_address = data.get('shipping_address', '')
            payment_method = data.get('payment_method', 'cod')

            if not items:
                return Response({'error': 'No items in order'}, status=status.HTTP_400_BAD_REQUEST)

            if not total_price:
                return Response({'error': 'Total price is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Check stock
            stock_errors = []
            for item in items:
                product_id = item.get('product')
                quantity = item.get('quantity', 1)
                try:
                    product = Product.objects.get(id=product_id)
                    if product.stock < quantity:
                        stock_errors.append(
                            f"{product.name}: Only {product.stock} available")
                except Product.DoesNotExist:
                    return Response({'error': f'Product with ID {product_id} not found'}, status=status.HTTP_400_BAD_REQUEST)

            if stock_errors:
                return Response({'error': 'Insufficient stock', 'details': stock_errors}, status=status.HTTP_400_BAD_REQUEST)

            # Create Order
            order = Order.objects.create(
                user=request.user,
                total_price=total_price,
                is_paid=(payment_method != 'cod'),
                status='pending',
                shipping_address=shipping_address,
                payment_method=payment_method
            )

            # Create Order Items and deduct stock
            order_total = 0
            order_items_list = []
            
            for item in items:
                product = Product.objects.get(id=item['product'])
                quantity = item.get('quantity', 1)
                item_price = product.price * quantity

                product.stock -= quantity
                product.save()

                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=item_price
                )
                order_total += item_price
                
                order_items_list.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'quantity': quantity,
                    'price': str(item_price),
                    'image': product.image.url if product.image else None
                })

            order.total_price = order_total
            order.save()

            # NOTIFICATION DISABLED - Handled by signal in notifications app
            # This block is commented out to prevent duplicate notifications
            # The signal in notifications/views.py creates the notification
            """
            try:
                from notifications.models import Notification
                admin_users = User.objects.filter(is_staff=True)
                for admin in admin_users:
                    existing = Notification.objects.filter(
                        user=admin,
                        message__contains=f'Order #{order.id}'
                    ).exists()
                    if not existing:
                        Notification.objects.create(
                            user=admin,
                            title='🛒 New Order!',
                            message=f'Order #{order.id} - ₹{order_total} from {request.user.username}',
                            notification_type='order'
                        )
            except Exception as e:
                print(f"Notification creation failed: {e}")
            """

            # ✅ EMIT SOCKET.IO EVENT FOR REAL-TIME NOTIFICATION
            socket_data = {
                'order_id': order.id,
                'total_amount': str(order_total),
                'customer_name': request.user.username,
                'customer_email': request.user.email,
                'items_count': len(items),
                'items': order_items_list,
                'status': order.status,
                'timestamp': str(order.created_at)
            }
            
            # Emit to Socket.IO server
            self.emit_socket_event('new_order', socket_data)

            return Response({
                'success': True,
                'message': 'Order placed successfully',
                'order_id': order.id,
                'status': order.status,
                'total_price': str(order.total_price)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print("Error creating order:", str(e))
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =========================
# 2. MY ORDERS (USER)
# =========================
class MyOrdersView(ListAPIView):
    """Get current user's orders"""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


# =========================
# 3. ORDER DETAIL (USER)
# =========================
class OrderDetailView(RetrieveAPIView):
    """Get single order details for current user"""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_object(self):
        return self.get_queryset().get(id=self.kwargs['order_id'])


# =========================
# 4. UPDATE ORDER STATUS (USER)
# =========================
class UpdateOrderStatusView(GenericAPIView):
    """User updates their own order status following flow"""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        status_flow = {
            'pending': 'confirmed',
            'confirmed': 'processing',
            'processing': 'shipped',
            'shipped': 'out_for_delivery',
            'out_for_delivery': 'delivered'
        }

        if order.status in status_flow:
            order.status = status_flow[order.status]
            order.save()
            return Response({'status': order.status, 'message': 'Status updated'}, status=status.HTTP_200_OK)

        return Response({'error': 'Cannot update status'}, status=status.HTTP_400_BAD_REQUEST)


# =========================
# 5. ADMIN - GET ALL ORDERS
# =========================
class AdminOrdersView(ListAPIView):
    """Get (all orders) for admin panel"""
    permission_classes = [IsAdminUser]
    serializer_class = OrderSerializer
    queryset = Order.objects.all().order_by('-created_at')


# =========================
# 6. ADMIN - GET SINGLE ORDER
# =========================
class AdminOrderDetailView(RetrieveAPIView):
    """Get single order for admin"""
    permission_classes = [IsAdminUser]
    serializer_class = OrderSerializer
    lookup_field = 'order_id'
    lookup_url_kwarg = 'order_id'

    def get_queryset(self):
        return Order.objects.all()


# =========================
# 7. ADMIN - UPDATE ORDER STATUS
# =========================
class AdminUpdateOrderStatusView(GenericAPIView):
    """Admin updates order status"""
    permission_classes = [IsAdminUser]

    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if 'status' not in request.data:
            return Response({"error": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)

        new_status = request.data['status'].lower()
        valid_statuses = ['pending', 'processing',
                          'shipped', 'delivered', 'cancelled']

        if new_status not in valid_statuses:
            return Response({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save()

        return Response({
            "message": "Order status updated successfully",
            "id": order.id,
            "status": order.status
        }, status=status.HTTP_200_OK)

    # Support PUT and POST methods too (for frontend compatibility)
    def put(self, request, order_id):
        return self.patch(request, order_id)

    def post(self, request, order_id):
        return self.patch(request, order_id)


# =========================
# 8. ADMIN - CANCEL ORDER (WITH STOCK RESTORE)
# =========================
class AdminCancelOrderView(GenericAPIView):
    """Admin cancels order and restores stock"""
    permission_classes = [IsAdminUser]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.status == 'cancelled':
            return Response({"error": "Order already cancelled"}, status=status.HTTP_400_BAD_REQUEST)

        # Restore stock
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

        order.status = 'cancelled'
        order.save()

        return Response({
            "message": "Order cancelled and stock restored",
            "id": order.id,
            "status": order.status
        }, status=status.HTTP_200_OK)


# =========================
# 9. ADMIN - DELETE ORDER (WITH STOCK RESTORE)
# =========================
class AdminDeleteOrderView(GenericAPIView):
    """Admin deletes order permanently and restores stock"""
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        try:
            order = Order.objects.get(id=pk)

            # Restore stock before deleting
            for item in order.items.all():
                product = item.product
                product.stock += item.quantity
                product.save()

            order.delete()
            return Response({"message": "Order deleted successfully"}, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
