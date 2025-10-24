"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # --- Frontend URL Patterns ---
    # This routes the root URL ('/') and other core pages to the 'core' app.
    path('', include('core.urls')),

    # --- Admin Panel ---
    path('admin/', admin.site.urls),

    # --- API URL Patterns ---
    # UPDATED: Changed prefix to '/api/' to better accommodate nested routes.
    # This will now handle URLs like /api/submissions/ and /api/submissions/{id}/comments/
    path('api/', include('submissions.urls')),

    # All user-related endpoints (register, login, profile) will be under /api/users/
    path('api/users/', include('users.urls')),

    # NEW: Added URL patterns for the private messaging API.
    # This will create endpoints like /api/messages/
    path('api/', include('messaging.urls')),

    # This provides the login/logout views for the browsable DRF API
    path('api-auth/', include('rest_framework.urls')),
]

# This is important for serving user-uploaded files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
