from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from safedelete.models import HARD_DELETE
from submissions.models import Submission

@shared_task
def cleanup_soft_deleted():
    """Hard-delete submissions soft-deleted more than 30 days ago."""
    cutoff = timezone.now() - timedelta(days=30)
    qs = Submission.all_objects.filter(deleted__isnull=False, deleted__lt=cutoff)
    count = 0
    for obj in qs:
        obj.delete(force_policy=HARD_DELETE)
        count += 1
    return count
