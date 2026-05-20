from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_price = serializers.ReadOnlyField(source='product.price')
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'product_name',
            'product_price',
            'product_image',
            'quantity',
        ]

    def get_product_image(self, obj):
        try:
            request = self.context.get('request')

            if obj.product.image:
                # SAFE CHECK (IMPORTANT)
                if request:
                    return request.build_absolute_uri(obj.product.image.url)
                else:
                    return obj.product.image.url

            return None

        except Exception:
            return None


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items']