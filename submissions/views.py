from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from django_ratelimit.decorators import ratelimit
from guardian.shortcuts import assign_perm
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Submission, SubmissionFile, SubmissionVote, submission_vote_stats, Folder, SubmissionMember
from .permissions import IsOwnerOrReadOnly, IsOwnerOrEditor
from .serializers import SubmissionFileSerializer, SubmissionSerializer, FolderSerializer
from django.conf import settings


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
        """
        user = self.request.user
        qs = Submission.objects.all()
        if user.is_authenticated:
            return qs.filter(
                Q(visibility='public') | Q(owner=user) | Q(members__user=user)
            ).distinct()
        return qs.filter(visibility='public', registered_only=False)

    def perform_create(self, serializer):
        """
        Saves the submission with the current user as the owner and assigns
        object-level permissions for changing and deleting the submission.
        """
        submission = serializer.save(owner=self.request.user)
        assign_perm('change_submission', self.request.user, submission)
        assign_perm('delete_submission', self.request.user, submission)

    @ratelimit(
        key='user_or_ip',
        rate=f"1/{getattr(settings,'SUBMISSION_CREATE_COOLDOWN_SECONDS',32)}s",
        method='POST',
        block=True,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @ratelimit(
        key='user',
        rate=f"1/{getattr(settings,'SUBMISSION_EDIT_COOLDOWN_SECONDS',16)}s",
        method=['PUT', 'PATCH'],
        block=True,
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrReadOnly])
    def restore(self, request, pk=None):
        submission = get_object_or_404(Submission.all_objects, pk=pk)
        self.check_object_permissions(request, submission)
        submission.undelete()
        return Response({'status': 'submission restored'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def report(self, request, pk=None):
        submission = self.get_object()
        reason = request.data.get('reason') or 'No reason provided'
        from .models import SubmissionReport
        SubmissionReport.objects.create(submission=submission, reporter=request.user, reason=reason)
        return Response({'message': 'Report submitted.'}, status=status.HTTP_201_CREATED)

    # Votes
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def votes(self, request, pk=None):
        sub = self.get_object()
        return Response(submission_vote_stats(sub))

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upvote(self, request, pk=None):
        sub = self.get_object()
        SubmissionVote.objects.update_or_create(
            submission=sub, user=request.user, defaults={'value': SubmissionVote.UP}
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def downvote(self, request, pk=None):
        sub = self.get_object()
        SubmissionVote.objects.update_or_create(
            submission=sub, user=request.user, defaults={'value': SubmissionVote.DOWN}
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def clear_vote(self, request, pk=None):
        sub = self.get_object()
        SubmissionVote.objects.filter(submission=sub, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Member management (owner-only)
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def members(self, request, pk=None):
        sub = self.get_object()
        if request.user != sub.owner:
            return Response(status=status.HTTP_403_FORBIDDEN)
        data = [
            {"user_id": m.user_id, "username": m.user.username, "role": m.role}
            for m in sub.members.select_related("user")
        ]
        return Response(data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_member(self, request, pk=None):
        sub = self.get_object()
        if request.user != sub.owner:
            return Response(status=status.HTTP_403_FORBIDDEN)
        user_id = request.data.get("user_id")
        role = request.data.get("role")
        from .models import SubmissionMember
        if role not in [SubmissionMember.Role.EDITOR, SubmissionMember.Role.VIEWER]:
            return Response({"detail": "Invalid role"}, status=400)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            target = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=404)
        SubmissionMember.objects.update_or_create(submission=sub, user=target, defaults={"role": role})
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def remove_member(self, request, pk=None):
        sub = self.get_object()
        if request.user != sub.owner:
            return Response(status=status.HTTP_403_FORBIDDEN)
        user_id = request.data.get("user_id")
        from .models import SubmissionMember
        SubmissionMember.objects.filter(submission=sub, user_id=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FolderViewSet(viewsets.ModelViewSet):
    serializer_class = FolderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_submission(self):
        submission_pk = self.kwargs.get('submission_pk')
        return get_object_or_404(Submission, pk=submission_pk)

    def get_queryset(self):
        submission = self.get_submission()
        return Folder.objects.filter(submission=submission, parent__isnull=True).order_by('name')

    def perform_create(self, serializer):
        submission = self.get_submission()
        if not (self.request.user == submission.owner or SubmissionMember.is_editor(self.request.user, submission)):
            self.permission_denied(self.request)
        serializer.save(submission=submission)

    def perform_update(self, serializer):
        submission = self.get_submission()
        if not (self.request.user == submission.owner or SubmissionMember.is_editor(self.request.user, submission)):
            self.permission_denied(self.request)
        instance = serializer.instance
        parent = serializer.validated_data.get('parent', instance.parent)
        if parent and parent.submission_id != submission.id:
            self.permission_denied(self.request, message='Parent folder must belong to this submission.')
        serializer.save()

    def perform_destroy(self, instance):
        submission = self.get_submission()
        if not (self.request.user == submission.owner or SubmissionMember.is_editor(self.request.user, submission)):
            self.permission_denied(self.request)
        instance.delete()


class SubmissionFileViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for uploading, retrieving, and deleting files within a Submission.
    This ViewSet is intended to be used with nested routing, e.g.,
    /api/submissions/{submission_pk}/files/
    """
    serializer_class = SubmissionFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_submission(self):
        submission_pk = self.kwargs.get('submission_pk')
        return get_object_or_404(Submission, pk=submission_pk)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['submission'] = self.get_submission()
        return ctx

    def get_queryset(self):
        """
        Returns only the files associated with the specific submission
        from the URL.
        """
        submission = self.get_submission()
        return SubmissionFile.objects.filter(submission=submission)

    def check_submission_permissions(self, request, submission):
        """
        Allow owner or editor to modify files; others denied.
        """
        from .models import SubmissionMember
        if request.user == submission.owner:
            return
        if SubmissionMember.is_editor(request.user, submission):
            return
        self.permission_denied(
            request,
            message='You do not have permission to modify files for this submission.'
        )

    def perform_create(self, serializer):
        submission = self.get_submission()
        self.check_submission_permissions(self.request, submission)
        folder = serializer.validated_data.get('folder')
        if folder and folder.submission_id != submission.id:
            self.permission_denied(self.request, message='Folder must belong to this submission.')
        serializer.save(submission=submission)

    def perform_destroy(self, instance):
        """
        Ensures the user has permission on the parent submission before deleting a file.
        """
        submission = self.get_submission()
        self.check_submission_permissions(self.request, submission)
        instance.delete()
