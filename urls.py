from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from products.views import SendReportEmailView  # ADD THIS IMPORT

# A simple JSON response for your homepage instead of an HTML template
def api_home(request):
    return JsonResponse({
        "status": "healthy",
        "message": "Welcome to the Rapido API backend",
        "endpoints": {
            "products": "/api/products/",
            "users": "/api/users/",
            "orders": "/api/orders/",
            "cart": "/api/cart/",
            "notifications": "/api/notifications/"
        }
    })

urlpatterns = [
    # Clean API Homepage Root
    path('', api_home, name='api-root'),

    # Admin Panel
    path('admin-django/', admin.site.urls),
    
    # Email endpoint
    path('api/send-report-email/', SendReportEmailView.as_view(), name='send-report-email'),
    
    # App Features
    path('api/notifications/', include('notifications.urls')),    
    path('api/products/', include('products.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/users/', include('users.urls')),
    
    # Authentication
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
]

# Media and Static configurations for local development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)