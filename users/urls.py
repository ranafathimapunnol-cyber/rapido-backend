# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', views.register_user, name='register'),
    path('profile/', views.profile, name='profile'),
    path('me/', views.get_user_profile, name='user_profile'),
    path('admin-login/', views.admin_login, name='admin_login'),
    # Admin
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin/block-user/<int:user_id>/', views.block_user, name='block_user'),
    
    # Addresses
    path('addresses/', views.user_addresses, name='addresses'),
    path('addresses/<int:address_id>/', views.user_address_detail, name='address_detail'),
    path('addresses/<int:address_id>/set-default/', views.set_default_address, name='set_default_address'),
    
    # Account
    path('delete-account/', views.delete_account, name='delete_account'),
]
