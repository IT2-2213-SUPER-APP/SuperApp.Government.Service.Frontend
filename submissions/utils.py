import string
import secrets
from django.conf import settings

ALPHABET = string.ascii_letters + string.digits


def generate_unique_slug(length=None):
    """Generate a unique slug not colliding (case-insensitively) and not reserved."""
    from .models import Submission  # local import to avoid circular dependency

    length = length or getattr(settings, "DEFAULT_SLUG_LENGTH", 8)
    while True:
        candidate = "".join(secrets.choice(ALPHABET) for _ in range(length))
        if candidate.lower() in getattr(settings, "RESERVED_SLUGS", set()):
            continue
        if not Submission.objects.filter(slug__iexact=candidate).exists():
            return candidate
