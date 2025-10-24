from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from django.db.models import Count
from .models import Submission, SubmissionVote
import math


def wilson_lower_bound(pos: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 0.0
    phat = 1.0 * pos / n
    return max(
        0.0,
        (phat + z * z / (2 * n) - z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n))
        / (1 + z * z / n),
    )


@shared_task
def recalculate_trending():
    """Recalculate weekly trending scores using Wilson lower bound on last 7 days of votes."""
    now = timezone.now()
    window_start = now - timedelta(days=7)
    for sub in Submission.objects.all():
        votes = SubmissionVote.objects.filter(submission=sub, created_at__gte=window_start)
        up = votes.filter(value=SubmissionVote.UP).count()
        total = votes.count()
        score = wilson_lower_bound(up, total)
        if sub.trending_score != score:
            sub.trending_score = score
            sub.save(update_fields=["trending_score"])
    return True
