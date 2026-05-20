from rest_framework import serializers

from .models import (
    Product,
    Category,
    SubCategory,
    Wishlist
)


# CATEGORY
class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'


# SUBCATEGORY
class SubCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SubCategory
        fields = '__all__'


# PRODUCT - FIXED with relative image URL
class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def get_image(self, obj):
        if obj.image:
            # Return relative path (starts with /media/)
            return obj.image.url
        return None


# WISHLIST
class WishlistSerializer(serializers.ModelSerializer):

    product = ProductSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = '__all__'