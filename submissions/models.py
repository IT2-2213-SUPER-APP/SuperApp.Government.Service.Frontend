import shortuuid
from django.conf import settings
from django.db import models
from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE


def generate_short_link():
    """Generates a unique short identifier for the submission URL."""
    return shortuuid.uuid()


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
    short_link = models.CharField(
        max_length=22,
        default=generate_short_link,
        unique=True,
        editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Show newest submissions first

    def __str__(self):
        return f'"{self.title}" by {self.owner.username}'


class SubmissionFile(models.Model):
    """
    Represents a single file that is part of a Submission.
    """
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='files'
    )
    # The upload_to path will be something like 'submissions/user_123/...'
    file = models.FileField(upload_to='submissions/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Get the filename from the file path
        try:
            name = self.file.name.split('/')[-1]
        except (AttributeError, IndexError):
            name = "N/A"
        return f'File "{name}" for submission: {self.submission.title}'
