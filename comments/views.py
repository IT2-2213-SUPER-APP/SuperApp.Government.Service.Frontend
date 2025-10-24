from rest_framework import viewsets, permissions
from django.shortcuts import get_object_or_404
from submissions.models import Submission
from .models import Comment
from .serializers import CommentSerializer
from .permissions import IsAuthorOrReadOnly

class CommentViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and creating comments on a submission.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        """
        This view should return a list of all the comments
        for the submission as determined by the submission_pk portion of the URL.
        We only return top-level comments (those without a parent).
        """
        submission_pk = self.kwargs['submission_pk']
        return Comment.objects.filter(submission_id=submission_pk, parent__isnull=True)

    def perform_create(self, serializer):
        """
        Assign the current user as the author of the comment and associate
        it with the submission from the URL.
        """
        submission = get_object_or_404(Submission, pk=self.kwargs['submission_pk'])
        serializer.save(author=self.request.user, submission=submission)
