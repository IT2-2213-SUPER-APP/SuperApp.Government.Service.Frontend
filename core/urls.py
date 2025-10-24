from django.urls import path
from .views import home_view, submission_detail_view_by_slug, upload_view

urlpatterns = [
    path('', home_view, name='home'),
    path('upload/', upload_view, name='upload'),
    path('s/<slug:slug>/', submission_detail_view_by_slug, name='submission_slug_detail'),
]
