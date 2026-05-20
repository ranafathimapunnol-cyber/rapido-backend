# products/urls.py
from django.urls import path
from .views import (
    GetCategoriesView,
    GetSubCategoriesView,
    GetProductsView,
    GetProductView,
    GetNewArrivalsView,
    GetFeaturedProductsView,
    GetWishlistView,
    AddWishlistView,
    RemoveWishlistView,
    ToggleWishlistView,
    CheckWishlistView,
    AddProductView,
    AdminProductsView,
    UpdateProductView,
    DeleteProductView,
    SendReportEmailView,
    debug_products_by_category,
)

urlpatterns = [
    # Public endpoints
    path('categories/', GetCategoriesView.as_view(), name='categories'),
    path('subcategories/<int:category_id>/', GetSubCategoriesView.as_view(), name='subcategories'),
    path('', GetProductsView.as_view(), name='products'),
    path('<int:pk>/', GetProductView.as_view(), name='product-detail'),
    path('new-arrivals/', GetNewArrivalsView.as_view(), name='new-arrivals'),
    path('featured/', GetFeaturedProductsView.as_view(), name='featured-products'),
    
    # Wishlist endpoints
    path('wishlist/', GetWishlistView.as_view(), name='wishlist'),
    path('wishlist/add/', AddWishlistView.as_view(), name='add-wishlist'),
    path('wishlist/remove/<int:pk>/', RemoveWishlistView.as_view(), name='remove-wishlist'),
    path('wishlist/toggle/', ToggleWishlistView.as_view(), name='toggle-wishlist'),
    path('wishlist/check/<int:product_id>/', CheckWishlistView.as_view(), name='check-wishlist'),
    
    # Admin endpoints
    path('add/', AddProductView.as_view(), name='add-product'),
    path('admin/all/', AdminProductsView.as_view(), name='admin-products'),
    path('update/<int:pk>/', UpdateProductView.as_view(), name='update-product'),
    path('delete/<int:pk>/', DeleteProductView.as_view(), name='delete-product'),
    
    # Email endpoint
    path('send-report-email/', SendReportEmailView.as_view(), name='send-report-email'),
    
    # Debug endpoint
    
    path('debug/category/<str:category_name>/', debug_products_by_category, name='debug-category'),
]