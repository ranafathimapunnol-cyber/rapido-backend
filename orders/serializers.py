# orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_name = serializers.SerializerMethodField()
    product_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name',
                  'product_price', 'quantity', 'price']

    def get_product_name(self, obj):
        return obj.product.name if obj.product else 'N/A'

    def get_product_price(self, obj):
        return str(obj.product.price) if obj.product else '0'


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_name', 'total_price', 'status', 'status_display',
            'is_paid', 'created_at', 'updated_at', 'shipping_address',
            'payment_method', 'tracking_number', 'items'
        ]

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.username
        return 'Guest'

    def get_status_display(self, obj):
        status_choices = dict(Order.STATUS_CHOICES)
        return status_choices.get(obj.status, obj.status)
