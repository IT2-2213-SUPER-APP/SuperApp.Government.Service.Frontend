from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from django_ratelimit.decorators import ratelimit
from guardian.shortcuts import assign_perm
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Submission, SubmissionFile
from .permissions import IsOwnerOrReadOnly
from .serializers import SubmissionFileSerializer, SubmissionSerializer


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing, creating, editing, and deleting Submissions.
    """
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['owner__username', 'visibility']

    def get_queryset(self):
        """
        Dynamically filters the queryset based on user authentication and
        submission visibility.

        - Unauthenticated users can only see 'public' submissions.
        - Authenticated users can see 'public' submissions and their own
          'private' or 'link_only' submissions.
        """
        user = self.request.user
        queryset = Submission.objects.all()

        if user.is_authenticated:
            # Show public submissions OR submissions owned by the current user
            return queryset.filter(Q(visibility='public') | Q(owner=user)).distinct()

        # For anonymous users, only show public submissions
        return queryset.filter(visibility='public')

    def perform_create(self, serializer):
        """
        Saves the submission with the current user as the owner and assigns
        object-level permissions for changing and deleting the submission.
        """
        submission = serializer.save(owner=self.request.user)
        # Assign object-level permissions to the owner
        assign_perm('change_submission', self.request.user, submission)
        assign_perm('delete_submission', self.request.user, submission)

    @method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='POST'), name='create')
    def create(self, request, *args, **kwargs):
        """
        Handles the creation of a new submission, with rate-limiting.
        """
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrReadOnly])
    def restore(self, request, pk=None):
        """
        Restores a soft-deleted submission. Only the owner can perform this action.
        This requires using `all_objects` to find the instance.
        """
        submission = get_object_or_404(Submission.all_objects, pk=pk)
        self.check_object_permissions(request, submission)
        submission.undelete()
        return Response(
            {'status': 'submission restored'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def report(self, request, pk=None):
        """
        Allows an authenticated user to report a submission.
        (This is a placeholder for a more complex reporting system).
        """
        submission = self.get_object()
        # In a real application, you would create a Report model instance
        # or trigger a Celery task to notify administrators.
        print(f"User '{request.user.username}' reported submission '{submission.title}' (ID: {submission.id})")
        return Response(
            {'message': 'Submission has been reported to the administrators.'},
            status=status.HTTP_200_OK
        )


class SubmissionFileViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for uploading, retrieving, and deleting files within a Submission.
    This ViewSet is intended to be used with nested routing, e.g.,
    /api/submissions/{submission_pk}/files/
    """
    serializer_class = SubmissionFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_submission(self):
        """Helper method to get the parent Submission object from the URL."""
        submission_pk = self.kwargs.get('submission_pk')
        return get_object_or_404(Submission, pk=submission_pk)

    def get_queryset(self):
        """
        Returns only the files associated with the specific submission
        from the URL.
        """
        submission = self.get_submission()
        return SubmissionFile.objects.filter(submission=submission)

    def check_submission_permissions(self, request, submission):
        """
        Checks if the request user has 'change_submission' permissions on the
        parent submission object, which is required to add or delete files.
        """
        if not request.user.has_perm('change_submission', submission):
            self.permission_denied(
                request,
                message='You do not have permission to modify files for this submission.'
            )

    def perform_create(self, serializer):
        """
        Associates the uploaded file with the submission specified in the URL.
        """
        submission = self.get_submission()
        self.check_submission_permissions(self.request, submission)
        serializer.save(submission=submission)

    def perform_destroy(self, instance):
        """
        Ensures the user has permission on the parent submission before deleting a file.
        """
        submission = self.get_submission()
        self.check_submission_permissions(self.request, submission)
        instance.delete()
