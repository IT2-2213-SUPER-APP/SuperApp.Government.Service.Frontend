from rest_framework_nested import routers

from .views import SubmissionFileViewSet, SubmissionViewSet

# Create a main router
router = routers.SimpleRouter()
# Register the base endpoint for submissions
router.register(r'submissions', SubmissionViewSet, basename='submission')

# Create a nested router for files within submissions
submissions_router = routers.NestedSimpleRouter(router, r'submissions', lookup='submission')
# Register the 'files' endpoint nested under a specific submission
submissions_router.register(r'files', SubmissionFileViewSet, basename='submission-file')

# The final URL patterns are the combination of both routers
urlpatterns = router.urls + submissions_router.urls
