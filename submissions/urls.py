from rest_framework_nested import routers
from .views import SubmissionFileViewSet, SubmissionViewSet
from comments.views import CommentViewSet

# Create a main router
router = routers.SimpleRouter()
router.register(r'submissions', SubmissionViewSet, basename='submission')

# Create a nested router for files within submissions
submissions_router = routers.NestedSimpleRouter(router, r'submissions', lookup='submission')
submissions_router.register(r'files', SubmissionFileViewSet, basename='submission-files')

# --- UPDATED: Nest comments under submissions ---
submissions_router.register(r'comments', CommentViewSet, basename='submission-comments')

# The final URL patterns are the combination of all routers
urlpatterns = router.urls + submissions_router.urls
