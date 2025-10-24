from django.conf import settings
from django.db import models
from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.core.exceptions import ValidationError
from .validators import validate_reserved_slug, validate_custom_slug_format
from .utils import generate_unique_slug
def default_slug():
    return generate_unique_slug()


class Submission(SafeDeleteModel):
    """
    Represents a submission, which acts as a container for files.
    It includes visibility settings, ownership, and a unique short link for sharing.
    """
    # Use safedelete's policy for soft-deleting related objects.
    _safedelete_policy = SOFT_DELETE_CASCADE

    class Visibility(models.TextChoices):
        PUBLIC = 'public', 'Public'
        PRIVATE = 'private', 'Private'
        LINK_ONLY = 'link_only', 'Link Only'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        db_index=True  # Add index for faster filtering on visibility
    )
    slug = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        default=default_slug,
        validators=[validate_reserved_slug, validate_custom_slug_format],
    )
    registered_only = models.BooleanField(default=False)
    trending_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Show newest submissions first
        constraints = [
            UniqueConstraint(Lower('slug'), name='submission_slug_unique_ci')
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = default_slug()
        # Run field validators (including reserved slug)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'"{self.title}" by {self.owner.username}'


class Folder(models.Model):
    submission = models.ForeignKey(Submission, related_name="folders", on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("submission", "parent", "name"),)
        indexes = [
            models.Index(fields=["submission", "parent", "name"]),
        ]

    def __str__(self):
        return self.path

    @property
    def path(self):
        parts = []
        node = self
        # Build path from root to this node
        while node is not None:
            parts.append(node.name)
            node = node.parent
        return "/".join(reversed(parts))

    def clean(self):
        # prevent cycles
        node = self.parent
        while node is not None:
            if node == self:
                raise ValidationError("Cannot set folder parent to a descendant.")
            node = node.parent


def upload_path(instance, filename):
    # instance is SubmissionFile
    sub_slug = instance.submission.slug
    folder_path = instance.folder.path if getattr(instance, 'folder', None) else ""
    prefix = f"submissions/{sub_slug}/"
    return prefix + (folder_path + "/" if folder_path else "") + filename


class SubmissionFile(models.Model):
    """
    Represents a single file that is part of a Submission.
    """
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='files'
    )
    folder = models.ForeignKey(Folder, null=True, blank=True, related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to=upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        try:
            name = self.file.name.split('/')[-1]
        except (AttributeError, IndexError):
            name = "N/A"
        return f'File "{name}" for submission: {self.submission.title}'


class SubmissionVote(models.Model):
    UP = 1
    DOWN = -1
    VALUE_CHOICES = (
        (UP, "Upvote"),
        (DOWN, "Downvote"),
    )
    submission = models.ForeignKey(Submission, related_name="votes", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="submission_votes", on_delete=models.CASCADE)
    value = models.SmallIntegerField(choices=VALUE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("submission", "user"),)
        indexes = [
            models.Index(fields=["submission", "user"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user} -> {self.submission} ({self.value})"


def submission_vote_stats(submission: Submission):
    qs = submission.votes.all()
    up = qs.filter(value=SubmissionVote.UP).count()
    down = qs.filter(value=SubmissionVote.DOWN).count()
    total = up + down
    percentage = (up / total) if total else None
    if percentage is None:
        stars = None
    else:
        stars = round(5.0 * percentage, 2)
    return {"up": up, "down": down, "percentage": percentage, "stars": stars}


class SubmissionReport(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        DISMISSED = "dismissed", "Dismissed"
        ACTIONED = "actioned", "Actioned"
    submission = models.ForeignKey(Submission, related_name="reports", on_delete=models.CASCADE)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="reports_made", on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report on {self.submission} by {self.reporter} [{self.status}]"


class SubmissionMember(models.Model):
    class Role(models.TextChoices):
        EDITOR = "editor", "Editor"
        VIEWER = "viewer", "Viewer"

    submission = models.ForeignKey(Submission, related_name="members", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="submission_memberships", on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=Role.choices)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("submission", "user"),)
        indexes = [
            models.Index(fields=["submission", "user", "role"]),
        ]

    def __str__(self):
        return f"{self.user} in {self.submission} as {self.role}"

    @staticmethod
    def is_editor(user, submission):
        if not user or not user.is_authenticated:
            return False
        return SubmissionMember.objects.filter(submission=submission, user=user, role=SubmissionMember.Role.EDITOR).exists()

    @staticmethod
    def is_viewer(user, submission):
        if not user or not user.is_authenticated:
            return False
        return SubmissionMember.objects.filter(
            submission=submission, user=user, role__in=[SubmissionMember.Role.EDITOR, SubmissionMember.Role.VIEWER]
        ).exists()
