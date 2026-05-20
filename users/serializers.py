# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserAddress

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'profile_picture',
                  'address', 'city', 'state', 'pincode', 'bio', 'date_joined']


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'profile_picture',
                  'address', 'city', 'state', 'pincode', 'bio']


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['id', 'full_name', 'phone', 'address', 'city',
                  'state', 'pincode', 'is_default', 'created_at']
        read_only_fields = ['id', 'created_at']
