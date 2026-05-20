# users/views.py - COMPLETE FIXED VERSION
from rest_framework.permissions import IsAdminUser
from .serializers import UserSerializer, UserUpdateSerializer, UserAddressSerializer
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status
from .models import UserAddress
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import json
import traceback

# Import Cart and Wishlist
from cart.models import Cart
from products.models import Wishlist

# Try to import Order, but handle if it doesn't exist
try:
    from orders.models import Order
    ORDER_MODEL_AVAILABLE = True
except ImportError:
    ORDER_MODEL_AVAILABLE = False
    print("Warning: Order model not available yet")

User = get_user_model()


# =========================
# JWT LOGIN
# =========================
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# =========================
# REGISTER
# =========================
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response(
            {'error': 'All fields are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )

    Cart.objects.create(user=user)

    return Response({
        'message': 'User created successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }, status=status.HTTP_201_CREATED)


# =========================
# USER PROFILE
# =========================
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        try:
            serializer = UserUpdateSerializer(
                user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error updating profile: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# SIMPLE PROFILE
# =========================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'phone': getattr(user, 'phone', ''),
        'profile_picture': user.profile_picture.url if hasattr(user, 'profile_picture') and user.profile_picture else None,
        'bio': getattr(user, 'bio', '')
    })


# =========================
# ADMIN LOGIN
# =========================
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """Admin login endpoint"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    print(f"Admin login attempt - Username: {username}")
    
    if not username or not password:
        return Response(
            {'error': 'Username and password are required', 'success': False},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if not user:
        print(f"Authentication failed for: {username}")
        return Response(
            {'error': 'Invalid username or password', 'success': False},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    print(f"User found: {user.username}, is_superuser: {user.is_superuser}, is_staff: {user.is_staff}")
    
    if user.is_superuser and user.is_staff:
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff
            }
        }, status=status.HTTP_200_OK)
    else:
        return Response(
            {'error': 'Access denied. Admin privileges required.', 'success': False},
            status=status.HTTP_403_FORBIDDEN
        )


# =========================
# ADDRESS VIEWS
# =========================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_addresses(request):
    user = request.user

    if request.method == 'GET':
        try:
            addresses = UserAddress.objects.filter(
                user=user).order_by('-is_default', '-created_at')
            serializer = UserAddressSerializer(addresses, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print("GET Addresses Error:", str(e))
            return Response(
                {'error': f'Failed to fetch addresses: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    elif request.method == 'POST':
        try:
            required_fields = ['address', 'city', 'state', 'pincode']
            missing_fields = [
                field for field in required_fields if not request.data.get(field)]

            if missing_fields:
                return Response(
                    {'error': f'Missing required fields: {", ".join(missing_fields)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            address_data = {
                'full_name': request.data.get('full_name', ''),
                'phone': request.data.get('phone', ''),
                'address': request.data.get('address', ''),
                'city': request.data.get('city', ''),
                'state': request.data.get('state', ''),
                'pincode': request.data.get('pincode', ''),
                'is_default': request.data.get('is_default', False)
            }

            user_address_count = UserAddress.objects.filter(user=user).count()
            is_default = address_data['is_default']

            if user_address_count == 0:
                is_default = True
            elif is_default:
                UserAddress.objects.filter(user=user).update(is_default=False)

            address = UserAddress.objects.create(
                user=user,
                full_name=address_data['full_name'],
                phone=address_data['phone'],
                address=address_data['address'],
                city=address_data['city'],
                state=address_data['state'],
                pincode=address_data['pincode'],
                is_default=is_default
            )

            response_serializer = UserAddressSerializer(address)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print("POST Address Error:", str(e))
            return Response(
                {'error': f'Failed to save address: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def user_address_detail(request, address_id):
    user = request.user

    try:
        address = UserAddress.objects.get(id=address_id, user=user)
    except UserAddress.DoesNotExist:
        return Response({'error': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        try:
            if 'full_name' in request.data:
                address.full_name = request.data['full_name']
            if 'phone' in request.data:
                address.phone = request.data['phone']
            if 'address' in request.data:
                address.address = request.data['address']
            if 'city' in request.data:
                address.city = request.data['city']
            if 'state' in request.data:
                address.state = request.data['state']
            if 'pincode' in request.data:
                address.pincode = request.data['pincode']
            if 'is_default' in request.data and request.data['is_default']:
                UserAddress.objects.filter(user=user).exclude(
                    id=address_id).update(is_default=False)
                address.is_default = True

            address.save()
            serializer = UserAddressSerializer(address)
            return Response(serializer.data)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'DELETE':
        try:
            address_count = UserAddress.objects.filter(user=user).count()
            if address_count <= 1:
                return Response(
                    {'error': 'Cannot delete the only address. Add another address first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            address.delete()
            return Response({'message': 'Address deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def set_default_address(request, address_id):
    user = request.user

    try:
        address = UserAddress.objects.get(id=address_id, user=user)
    except UserAddress.DoesNotExist:
        return Response({'error': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        UserAddress.objects.filter(user=user).update(is_default=False)
        address.is_default = True
        address.save()
        return Response({'message': 'Default address updated successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# DELETE ACCOUNT
# =========================
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    user = request.user
    try:
        Cart.objects.filter(user=user).delete()
    except:
        pass
    try:
        Wishlist.objects.filter(user=user).delete()
    except:
        pass
    user.delete()
    return Response({'message': 'Account deleted successfully'}, status=status.HTTP_200_OK)


# =========================
# ADMIN - GET ALL USERS (Simple version without Order count)
# =========================
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_users(request):
    """Admin: Get all users"""
    try:
        users = User.objects.all().order_by('-date_joined')
        
        data = []
        for user in users:
            # Get order count safely
            order_count = 0
            if ORDER_MODEL_AVAILABLE:
                try:
                    order_count = Order.objects.filter(user=user).count()
                except:
                    order_count = 0
            
            data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "date_joined": user.date_joined,
                "last_login": user.last_login,
                "order_count": order_count,
            })
        
        return Response(data, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"Error in admin_users: {e}")
        traceback.print_exc()
        return Response(
            {'error': str(e), 'success': False},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =========================
# ADMIN - BLOCK / UNBLOCK USER
# =========================
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def block_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        return Response({
            "success": True,
            "message": "User status updated",
            "id": user.id,
            "is_active": user.is_active
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found", "success": False},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e), "success": False},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =========================
# ADMIN - GET/UPDATE SINGLE USER
# =========================
@api_view(['GET', 'PATCH', 'PUT'])
@permission_classes([IsAdminUser])
def admin_user_detail(request, user_id):
    """Admin: Get or update a single user"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found", "success": False},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        # Get order count safely
        order_count = 0
        if ORDER_MODEL_AVAILABLE:
            try:
                order_count = Order.objects.filter(user=user).count()
            except:
                order_count = 0
                
        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "date_joined": user.date_joined,
            "last_login": user.last_login,
            "order_count": order_count,
        }
        return Response(data, status=status.HTTP_200_OK)

    elif request.method in ['PATCH', 'PUT']:
        try:
            if 'is_active' in request.data:
                user.is_active = request.data['is_active']
            if 'is_staff' in request.data:
                user.is_staff = request.data['is_staff']
            if 'first_name' in request.data:
                user.first_name = request.data['first_name']
            if 'last_name' in request.data:
                user.last_name = request.data['last_name']
            if 'email' in request.data:
                user.email = request.data['email']

            user.save()

            return Response({
                "success": True,
                "message": "User updated successfully",
                "id": user.id,
                "is_active": user.is_active,
                "is_staff": user.is_staff
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e), "success": False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """Admin login endpoint"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if user and (user.is_superuser or user.is_staff):
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff
            }
        }, status=status.HTTP_200_OK)
    elif user:
        return Response(
            {'error': 'Admin privileges required'},
            status=status.HTTP_403_FORBIDDEN
        )
    else:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

@api_view(["POST"])
@permission_classes([AllowAny])
def admin_login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    
    if not username or not password:
        return Response(
            {"error": "Username and password required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if user and (user.is_superuser or user.is_staff):
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff
            }
        })
    return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

