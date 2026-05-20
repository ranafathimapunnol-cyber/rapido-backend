# cart/urls.py - UPDATED FOR GENERIC VIEWS
from django.urls import path
from .views import (
    GetCartView,
    AddToCartView,
    UpdateCartItemView,
    RemoveCartItemView,
)

urlpatterns = [
    path('', GetCartView.as_view(), name='get-cart'),
    path('add/', AddToCartView.as_view(), name='add-to-cart'),
    path('update/', UpdateCartItemView.as_view(), name='update-cart'),
    path('remove/<int:pk>/', RemoveCartItemView.as_view(), name='remove-item'),
]
