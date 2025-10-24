import re
from django.core.exceptions import ValidationError
from django.conf import settings

SLUG_ALLOWED_RE = re.compile(r"^[A-Za-z0-9-]{3,32}$")


def validate_reserved_slug(value: str):
    if value and value.lower() in getattr(settings, "RESERVED_SLUGS", set()):
        raise ValidationError("This slug is reserved.")


def validate_custom_slug_format(value: str):
    if value and not SLUG_ALLOWED_RE.match(value):
        raise ValidationError("Slug must be 3-32 chars, alphanumeric or hyphen.")
