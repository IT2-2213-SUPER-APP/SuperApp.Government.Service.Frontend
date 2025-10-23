from django.urls import path
from .views import home_view

urlpatterns = [
    # The root URL of the site will point to our home_view
    path('', home_view, name='home'),
]
