# backend/urls.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from products.views import SendReportEmailView  # ADD THIS IMPORT

from django.views.generic import TemplateView


urlpatterns = [
    path('admin-django/', admin.site.urls),
    
    # ADD THIS LINE - Email endpoint
    path('api/send-report-email/', SendReportEmailView.as_view(), name='send-report-email'),
    path('api/notifications/', include('notifications.urls')),    
    path('api/products/', include('products.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/users/', include('users.urls')),
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
        path('', TemplateView.as_view(template_name='index.html')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
