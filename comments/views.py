from rest_framework import viewsets, permissions
from django.shortcuts import get_object_or_404
from submissions.models import Submission
from .models import Comment
from .serializers import CommentSerializer
from .permissions import IsAuthorOrReadOnly
from django.utils.decorators import method_decorator
from django.conf import settings
from django_ratelimit.decorators import ratelimit

class CommentViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and creating comments on a submission.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    @method_decorator(
        ratelimit(
            key='user_or_ip',
            rate=f"1/{getattr(settings,'COMMENT_COOLDOWN_SECONDS',8)}s",
            method='POST',
            block=True,
        ),
        name='create'
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        """
        This view should return a list of all the comments
        for the submission as determined by the submission_pk portion of the URL.
        We only return top-level comments (those without a parent).
        """
        submission_pk = self.kwargs['submission_pk']
        submission = get_object_or_404(Submission, pk=submission_pk)
        from core.views import can_view_submission
        if not can_view_submission(self.request.user, submission):
            return Comment.objects.none()
        return Comment.objects.filter(submission=submission, parent__isnull=True)

    def perform_create(self, serializer):
        submission = get_object_or_404(Submission, pk=self.kwargs['submission_pk'])
        from core.views import can_view_submission
        if not can_view_submission(self.request.user, submission):
            self.permission_denied(self.request)
        serializer.save(author=self.request.user, submission=submission)
        """
        Assign the current user as the author of the comment and associate
        it with the submission from the URL.
        """
        submission = get_object_or_404(Submission, pk=self.kwargs['submission_pk'])
        serializer.save(author=self.request.user, submission=submission)
