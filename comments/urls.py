from rest_framework_nested import routers
from .views import CommentViewSet

# The router is registered in submissions/urls.py, so this file is not
# strictly necessary for this nested approach, but it's good practice
# to keep it for future expansion.
router = routers.SimpleRouter()
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = router.urls
