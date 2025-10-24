# CONTENTS

CONVERSATION ANSWER HISTORY...

```md
1. yes, python version `3.11.14` is OK to target;
2. let's switch to `postgres` as we will dockerize the project in the future, including the database daemon;
3. yes, it is okay to include `redis` in the project, it will be also running in a separate docker container in the future;
4. for now, stick to the local file storage management;

5. yes, implement features like upvoting/downvoting that will be down as a star-rating on the website based on the up/down ratio percentage, i.e. 0% means zero stars, 100% means five stars;
6. yes, implement this feature with one exception that reports will be delivered exclusively through the admin panel (no email notifying);
7. ability to edit applies both for submission data and files in the submission, i,e, editing submission title, description, ability to change submission visibility, remove files, add new files/folders. note that submission descriptions will support markdown syntax;
8. all submissons will live under `/s/` URLs and have randomly generated alpha-numeric only 8 characters with the exception that admin users will have the ability to set custom URLs regardless of the URL rules excluding that this URL is not already used (i.e. admin cannot use already used URL of another user, regardless of their status);
9. good idea. let's allow users to manage roles in their own submissions, i.e. each submission will be able to have different people with different levels of access and management, example of roles... owner/editor/viewer (if the submission owner blocked another user, that user won't have access to their submissions). also users will be able to choose visibility for guests, i.e. submission option to only show it for regitered users, while hiding it to guests (unregistered users);
10. here's sample of rate-limits... note that rate-limiting will be applied if only the user exceeds the specified threshold (come up with reasonable and non intruisive value). the rate-limits are..
"""
submission creation - 32 seconds;
submission edits - 16 seconds;
comments - 8 seconds;
messaging - 2 seconds.
"""
11. periodic jobs are...
"""
digests/summary - none (do not implement)
soft items cleanup - weekly
old reports and etc - none (keep forever)
recalculations - weekly (on the website will be shown as weekly trending)
"""
12. do not make admin registration available and visible for regular users. regarding user creation for admins, yes - make that admins will also have a profile with matching username, email and password. include validations if such username exists (i.e. users cannot have safe usernames, inlcuding admins because admins are users as well), the website will have a badges system which will let users identify moderators, admins and regular users, as well as banned or silenced members for violations. regarding frontend templates, start wiring login/register UI but before that, fully ensure that all the BACKEND components are 100% working and functioning properly. write unit tests and ensure everything is functional as expected/intended.

```

```md
1. yes, feel free to manage the project's `README.md` file. include the overview, description and overall used technology stack and components, as well as instructions for how to build and run (in the future). outline the project logic and flow including mermaid diagrams showcasing the features of the project. and yes, make the `docs/` directory and let's make detailed documentations written in markdown.

2. yes, let's replace old `flush.sh` with a new, much safer and more interactive one. for `.env` vars, yes, I confirm. also ensure the `.env` contains all the customizable values in the project such as rate-limiting values and other things to prevent magic numbers spanning across the whole project.

3. consider switching to hierarchical model which is robust, scalable and professional solution to avoid potential complications in the future development.

4. ALL OK.

5. `registered_only` boolean is more preferable. implement it as a checkbox in the submission page next to view permissions options.

6. yes, correct, if Alice blocks Bob, Bob won't have access to ALL of Alive's submissions and her profile altogether (i.e. Bob will see a warning on Alice's profile and submission that he's been blocked like in Twitter). as for `Profile.blocked_users` M2M to `User` - OK.

7. ALL OK.

8. ALL OK.

9. ALL OK.

10. containerization will be handled in the future (no need to dockerize project for now)

11. yes, reserve certain words including API related and future possible words to prevent conflicts in the future. like words "s", "admin", "api", "users", etc.
```

# PLAN

```md
Plan accepted: 1. Phase 0 — Create a working branch, pin Python 3.11.14, install deps
Run these commands to prepare the environment. Do not run as root, and do not sudo Poetry commands.

- Create and switch to a working branch
  - git checkout -b feat/backend-foundation-ratelimits-slugs-votes-folders

- Ensure local Python version is 3.11.14 and Poetry uses it
  - pyenv install -s 3.11.14
  - pyenv local 3.11.14
  - poetry env use 3.11.14
  - poetry install

- Add/upgrade dependencies (Markdown, sanitization, Celery beat, test utilities)
  - poetry add markdown==3.7 bleach==6.2.0
  - poetry add django-celery-beat@^2.8.1 --group=main
  - poetry add pytest pytest-django pytest-cov model-bakery --group=dev

- Verify your virtualenv is active
  - poetry shell
2. Phase 1 — Introduce .env, switch DB to Postgres, configure Redis/Celery, centralize rates/constants
1) Add .env with all tunables (example content)

Create a new file at project root named .env with this content (adjust credentials):

ENV=dev
DEBUG=True
SECRET_KEY=change-me-in-prod

# Django allowed hosts (comma separated)
ALLOWED_HOSTS=127.0.0.1,localhost

# Postgres
POSTGRES_DB=file_forum
POSTGRES_USER=file_forum_user
POSTGRES_PASSWORD=file_forum_pass
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

# Redis (Celery broker and result backend)
REDIS_URL=redis://127.0.0.1:6379/0

# Rate limits (seconds)
SUBMISSION_CREATE_COOLDOWN_SECONDS=32
SUBMISSION_EDIT_COOLDOWN_SECONDS=16
COMMENT_COOLDOWN_SECONDS=8
MESSAGE_COOLDOWN_SECONDS=2

# Short slug length and reserved words (comma separated)
DEFAULT_SLUG_LENGTH=8
RESERVED_SLUGS=s,admin,api,users,submissions,comments,messages,static,media,login,logout,register,profile,docs,help,terms,privacy

# Markdown settings
MARKDOWN_ALLOWED_TAGS=p,a,ul,ol,li,em,strong,code,pre,blockquote,hr,br,h1,h2,h3,h4,h5,h6
MARKDOWN_ALLOWED_ATTRS=a:href,a:title

# File storage (local)
MEDIA_ROOT=.media
MEDIA_URL=/media/

2) Prepare Postgres locally (Linux examples)

- Install Postgres if needed
  - sudo apt-get update
  - sudo apt-get install -y postgresql postgresql-contrib

- Create DB user and database (adapt to your .env values)
  - sudo -u postgres psql -c "CREATE USER file_forum_user WITH PASSWORD 'file_forum_pass';"
  - sudo -u postgres psql -c "CREATE DATABASE file_forum OWNER file_forum_user;"
  - sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE file_forum TO file_forum_user;"

3) Install Redis locally (for Celery broker/result)
- sudo apt-get install -y redis-server
- sudo systemctl enable redis-server
- sudo systemctl start redis-server
- redis-cli ping  # should return PONG

4) Edit config/settings.py to use python-decouple, Postgres, Redis, Celery, and centralized constants

Apply this patch:

--- a/config/settings.py
+++ b/config/settings.py
@@ -1,22 +1,39 @@
 """
 Django settings for config project.
 """

-from pathlib import Path
+from pathlib import Path
 from datetime import timedelta
+from decouple import config, Csv

 BASE_DIR = Path(__file__).resolve().parent.parent

-SECRET_KEY = "django-insecure-5di%7s5mfz07%)kz==u=l34mq68$)8$(ijr#%c61idic^-avnf"
-DEBUG = True
-ALLOWED_HOSTS = []
+SECRET_KEY = config("SECRET_KEY", default="insecure-change-me")
+DEBUG = config("DEBUG", default=True, cast=bool)
+ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())
+ENV = config("ENV", default="dev")

 INSTALLED_APPS = [
     "django.contrib.admin",
     "django.contrib.auth",
     "django.contrib.contenttypes",
     "django.contrib.sessions",
     "django.contrib.messages",
     "django.contrib.staticfiles",

     # --- Third-Party Apps ---
     'rest_framework',
     'rest_framework_simplejwt',
     'corsheaders',
     'guardian',
     'safedelete',
     'django_filters',
+    'django_celery_beat',

     # --- Your Local Apps ---
     'users',
     'submissions',
     'comments',
     'messaging',

     'core'
 ]
@@ -53,11 +70,23 @@
 WSGI_APPLICATION = "config.wsgi.application"

-# SQLite (old)
-DATABASES = {
-    "default": {
-        "ENGINE": "django.db.backends.sqlite3",
-        "NAME": BASE_DIR / "db.sqlite3",
-    }
-}
+# Postgres (env-driven)
+DATABASES = {
+    "default": {
+        "ENGINE": "django.db.backends.postgresql",
+        "NAME": config("POSTGRES_DB", default="file_forum"),
+        "USER": config("POSTGRES_USER", default="file_forum_user"),
+        "PASSWORD": config("POSTGRES_PASSWORD", default="file_forum_pass"),
+        "HOST": config("POSTGRES_HOST", default="127.0.0.1"),
+        "PORT": config("POSTGRES_PORT", default=5432, cast=int),
+        "CONN_MAX_AGE": 60,
+    }
+}

@@ -114,6 +143,61 @@
 SIMPLE_JWT = {
     "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
     "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
@@ -147,3 +231,74 @@
     "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
 }
+
+# Media
+MEDIA_URL = config("MEDIA_URL", default="/media/")
+MEDIA_ROOT = config("MEDIA_ROOT", default=str(BASE_DIR / "media"))
+
+# Local file storage retained. S3 may be added later using django-storages.
+
+# Short links / slug settings
+DEFAULT_SLUG_LENGTH = config("DEFAULT_SLUG_LENGTH", default=8, cast=int)
+RESERVED_SLUGS = set(config("RESERVED_SLUGS", default="s,admin,api,users,submissions,comments,messages,static,media,login,logout,register,profile,docs,help,terms,privacy", cast=Csv()))
+
+# Rate Limits (cooldowns)
+SUBMISSION_CREATE_COOLDOWN_SECONDS = config("SUBMISSION_CREATE_COOLDOWN_SECONDS", default=32, cast=int)
+SUBMISSION_EDIT_COOLDOWN_SECONDS = config("SUBMISSION_EDIT_COOLDOWN_SECONDS", default=16, cast=int)
+COMMENT_COOLDOWN_SECONDS = config("COMMENT_COOLDOWN_SECONDS", default=8, cast=int)
+MESSAGE_COOLDOWN_SECONDS = config("MESSAGE_COOLDOWN_SECONDS", default=2, cast=int)
+
+# Markdown sanitization
+MARKDOWN_ALLOWED_TAGS = set(config("MARKDOWN_ALLOWED_TAGS", default="p,a,ul,ol,li,em,strong,code,pre,blockquote,hr,br,h1,h2,h3,h4,h5,h6", cast=Csv()))
+MARKDOWN_ALLOWED_ATTRS = {
+    "a": set(config("MARKDOWN_ALLOWED_ATTRS", default="a:href,a:title", cast=Csv()))
+}
+
+# Celery/Redis
+CELERY_BROKER_URL = config("REDIS_URL", default="redis://127.0.0.1:6379/0")
+CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://127.0.0.1:6379/0")
+CELERY_TASK_ALWAYS_EAGER = False
+CELERY_TIMEZONE = "UTC"
+
+from celery.schedules import crontab
+CELERY_BEAT_SCHEDULE = {
+    "weekly_soft_delete_cleanup": {
+        "task": "core.tasks.cleanup_soft_deleted",
+        "schedule": crontab(minute=0, hour=0, day_of_week="sun"),
+    },
+    "weekly_recalc_trending": {
+        "task": "submissions.tasks.recalculate_trending",
+        "schedule": crontab(minute=5, hour=0, day_of_week="sun"),
+    },
+}

2) Ensure Celery app is exported (config/__init__.py)

Replace contents with:

from .celery import app as celery_app
__all__ = ["celery_app"]

3) Verify config/celery.py remains as loader (already present)

No change needed unless missing.

4) Install and apply migrations to validate new settings
- poetry run python manage.py makemigrations
- poetry run python manage.py migrate

5) Smoke-run server to validate Postgres connection
- poetry run python manage.py runserver

You should see no DB errors. Stop the server after the check.

Acceptance for Phase 1:
- Django boots using Postgres per .env.
- Redis reachable at REDIS_URL.
- django_celery_beat is in INSTALLED_APPS and migrations applied.
- Settings expose rate limits and reserved slugs via env.
3. Phase 2 — Fix known bug: messaging/permissions.py and add messaging rate-limit
1) Replace incorrect messaging/permissions.py file

Create/replace messaging/permissions.py with:

from rest_framework import permissions

class IsSenderOrRecipient(permissions.BasePermission):
    """
    Allow access only to sender or recipient of the Message object.
    For create: any authenticated user can create (sender becomes request.user).
    """
    def has_permission(self, request, view):
        # Allow listing/creating for authenticated users; queryset is filtered in view
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user == obj.sender or request.user == obj.recipient

2) Ensure views import this (messaging/views.py already references IsSenderOrRecipient). Add rate-limiting to create.

Patch messaging/views.py:

--- a/messaging/views.py
+++ b/messaging/views.py
@@ -1,8 +1,16 @@
-from django.db.models import Q
+from django.db.models import Q
 from rest_framework import viewsets, permissions
 from .models import Message
 from .serializers import MessageSerializer
 from .permissions import IsSenderOrRecipient
+from django.utils.decorators import method_decorator
+from django.conf import settings
+from django_ratelimit.decorators import ratelimit

 class MessageViewSet(viewsets.ModelViewSet):
@@ -12,6 +20,12 @@
     serializer_class = MessageSerializer
     permission_classes = [permissions.IsAuthenticated, IsSenderOrRecipient]

+    # Apply per-user cooldown on sending messages
+    @method_decorator(
+        ratelimit(key='user_or_ip', rate=f"1/{getattr(settings, 'MESSAGE_COOLDOWN_SECONDS', 2)}s", method="POST", block=True),
+        name='create',
+    )
+    def dispatch(self, *args, **kwargs):  # type: ignore[override]
+        return super().dispatch(*args, **kwargs)
+
     def get_queryset(self):
         """
         This view should return a list of all messages
         sent to or from the currently authenticated user.
         """
         user = self.request.user
         return Message.objects.filter(Q(sender=user) | Q(recipient=user))

     def perform_create(self, serializer):
         """
         Set the current user as the sender of the message.
         """
         serializer.save(sender=self.request.user)

3) Add a quick unit test first for permission behavior

Create tests/messaging/test_permissions.py:

import pytest
from django.urls import reverse
from model_bakery import baker

@pytest.mark.django_db
def test_only_sender_or_recipient_can_view_message(api_client):
    sender = baker.make("users.User")
    recipient = baker.make("users.User")
    other = baker.make("users.User")
    msg = baker.make("messaging.Message", sender=sender, recipient=recipient)

    api_client.force_authenticate(user=sender)
    url = reverse("message-detail", args=[msg.id])
    assert api_client.get(url).status_code == 200

    api_client.force_authenticate(user=recipient)
    assert api_client.get(url).status_code == 200

    api_client.force_authenticate(user=other)
    assert api_client.get(url).status_code in (403, 404)

Note: Ensure a pytest fixture api_client is available or use DRF APIClient directly in test.

4) Run tests
- poetry run pytest -q

Acceptance for Phase 2:
- permissions import no longer breaks.
- messages create/list works.
- rate-limit applies to POST create (429 on exceeding).
- tests pass for IsSenderOrRecipient.
4. Phase 3 — Test-first: slugs under /s/&lt;slug&gt;, reserved words, registered_only on submissions
1) Add tests for slug behavior and visibility

Create submissions/tests/test_slugs_and_visibility.py:

import pytest
from django.urls import reverse
from model_bakery import baker
from submissions.models import Submission

@pytest.mark.django_db
def test_submission_has_8_char_slug_by_default():
    sub = baker.make(Submission, slug=None)
    assert sub.slug
    assert len(sub.slug) == 8
    assert sub.slug.isalnum()

@pytest.mark.django_db
def test_reserved_slug_is_rejected(django_user_model):
    owner = baker.make(django_user_model)
    with pytest.raises(Exception):
        Submission.objects.create(title="X", owner=owner, visibility="public", slug="admin")

@pytest.mark.django_db
def test_registered_only_blocks_anonymous(client, django_user_model):
    owner = baker.make(django_user_model)
    sub = baker.make(Submission, owner=owner, visibility="public", registered_only=True)
    url = reverse("submission_slug_detail", kwargs={"slug": sub.slug})
    resp = client.get(url)
    assert resp.status_code in (302, 403, 401)  # should not render content to guests

@pytest.mark.django_db
def test_slug_route_serves_detail_for_public_authenticated(authenticated_client, django_user_model):
    owner = authenticated_client.user
    sub = baker.make(Submission, owner=owner, visibility="public", registered_only=False)
    url = reverse("submission_slug_detail", kwargs={"slug": sub.slug})
    resp = authenticated_client.get(url)
    assert resp.status_code == 200
    assert sub.title.encode() in resp.content

2) Implement slug field, generator, reserved validator, registered_only

Create submissions/validators.py:

import re
from django.core.exceptions import ValidationError
from django.conf import settings

SLUG_ALLOWED_RE = re.compile(r"^[A-Za-z0-9-]{3,32}$")

def validate_reserved_slug(value: str):
    if value and value.lower() in getattr(settings, "RESERVED_SLUGS", set()):
        raise ValidationError("This slug is reserved.")

def validate_custom_slug_format(value: str):
    if not SLUG_ALLOWED_RE.match(value):
        raise ValidationError("Slug must be 3-32 chars, alphanumeric or hyphen.")

Create submissions/utils.py:

import string, secrets
from django.conf import settings
from django.db.models.functions import Lower
from submissions.models import Submission

ALPHABET = string.ascii_letters + string.digits

def generate_unique_slug(length=None):
    length = length or getattr(settings, "DEFAULT_SLUG_LENGTH", 8)
    while True:
        candidate = "".join(secrets.choice(ALPHABET) for _ in range(length))
        if not Submission.objects.filter(slug__iexact=candidate).exists():
            return candidate

Patch submissions/models.py:

--- a/submissions/models.py
+++ b/submissions/models.py
@@ -1,16 +1,34 @@
-import shortuuid
 from django.conf import settings
 from django.db import models
 from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE
+from django.db.models import UniqueConstraint
+from django.db.models.functions import Lower
+from django.core.validators import RegexValidator
+from django.utils import timezone
+from .validators import validate_reserved_slug, validate_custom_slug_format
+from .utils import generate_unique_slug

-def generate_short_link():
-    """Generates a unique short identifier for the submission URL."""
-    return shortuuid.uuid()
+def default_slug():
+    return generate_unique_slug()

 class Submission(SafeDeleteModel):
@@ -24,21 +42,31 @@
     )
     visibility = models.CharField(
         max_length=10,
         choices=Visibility.choices,
         default=Visibility.PUBLIC,
         db_index=True
     )
-    short_link = models.CharField(
-        max_length=22,
-        default=generate_short_link,
-        unique=True,
-        editable=False
-    )
+    # Short link replaced by slug:
+    slug = models.CharField(
+        max_length=32,
+        unique=True,
+        db_index=True,
+        default=default_slug,
+        validators=[validate_reserved_slug, validate_custom_slug_format],
+    )
+    registered_only = models.BooleanField(default=False)
+    trending_score = models.FloatField(default=0.0)
     created_at = models.DateTimeField(auto_now_add=True)
     updated_at = models.DateTimeField(auto_now=True)

     class Meta:
-        ordering = ['-created_at']
+        ordering = ['-created_at']
+        constraints = [
+            UniqueConstraint(
+                Lower('slug'),
+                name='submission_slug_unique_ci'
+            )
+        ]

     def __str__(self):
         return f'"{self.title}" by {self.owner.username}'
@@ -47,6 +75,8 @@
 class SubmissionFile(models.Model):
     submission = models.ForeignKey(
         Submission,
         on_delete=models.CASCADE,
         related_name='files'
     )
     file = models.FileField(upload_to='submissions/')
     uploaded_at = models.DateTimeField(auto_now_add=True)

     def __str__(self):
         try:
             name = self.file.name.split('/')[-1]
         except (AttributeError, IndexError):
             name = "N/A"
         return f'File "{name}" for submission: {self.submission.title}'

3) Update admin to show/edit slug only for superuser; add registered_only

Patch submissions/admin.py:

--- a/submissions/admin.py
+++ b/submissions/admin.py
@@ -1,7 +1,9 @@
 from django.contrib import admin
 from safedelete.admin import SafeDeleteAdmin, highlight_deleted
-from .models import Submission, SubmissionFile
+from .models import Submission, SubmissionFile

 class SubmissionFileInline(admin.TabularInline):
@@ -18,20 +20,35 @@

 @admin.register(Submission)
 class SubmissionAdmin(SafeDeleteAdmin):
@@ -22,17 +39,34 @@
     list_display = (
         highlight_deleted,
         'title',
         'owner',
         'visibility',
-        'short_link',
+        'slug',
+        'registered_only',
         'created_at',
     )
     search_fields = ('title', 'owner__username')
-    list_filter = ('visibility', 'deleted', 'created_at')
-    readonly_fields = ('short_link', 'created_at', 'updated_at')
+    list_filter = ('visibility', 'registered_only', 'deleted', 'created_at')
+    readonly_fields = ('created_at', 'updated_at')
     inlines = [SubmissionFileInline]
+
+    def get_readonly_fields(self, request, obj=None):
+        ro = list(super().get_readonly_fields(request, obj))
+        # Only superusers can edit slug; others see slug as readonly
+        if not request.user.is_superuser:
+            ro.append('slug')
+        return ro

4) Update serializer to expose slug and registered_only, plus description_html rendering

Patch submissions/serializers.py:

--- a/submissions/serializers.py
+++ b/submissions/serializers.py
@@ -1,5 +1,8 @@
 from rest_framework import serializers
+import markdown as md
+import bleach
+from django.conf import settings

 from .models import Submission, SubmissionFile
@@ -44,23 +47,45 @@
 class SubmissionSerializer(serializers.ModelSerializer):
     owner = serializers.ReadOnlyField(source='owner.username')
     files = SubmissionFileSerializer(many=True, read_only=True)
+    description_html = serializers.SerializerMethodField()

     class Meta:
         model = Submission
         fields = [
             'id',
             'title',
             'description',
+            'description_html',
             'owner',
             'visibility',
-            'short_link',
+            'slug',
+            'registered_only',
             'files',
             'created_at',
             'updated_at',
         ]
         read_only_fields = [
-            'short_link',
+            'slug',
             'created_at',
             'updated_at',
         ]

+    def get_description_html(self, obj):
+        raw = obj.description or ""
+        html = md.markdown(raw, extensions=["extra"])
+        allowed_tags = getattr(settings, "MARKDOWN_ALLOWED_TAGS", {"p","a","em","strong"})
+        allowed_attrs = getattr(settings, "MARKDOWN_ALLOWED_ATTRS", {"a": {"href","title"}})
+        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)
+
     def create(self, validated_data):
         return Submission.objects.create(**validated_data)

5) Add /s/<slug>/ route and enforce registered_only in view

Patch core/urls.py:

--- a/core/urls.py
+++ b/core/urls.py
@@ -1,8 +1,9 @@
 from django.urls import path
-from .views import home_view, submission_detail_view, upload_view
+from .views import home_view, submission_detail_view_by_slug, upload_view

 urlpatterns = [
     path('', home_view, name='home'),
     path('upload/', upload_view, name='upload'),
-    path('submission/<int:submission_id>/', submission_detail_view, name='submission_detail'),
+    path('s/<slug:slug>/', submission_detail_view_by_slug, name='submission_slug_detail'),
 ]

Patch core/views.py:

--- a/core/views.py
+++ b/core/views.py
@@ -1,31 +1,58 @@
-from django.shortcuts import render, get_object_or_404
+from django.shortcuts import render, get_object_or_404
+from django.http import HttpResponseForbidden
 from submissions.models import Submission
+from users.models import Profile

 def home_view(request):
     public_submissions = Submission.objects.filter(visibility='public').order_by('-created_at')
     context = {
         'submissions': public_submissions
     }
     return render(request, 'home.html', context)

-def submission_detail_view(request, submission_id):
-    """
-    Renders the detail page for a single submission, including its files and comments.
-    """
-    submission = get_object_or_404(
-        Submission.objects.prefetch_related('files', 'comments__replies'),
-        pk=submission_id
-    )
-    # Basic authorization: check if user can view it
-    can_view = submission.visibility == 'public' or submission.owner == request.user
-    if not can_view and submission.visibility != 'link_only': # link_only logic can be expanded
-        return render(request, 'home.html', {'error': 'You do not have permission to view this.'})
+def is_blocked(owner, user):
+    if not user.is_authenticated:
+        return False
+    try:
+        owner_profile = owner.profile
+    except Profile.DoesNotExist:
+        return False
+    return owner_profile.blocked_users.filter(id=user.id).exists()
+
+def can_view_submission(user, submission: Submission):
+    if is_blocked(submission.owner, user):
+        return False
+    if submission.visibility == Submission.Visibility.PUBLIC:
+        if submission.registered_only and not user.is_authenticated:
+            return False
+        return True
+    if user.is_authenticated and user == submission.owner:
+        return True
+    # Editors/viewers can also view (API enforces object roles; template view is lenient)
+    return False

-    context = {
-        'submission': submission
-    }
-    return render(request, 'submission_detail.html', context)
+def submission_detail_view_by_slug(request, slug):
+    submission = get_object_or_404(
+        Submission.objects.prefetch_related('files', 'comments__replies'),
+        slug__iexact=slug
+    )
+    if not can_view_submission(request.user, submission):
+        if request.user.is_authenticated and is_blocked(submission.owner, request.user):
+            return HttpResponseForbidden("You are blocked by this user.")
+        return HttpResponseForbidden("You do not have permission to view this.")
+    return render(request, 'submission_detail.html', {'submission': submission})

 def upload_view(request):
     return render(request, 'upload.html')

Update templates to link by slug:

Patch templates/home.html:

--- a/templates/home.html
+++ b/templates/home.html
@@ -23,14 +23,14 @@
                 <div class="submission-details">
-                    <h3 class="submission-title"><a href="{% url 'submission_detail' submission.id %}">{{ submission.title }}</a></h3>
+                    <h3 class="submission-title"><a href="{% url 'submission_slug_detail' submission.slug %}">{{ submission.title }}</a></h3>
@@ -31,7 +31,7 @@
                     </p>
                     <p class="submission-description">{{ submission.description|truncatewords:30 }}</p>
                     <div class="submission-actions">
-                        <a href="{% url 'submission_detail' submission.id %}">{{ submission.files.count }} File(s)</a> |
-                        <a href="{% url 'submission_detail' submission.id %}#comments">Comments</a> |
+                        <a href="{% url 'submission_slug_detail' submission.slug %}">{{ submission.files.count }} File(s)</a> |
+                        <a href="{% url 'submission_slug_detail' submission.slug %}#comments">Comments</a> |
                         <a href="#">Share</a> |
                         <a href="#">Report</a>
                     </div>

6) Create and run migrations

- poetry run python manage.py makemigrations submissions core
- poetry run python manage.py migrate

7) Adjust README badges later; proceed with next phases.

Acceptance for Phase 3:
- /s/<slug> route serves submissions.
- Slugs are 8-char alphanumeric by default; admin can edit in admin (only if superuser).
- Reserved words rejected.
- registered_only blocks guests.
- Tests added and passing.
5. Phase 4 — Test-first: votes model, endpoints, star rating mapping
1) Add tests

Create submissions/tests/test_votes_and_rating.py:

import pytest
from model_bakery import baker
from django.urls import reverse
from submissions.models import Submission

@pytest.mark.django_db
def test_upvote_downvote_clear(api_client, django_user_model):
    user = baker.make(django_user_model)
    owner = baker.make(django_user_model)
    sub = baker.make(Submission, owner=owner, visibility="public")
    api_client.force_authenticate(user=user)

    url_up = reverse("submission-upvote", args=[sub.id])
    url_down = reverse("submission-downvote", args=[sub.id])
    url_clear = reverse("submission-clear-vote", args=[sub.id])
    url_stats = reverse("submission-votes", args=[sub.id])

    r = api_client.post(url_up)
    assert r.status_code in (200, 204)
    stats = api_client.get(url_stats).json()
    assert stats["up"] == 1
    assert stats["down"] == 0
    assert 0 <= stats["stars"] <= 5

    r = api_client.post(url_down)
    assert r.status_code in (200, 204)
    stats = api_client.get(url_stats).json()
    assert stats["up"] == 0
    assert stats["down"] == 1

    r = api_client.post(url_clear)
    assert r.status_code in (200, 204)
    stats = api_client.get(url_stats).json()
    assert stats["up"] == 0 and stats["down"] == 0

2) Implement model and endpoints

Patch submissions/models.py to add vote model:

--- a/submissions/models.py
+++ b/submissions/models.py
@@ -1,6 +1,7 @@
 from django.conf import settings
 from django.db import models
 from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE
+from django.utils import timezone
@@ -86,3 +87,37 @@
         return f'File "{name}" for submission: {self.submission.title}'
+
+class SubmissionVote(models.Model):
+    UP = 1
+    DOWN = -1
+    VALUE_CHOICES = (
+        (UP, "Upvote"),
+        (DOWN, "Downvote"),
+    )
+    submission = models.ForeignKey(Submission, related_name="votes", on_delete=models.CASCADE)
+    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submission_votes")
+    value = models.SmallIntegerField(choices=VALUE_CHOICES)
+    created_at = models.DateTimeField(auto_now_add=True)
+
+    class Meta:
+        unique_together = (("submission", "user"),)
+        indexes = [
+            models.Index(fields=["submission", "user"]),
+            models.Index(fields=["created_at"]),
+        ]
+
+    def __str__(self):
+        return f"{self.user} -> {self.submission} ({self.value})"
+
+def submission_vote_stats(submission: Submission):
+    qs = submission.votes.all()
+    up = qs.filter(value=SubmissionVote.UP).count()
+    down = qs.filter(value=SubmissionVote.DOWN).count()
+    total = up + down
+    percentage = (up / total) if total else None
+    if percentage is None:
+        stars = None
+    else:
+        stars = round(5.0 * percentage, 2)
+    return {"up": up, "down": down, "percentage": percentage, "stars": stars}

Patch submissions/views.py to add actions:

--- a/submissions/views.py
+++ b/submissions/views.py
@@ -1,16 +1,23 @@
 from django.db.models import Q
 from django.shortcuts import get_object_or_404
 from django.utils.decorators import method_decorator
 from django_filters.rest_framework import DjangoFilterBackend
 from django_ratelimit.decorators import ratelimit
 from guardian.shortcuts import assign_perm
 from rest_framework import permissions, status, viewsets
 from rest_framework.decorators import action
 from rest_framework.response import Response

-from .models import Submission, SubmissionFile
+from .models import Submission, SubmissionFile, SubmissionVote, submission_vote_stats
 from .permissions import IsOwnerOrReadOnly
 from .serializers import SubmissionFileSerializer, SubmissionSerializer
+from django.conf import settings

 class SubmissionViewSet(viewsets.ModelViewSet):
@@ -37,9 +44,16 @@
         return queryset.filter(visibility='public')

-    @method_decorator(ratelimit(key='user_or_ip', rate='5/m', method='POST'), name='create')
+    @method_decorator(
+        ratelimit(
+            key='user_or_ip',
+            rate=f"1/{getattr(settings,'SUBMISSION_CREATE_COOLDOWN_SECONDS',32)}s",
+            method='POST',
+            block=True
+        ),
+        name='create'
+    )
     def create(self, request, *args, **kwargs):
         return super().create(request, *args, **kwargs)

+    @method_decorator(ratelimit(key='user', rate=f"1/{getattr(settings,'SUBMISSION_EDIT_COOLDOWN_SECONDS',16)}s", method=['PUT','PATCH'], block=True), name='update')
     def update(self, request, *args, **kwargs):
         return super().update(request, *args, **kwargs)

@@ -67,6 +81,46 @@
         print(f"User '{request.user.username}' reported submission '{submission.title}' (ID: {submission.id})")
         return Response(
             {'message': 'Submission has been reported to the administrators.'},
             status=status.HTTP_200_OK
         )
+
+    # Votes API
+    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
+    def votes(self, request, pk=None):
+        sub = self.get_object()
+        return Response(submission_vote_stats(sub))
+
+    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
+    def upvote(self, request, pk=None):
+        sub = self.get_object()
+        obj, created = SubmissionVote.objects.update_or_create(
+            submission=sub, user=request.user, defaults={"value": SubmissionVote.UP}
+        )
+        return Response(status=status.HTTP_204_NO_CONTENT)
+
+    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
+    def downvote(self, request, pk=None):
+        sub = self.get_object()
+        obj, created = SubmissionVote.objects.update_or_create(
+            submission=sub, user=request.user, defaults={"value": SubmissionVote.DOWN}
+        )
+        return Response(status=status.HTTP_204_NO_CONTENT)
+
+    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
+    def clear_vote(self, request, pk=None):
+        sub = self.get_object()
+        SubmissionVote.objects.filter(submission=sub, user=request.user).delete()
+        return Response(status=status.HTTP_204_NO_CONTENT)

Expose rating in serializer:

Patch submissions/serializers.py to add stats:

--- a/submissions/serializers.py
+++ b/submissions/serializers.py
@@ -3,6 +3,7 @@
 import markdown as md
 import bleach
 from django.conf import settings
+from .models import submission_vote_stats

@@ -20,6 +21,7 @@
 class SubmissionSerializer(serializers.ModelSerializer):
     owner = serializers.ReadOnlyField(source='owner.username')
     files = SubmissionFileSerializer(many=True, read_only=True)
     description_html = serializers.SerializerMethodField()
+    rating = serializers.SerializerMethodField()

@@ -35,6 +37,7 @@
             'visibility',
             'slug',
             'registered_only',
+            'rating',
             'files',
             'created_at',
             'updated_at',
         ]
@@ -47,6 +50,10 @@
         return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)

+    def get_rating(self, obj):
+        stats = submission_vote_stats(obj)
+        return stats
+
3) Create migrations and test
- poetry run python manage.py makemigrations submissions
- poetry run python manage.py migrate
- poetry run pytest -q

Acceptance for Phase 4:
- Users can upvote, downvote, clear vote via /api/submissions/{id}/(upvote|downvote|clear_vote)/.
- GET /api/submissions/{id}/votes returns up, down, percentage, and stars (None when no votes).
- Serializer returns rating field.
- Tests pass.
6. Phase 5 — Test-first: submission roles (owner/editor/viewer), blocked users, badges, visibility enforcement
1) Add tests

Create users/tests/test_blocking_and_badges.py:

import pytest
from model_bakery import baker

@pytest.mark.django_db
def test_blocking_prevents_access(django_user_model):
    owner = baker.make(django_user_model)
    blocked = baker.make(django_user_model)
    other = baker.make(django_user_model)
    # Create profile relations
    owner.profile.blocked_users.add(blocked)
    assert owner.profile.blocked_users.filter(id=blocked.id).exists()

    from submissions.models import Submission
    sub = baker.make(Submission, owner=owner, visibility="public", registered_only=False)
    # Simulate blocked logic helper
    from core.views import is_blocked
    assert is_blocked(owner, blocked) is True
    assert is_blocked(owner, other) is False

Create submissions/tests/test_roles_permissions.py:

import pytest
from model_bakery import baker
from django.urls import reverse
from submissions.models import Submission

@pytest.mark.django_db
def test_editor_can_upload_files(api_client, django_user_model):
    owner = baker.make(django_user_model)
    editor = baker.make(django_user_model)
    sub = baker.make(Submission, owner=owner)
    # add editor member
    from submissions.models import SubmissionMember
    SubmissionMember.objects.create(submission=sub, user=editor, role=SubmissionMember.Role.EDITOR)

    api_client.force_authenticate(user=editor)
    url = reverse("submission-files-list", kwargs={"submission_pk": sub.id})
    assert api_client.get(url).status_code == 200

2) Implement Profile.blocked_users, badges, and roles

Patch users/models.py:

--- a/users/models.py
+++ b/users/models.py
@@ -1,12 +1,42 @@
 from django.contrib.auth.models import AbstractUser
 from django.db import models
+from django.db.models.signals import post_save
+from django.dispatch import receiver

 class User(AbstractUser):
     email = models.EmailField(unique=True)

 class Profile(models.Model):
     user = models.OneToOneField(User, on_delete=models.CASCADE)
     bio = models.TextField(blank=True)
     avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
+    blocked_users = models.ManyToManyField(User, related_name='blocked_by_profiles', blank=True)
+    is_banned = models.BooleanField(default=False)
+    is_silenced = models.BooleanField(default=False)

     def __str__(self):
         return self.user.username
+
+    @property
+    def badge(self):
+        u = self.user
+        if self.is_banned:
+            return "banned"
+        if self.is_silenced:
+            return "silenced"
+        if u.is_superuser:
+            return "admin"
+        if u.is_staff:
+            return "mod"
+        return "regular"
+
+@receiver(post_save, sender=User)
+def create_profile_for_user(sender, instance, created, **kwargs):
+    if created:
+        Profile.objects.create(user=instance)

Optional: register Profile in admin with blocked_users widget later.

3) Implement SubmissionMember roles and permissions

Patch submissions/models.py to add roles/member:

--- a/submissions/models.py
+++ b/submissions/models.py
@@ -88,6 +88,35 @@
         return f'File "{name}" for submission: {self.submission.title}'

+class SubmissionMember(models.Model):
+    class Role(models.TextChoices):
+        EDITOR = "editor", "Editor"
+        VIEWER = "viewer", "Viewer"
+    submission = models.ForeignKey(Submission, related_name="members", on_delete=models.CASCADE)
+    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="submission_memberships", on_delete=models.CASCADE)
+    role = models.CharField(max_length=10, choices=Role.choices)
+    added_at = models.DateTimeField(auto_now_add=True)
+
+    class Meta:
+        unique_together = (("submission", "user"),)
+
+    def __str__(self):
+        return f"{self.user} in {self.submission} as {self.role}"
+
+    @staticmethod
+    def is_editor(user, submission):
+        return SubmissionMember.objects.filter(submission=submission, user=user, role=SubmissionMember.Role.EDITOR).exists()
+
+    @staticmethod
+    def is_viewer(user, submission):
+        return SubmissionMember.objects.filter(submission=submission, user=user, role__in=[SubmissionMember.Role.EDITOR, SubmissionMember.Role.VIEWER]).exists()

Patch submissions/permissions.py to add role-based permissions:

--- a/submissions/permissions.py
+++ b/submissions/permissions.py
@@ -1,16 +1,55 @@
 from rest_framework import permissions
+from .models import SubmissionMember

 class IsOwnerOrReadOnly(permissions.BasePermission):
     """
     Custom permission to only allow owners of an object to edit it.
     Assumes the model instance has an `owner` attribute.
     """
     def has_object_permission(self, request, view, obj):
         if request.method in permissions.SAFE_METHODS:
             return True
         return obj.owner == request.user
+
+class IsOwnerOrEditor(permissions.BasePermission):
+    """
+    Allow write actions for owner or editors, read for viewers/public.
+    """
+    def has_object_permission(self, request, view, obj):
+        if request.method in permissions.SAFE_METHODS:
+            return True
+        if request.user == obj.owner:
+            return True
+        return SubmissionMember.is_editor(request.user, obj)

Enforce blocking/visibility checks in SubmissionViewSet list/get:

Patch submissions/views.py get_queryset to consider registered_only and blocking:

--- a/submissions/views.py
+++ b/submissions/views.py
@@ -20,17 +20,41 @@
 class SubmissionViewSet(viewsets.ModelViewSet):
@@ -28,14 +52,31 @@
     def get_queryset(self):
-        user = self.request.user
-        queryset = Submission.objects.all()
-
-        if user.is_authenticated:
-            return queryset.filter(Q(visibility='public') | Q(owner=user)).distinct()
-        return queryset.filter(visibility='public')
+        user = self.request.user
+        qs = Submission.objects.all()
+        if user.is_authenticated:
+            # public (respect registered_only) or owned
+            public_qs = qs.filter(visibility='public')
+            if not user.is_authenticated:
+                public_qs = public_qs.filter(registered_only=False)
+            owned_qs = qs.filter(owner=user)
+            return public_qs.union(owned_qs).distinct()
+        else:
+            return qs.filter(visibility='public', registered_only=False)

Add member management endpoints to SubmissionViewSet:

--- a/submissions/views.py
+++ b/submissions/views.py
@@ -1,6 +1,7 @@
 from rest_framework.decorators import action
 from rest_framework.response import Response
+from .models import SubmissionMember

@@ -109,3 +110,44 @@
         return Response(status=status.HTTP_204_NO_CONTENT)
+
+    # Owner-only: manage members
+    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
+    def members(self, request, pk=None):
+        sub = self.get_object()
+        if request.user != sub.owner:
+            return Response(status=status.HTTP_403_FORBIDDEN)
+        data = [{"user_id": m.user_id, "username": m.user.username, "role": m.role} for m in sub.members.select_related("user")]
+        return Response(data)
+
+    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
+    def add_member(self, request, pk=None):
+        sub = self.get_object()
+        if request.user != sub.owner:
+            return Response(status=status.HTTP_403_FORBIDDEN)
+        user_id = request.data.get("user_id")
+        role = request.data.get("role")
+        if role not in [SubmissionMember.Role.EDITOR, SubmissionMember.Role.VIEWER]:
+            return Response({"detail":"Invalid role."}, status=400)
+        from django.contrib.auth import get_user_model
+        User = get_user_model()
+        try:
+            target = User.objects.get(id=user_id)
+        except User.DoesNotExist:
+            return Response({"detail":"User not found"}, status=404)
+        SubmissionMember.objects.update_or_create(submission=sub, user=target, defaults={"role": role})
+        return Response(status=204)
+
+    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
+    def remove_member(self, request, pk=None):
+        sub = self.get_object()
+        if request.user != sub.owner:
+            return Response(status=status.HTTP_403_FORBIDDEN)
+        user_id = request.data.get("user_id")
+        SubmissionMember.objects.filter(submission=sub, user_id=user_id).delete()
+        return Response(status=204)

4) Migrations and tests
- poetry run python manage.py makemigrations users submissions
- poetry run python manage.py migrate
- poetry run pytest -q

Acceptance for Phase 5:
- Profiles include blocked_users, is_banned, is_silenced, and badge property.
- Submission members allow owner to manage editors/viewers via endpoints.
- Editor permission allows file modifications; viewer/readers read-only.
- Visibility and registered_only enforced in queries and views.
- Tests pass.
7. Phase 6 — Test-first: hierarchical folders under submissions and file management
1) Add tests

Create submissions/tests/test_folders_files.py:

import pytest
from model_bakery import baker
from django.urls import reverse

@pytest.mark.django_db
def test_create_list_move_delete_folder(api_client, django_user_model):
    owner = baker.make(django_user_model)
    sub = baker.make("submissions.Submission", owner=owner)
    api_client.force_authenticate(user=owner)

    # create root folder
    url = reverse("submission-folders-list", kwargs={"submission_pk": sub.id})
    r = api_client.post(url, {"name":"docs"})
    assert r.status_code == 201
    folder_id = r.json()["id"]

    # list
    r = api_client.get(url)
    assert any(f["name"]=="docs" for f in r.json())

2) Implement Folder model and endpoints

Patch submissions/models.py:

--- a/submissions/models.py
+++ b/submissions/models.py
@@ -1,6 +1,7 @@
 from django.conf import settings
 from django.db import models
 from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE
+from django.core.exceptions import ValidationError
@@ -38,6 +39,60 @@
     )

+class Folder(models.Model):
+    submission = models.ForeignKey(Submission, related_name="folders", on_delete=models.CASCADE)
+    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.CASCADE)
+    name = models.CharField(max_length=255)
+    created_at = models.DateTimeField(auto_now_add=True)
+
+    class Meta:
+        unique_together = (("submission", "parent", "name"),)
+        indexes = [
+            models.Index(fields=["submission", "parent", "name"]),
+        ]
+
+    def __str__(self):
+        return f"{self.path}"
+
+    @property
+    def path(self):
+        parts = []
+        node = self
+        while node:
+            parts.append(node.name)
+            node = node.parent
+        return "/".join(reversed(parts))
+
+    def clean(self):
+        # prevent cycles
+        node = self.parent
+        while node:
+            if node == self:
+                raise ValidationError("Cannot set folder parent to a descendant.")
+            node = node.parent
+
+def upload_path(instance, filename):
+    # instance is SubmissionFile
+    sub_slug = instance.submission.slug
+    folder_path = instance.folder.path if instance.folder else ""
+    prefix = f"submissions/{sub_slug}/"
+    return prefix + (folder_path + "/" if folder_path else "") + filename
@@ -70,9 +125,11 @@
 class SubmissionFile(models.Model):
     submission = models.ForeignKey(
         Submission,
         on_delete=models.CASCADE,
         related_name='files'
     )
-    file = models.FileField(upload_to='submissions/')
+    folder = models.ForeignKey(Folder, null=True, blank=True, related_name="files", on_delete=models.CASCADE)
+    file = models.FileField(upload_to=upload_path)
     uploaded_at = models.DateTimeField(auto_now_add=True)

Update serializers: add Folder serializer and adapt file serializer

Patch submissions/serializers.py:

--- a/submissions/serializers.py
+++ b/submissions/serializers.py
@@ -1,7 +1,9 @@
 from rest_framework import serializers
 import markdown as md
 import bleach
 from django.conf import settings
+from .models import Folder
@@ -7,6 +9,26 @@
 from .models import Submission, SubmissionFile
@@ -8,6 +30,33 @@
 class SubmissionFileSerializer(serializers.ModelSerializer):
     file_url = serializers.SerializerMethodField()
+    folder_id = serializers.PrimaryKeyRelatedField(
+        queryset=Folder.objects.all(), source="folder", required=False, allow_null=True
+    )

     class Meta:
         model = SubmissionFile
-        fields = ['id','file','file_url','uploaded_at']
+        fields = ['id','file','file_url','uploaded_at','folder_id']
         extra_kwargs = { 'file': {'write_only': True} }
@@ -23,6 +62,20 @@
         return None
+
+class FolderSerializer(serializers.ModelSerializer):
+    parent_id = serializers.PrimaryKeyRelatedField(
+        queryset=Folder.objects.all(), source="parent", required=False, allow_null=True
+    )
+    class Meta:
+        model = Folder
+        fields = ["id","name","parent_id","created_at"]

Add a new viewset for folders and adjust files ViewSet to enforce owner/editor permissions:

Patch submissions/views.py:

--- a/submissions/views.py
+++ b/submissions/views.py
@@ -6,11 +6,13 @@
 from guardian.shortcuts import assign_perm
 from rest_framework import permissions, status, viewsets
 from rest_framework.decorators import action
 from rest_framework.response import Response

-from .models import Submission, SubmissionFile, SubmissionVote, submission_vote_stats
-from .permissions import IsOwnerOrReadOnly
-from .serializers import SubmissionFileSerializer, SubmissionSerializer
+from .models import Submission, SubmissionFile, SubmissionVote, submission_vote_stats, Folder, SubmissionMember
+from .permissions import IsOwnerOrReadOnly, IsOwnerOrEditor
+from .serializers import SubmissionFileSerializer, SubmissionSerializer, FolderSerializer
@@ -121,6 +123,54 @@
         return Response(status=status.HTTP_204_NO_CONTENT)

 class SubmissionFileViewSet(viewsets.ModelViewSet):
     serializer_class = SubmissionFileSerializer
-    permission_classes = [permissions.IsAuthenticated]
+    permission_classes = [permissions.IsAuthenticated]

     def get_submission(self):
         submission_pk = self.kwargs.get('submission_pk')
         return get_object_or_404(Submission, pk=submission_pk)
@@ -134,6 +184,10 @@
     def check_submission_permissions(self, request, submission):
-        if not request.user.has_perm('change_submission', submission):
+        # Owner or editor can modify
+        if request.user == submission.owner:
+            return
+        if SubmissionMember.is_editor(request.user, submission):
+            return
         self.permission_denied(
             request,
             message='You do not have permission to modify files for this submission.'
         )
@@ -154,3 +208,39 @@
         instance.delete()
+
+class FolderViewSet(viewsets.ModelViewSet):
+    serializer_class = FolderSerializer
+    permission_classes = [permissions.IsAuthenticated]
+
+    def get_submission(self):
+        submission_pk = self.kwargs.get('submission_pk')
+        return get_object_or_404(Submission, pk=submission_pk)
+
+    def get_queryset(self):
+        submission = self.get_submission()
+        return Folder.objects.filter(submission=submission, parent__isnull=True).order_by("name")
+
+    def perform_create(self, serializer):
+        submission = self.get_submission()
+        # only owner/editor
+        if not (self.request.user == submission.owner or SubmissionMember.is_editor(self.request.user, submission)):
+            self.permission_denied(self.request)
+        serializer.save(submission=submission)
+
+    def perform_update(self, serializer):
+        submission = self.get_submission()
+        if not (self.request.user == submission.owner or SubmissionMember.is_editor(self.request.user, submission)):
+            self.permission_denied(self.request)
+        serializer.save()
+
+    def perform_destroy(self, instance):
+        submission = self.get_submission()
+        if not (self.request.user == submission.owner or SubmissionMember.is_editor(self.request.user, submission)):
+            self.permission_denied(self.request)
+        instance.delete()

Register nested route for folders:

Patch submissions/urls.py:

--- a/submissions/urls.py
+++ b/submissions/urls.py
@@ -1,10 +1,12 @@
 from rest_framework_nested import routers
-from .views import SubmissionFileViewSet, SubmissionViewSet
+from .views import SubmissionFileViewSet, SubmissionViewSet, FolderViewSet
 from comments.views import CommentViewSet

 router = routers.SimpleRouter()
 router.register(r'submissions', SubmissionViewSet, basename='submission')
 submissions_router = routers.NestedSimpleRouter(router, r'submissions', lookup='submission')
 submissions_router.register(r'files', SubmissionFileViewSet, basename='submission-files')
+submissions_router.register(r'folders', FolderViewSet, basename='submission-folders')
 submissions_router.register(r'comments', CommentViewSet, basename='submission-comments')
 urlpatterns = router.urls + submissions_router.urls

3) Migrations and tests
- poetry run python manage.py makemigrations submissions
- poetry run python manage.py migrate
- poetry run pytest -q

Acceptance for Phase 6:
- Folder CRUD supported under submissions.
- Files can be associated with folders and enforce owner/editor permissions.
- Upload path nests under submissions/<slug>/[folder path].
- Tests pass.
8. Phase 7 — Test-first: Reports model with Admin management only
1) Add tests

Create submissions/tests/test_reports_admin.py:

import pytest
from model_bakery import baker
from django.contrib.admin.sites import AdminSite

@pytest.mark.django_db
def test_report_creation_via_api_and_visible_in_admin(api_client, django_user_model):
    owner = baker.make(django_user_model)
    reporter = baker.make(django_user_model)
    sub = baker.make("submissions.Submission", owner=owner)
    api_client.force_authenticate(user=reporter)
    url = f"/api/submissions/{sub.id}/report/"
    r = api_client.post(url, {"reason": "Inappropriate"})
    assert r.status_code in (200, 201)
    # admin list exists
    from submissions.models import SubmissionReport
    assert SubmissionReport.objects.filter(submission=sub, reporter=reporter).exists()

2) Implement model and admin

Patch submissions/models.py:

--- a/submissions/models.py
+++ b/submissions/models.py
@@ -160,3 +160,24 @@
         instance.delete()
+
+class SubmissionReport(models.Model):
+    class Status(models.TextChoices):
+        OPEN = "open", "Open"
+        DISMISSED = "dismissed", "Dismissed"
+        ACTIONED = "actioned", "Actioned"
+    submission = models.ForeignKey(Submission, related_name="reports", on_delete=models.CASCADE)
+    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="reports_made", on_delete=models.CASCADE)
+    reason = models.TextField()
+    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
+    created_at = models.DateTimeField(auto_now_add=True)
+
+    def __str__(self):
+        return f"Report on {self.submission} by {self.reporter} [{self.status}]"

Patch submissions/admin.py to register reports:

--- a/submissions/admin.py
+++ b/submissions/admin.py
@@ -1,7 +1,8 @@
 from django.contrib import admin
 from safedelete.admin import SafeDeleteAdmin, highlight_deleted
-from .models import Submission, SubmissionFile
+from .models import Submission, SubmissionFile, SubmissionReport
@@ -47,3 +48,12 @@
 class SubmissionFileAdmin(admin.ModelAdmin):
     list_display = ('id', 'submission', 'file', 'uploaded_at')
     search_fields = ('submission__title',)
     list_filter = ('uploaded_at',)
     readonly_fields = ('uploaded_at',)
+
+@admin.register(SubmissionReport)
+class SubmissionReportAdmin(admin.ModelAdmin):
+    list_display = ("id","submission","reporter","status","created_at")
+    list_filter = ("status","created_at")
+    search_fields = ("submission__title","reporter__username","reason")

3) Implement API endpoint in SubmissionViewSet.report to persist report

Patch submissions/views.py report action:

--- a/submissions/views.py
+++ b/submissions/views.py
@@ -61,11 +61,20 @@
     @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
     def report(self, request, pk=None):
-        submission = self.get_object()
-        print(f"User '{request.user.username}' reported submission '{submission.title}' (ID: {submission.id})")
-        return Response(
-            {'message': 'Submission has been reported to the administrators.'},
-            status=status.HTTP_200_OK
-        )
+        submission = self.get_object()
+        reason = request.data.get("reason") or "No reason provided"
+        from .models import SubmissionReport
+        SubmissionReport.objects.create(submission=submission, reporter=request.user, reason=reason)
+        return Response({'message': 'Report submitted.'}, status=status.HTTP_201_CREATED)

4) Migrations and tests
- poetry run python manage.py makemigrations submissions
- poetry run python manage.py migrate
- poetry run pytest -q

Acceptance for Phase 7:
- Reports saved to DB.
- Admin UI allows triage of reports.
- No outgoing emails or notifications sent.
- Tests pass.
9. Phase 8 — Test-first: comment and submission rate-limits and registered_only/blocked enforcement
1) Add tests

Create comments/tests/test_rate_limits_and_visibility.py:

import pytest
from model_bakery import baker
from django.urls import reverse

@pytest.mark.django_db
def test_comment_create_rate_limited(api_client, settings):
    author = baker.make("users.User")
    sub = baker.make("submissions.Submission", owner=author, visibility="public", registered_only=False)
    api_client.force_authenticate(user=author)
    url = reverse("submission-comments-list", kwargs={"submission_pk": sub.id})
    r1 = api_client.post(url, {"content":"hi"})
    r2 = api_client.post(url, {"content":"again"})
    assert r1.status_code in (200,201)
    assert r2.status_code in (429, 403, 400)  # depending on decorator config

2) Enforce rate limit and registered_only in comments.view

Patch comments/views.py:

--- a/comments/views.py
+++ b/comments/views.py
@@ -1,10 +1,22 @@
 from rest_framework import viewsets, permissions
 from django.shortcuts import get_object_or_404
 from submissions.models import Submission
 from .models import Comment
 from .serializers import CommentSerializer
 from .permissions import IsAuthorOrReadOnly
+from django.utils.decorators import method_decorator
+from django.conf import settings
+from django_ratelimit.decorators import ratelimit

 class CommentViewSet(viewsets.ModelViewSet):
@@ -12,16 +24,35 @@
     serializer_class = CommentSerializer
     permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

+    @method_decorator(
+        ratelimit(
+            key='user_or_ip',
+            rate=f"1/{getattr(settings,'COMMENT_COOLDOWN_SECONDS',8)}s",
+            method='POST',
+            block=True
+        ),
+        name='create',
+    )
+    def dispatch(self, *args, **kwargs):  # type: ignore[override]
+        return super().dispatch(*args, **kwargs)
+
     def get_queryset(self):
         submission_pk = self.kwargs['submission_pk']
-        return Comment.objects.filter(submission_id=submission_pk, parent__isnull=True)
+        sub = get_object_or_404(Submission, pk=submission_pk)
+        qs = Comment.objects.filter(submission=sub, parent__isnull=True)
+        # enforce registered_only/blocking
+        from core.views import can_view_submission
+        if not can_view_submission(self.request.user, sub):
+            return Comment.objects.none()
+        return qs

     def perform_create(self, serializer):
-        submission = get_object_or_404(Submission, pk=self.kwargs['submission_pk'])
+        submission = get_object_or_404(Submission, pk=self.kwargs['submission_pk'])
+        from core.views import can_view_submission
+        if not can_view_submission(self.request.user, submission):
+            self.permission_denied(self.request)
         serializer.save(author=self.request.user, submission=submission)

3) Run tests
- poetry run pytest -q

Acceptance for Phase 8:
- Rate limits applied to comments creates.
- registered_only and blocked enforcement applied in comments endpoints.
- Tests pass.
10. Phase 9 — Weekly Celery tasks: cleanup soft-deleted and recalc trending (Wilson score)
1) Implement tasks

Create core/tasks.py:

from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from safedelete.models import HARD_DELETE
from submissions.models import Submission

@shared_task
def cleanup_soft_deleted():
    cutoff = timezone.now() - timedelta(days=30)
    # Purge soft-deleted submissions older than cutoff
    # safedelete uses deleted field to store timestamp
    qs = Submission.all_objects.filter(deleted__isnull=False, deleted__lt=cutoff)
    count = 0
    for obj in qs:
        obj.delete(force_policy=HARD_DELETE)
        count += 1
    return count

Create submissions/tasks.py:

from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from django.db.models import Q, Count
from .models import Submission, SubmissionVote
import math

def wilson_lower_bound(pos, n, z=1.96):
    if n == 0:
        return 0.0
    phat = 1.0 * pos / n
    return max(0.0, (phat + z*z/(2*n) - z*math.sqrt((phat*(1-phat)+z*z/(4*n))/n)) / (1+z*z/n))

@shared_task
def recalculate_trending():
    now = timezone.now()
    window_start = now - timedelta(days=7)
    # For each submission, compute Wilson score on last 7 days
    for sub in Submission.objects.all():
        votes = SubmissionVote.objects.filter(submission=sub, created_at__gte=window_start)
        up = votes.filter(value=SubmissionVote.UP).count()
        total = votes.count()
        score = wilson_lower_bound(up, total)
        if sub.trending_score != score:
            sub.trending_score = score
            sub.save(update_fields=["trending_score"])
    return True

2) Make sure Celery beat tables are present
- poetry run python manage.py migrate django_celery_beat

3) Start worker and beat during local dev (after all phases when testing)
- poetry run celery -A config worker -l info
- poetry run celery -A config beat -l info

Acceptance for Phase 9:
- cleanup_soft_deleted task deletes soft-deleted submissions older than 30 days.
- recalculate_trending updates trending_score using last 7 days Wilson LB.
- celery beat schedule registered in settings runs weekly.
11. Phase 10 — Safer interactive reset script replacing flush.sh
1) Add scripts/reset.sh and remove flush.sh

- git rm flush.sh

Create scripts/reset.sh (make executable chmod +x scripts/reset.sh):

#!/usr/bin/env bash
set -euo pipefail

if [ ! -f ".env" ]; then
  echo ".env not found. Aborting."
  exit 1
fi

source <(grep -E '^(POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_HOST|POSTGRES_PORT|ENV)=' .env | sed 's/^/export /')

echo "This will DROP and RECREATE the Postgres database: ${POSTGRES_DB} on ${POSTGRES_HOST}:${POSTGRES_PORT}"
read -p "Type the database name '${POSTGRES_DB}' to confirm: " CONFIRM
if [ "${CONFIRM}" != "${POSTGRES_DB}" ]; then
  echo "Confirmation mismatch. Aborting."
  exit 1
fi

echo "Dropping database..."
dropdb --if-exists -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" "${POSTGRES_DB}" || true

echo "Creating database..."
createdb -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" "${POSTGRES_DB}"

echo "Applying migrations..."
poetry run python manage.py migrate

read -p "Create superuser now? (y/N): " CREATE_SU
if [[ "${CREATE_SU}" == "y" || "${CREATE_SU}" == "Y" ]]; then
  poetry run python manage.py createsuperuser
fi

echo "Reset complete."

2) Document in README and ensure devs have dropdb/createdb installed (from postgresql-client).

Acceptance for Phase 10:
- flush.sh is removed.
- scripts/reset.sh interacts and uses .env to drop/recreate Postgres DB and apply migrations safely.
12. Phase 11 — Documentation: README overhaul and docs/ scaffold with mermaid diagrams
1) Replace README.md with project overview, stack, setup, run, Celery, reset, and basic API smoke tests

Overwrite README.md with:

# FileForum

A forum-like service for seamless file sharing with short links. Backend: Django + DRF, Postgres, Redis/Celery. Local file storage for development.

## Tech Stack
- Python 3.11.14, Django 4.2, DRF
- Postgres (dev), Redis (Celery broker/result)
- Celery + django-celery-beat (weekly tasks)
- django-safedelete (soft deletes)
- django-guardian (object-level perms), django-ratelimit
- Markdown + bleach sanitized HTML

## Features
- Submissions under /s/&lt;slug&gt; (default 8 alphanumeric, admin-customizable)
- Roles per submission: owner/editor/viewer
- Visibility: public, private, link_only + registered_only boolean
- Voting: up/down => 0–5 stars
- Reporting: admin-only triage
- Hierarchical folders and file management per submission
- Blocking: Profile.blocked_users prevents access
- Rate limits: create/edit/comments/messaging (env-configurable)
- Weekly tasks: purge soft-deleted older than 30 days, recalc trending (Wilson)

## Architecture (Mermaid)

```mermaid
flowchart TD
A[Client] -->|REST| B(DRF API)
B --> C[Submissions]
B --> D[Comments]
B --> E[Messaging]
B --> F[Users/Profile]
C --> G[(Postgres)]
D --> G
E --> G
F --> G
B --> H{Celery}
H --> I[(Redis)]
H -->|beat| J[Weekly Tasks]
```

```mermaid
sequenceDiagram
  participant U as User
  participant API as DRF API
  participant DB as Postgres
  participant R as Redis/Celery
  U->>API: POST /api/submissions/
  API->>DB: Create Submission (slug)
  API-->>U: 201 Created (slug)
  U->>API: POST /api/submissions/{id}/files/
  API->>DB: Save files (folder path)
  API-->>U: 201 Created
  Note over U,API: Upvote/downvote maps to star rating
```

## Local Setup

- pyenv install -s 3.11.14
- pyenv local 3.11.14
- poetry env use 3.11.14
- poetry install
- Create .env (see example in plan)
- Prepare Postgres and Redis (see plan commands)

## Database Migrations

- poetry run python manage.py makemigrations
- poetry run python manage.py migrate

## Run Dev Server

- poetry run python manage.py runserver

## Celery

- poetry run celery -A config worker -l info
- poetry run celery -A config beat -l info

## Safe Reset

- bash scripts/reset.sh

## Tests

- poetry run pytest -q
- poetry run pytest --cov

## API Smoke (examples)

- Get submissions: curl http://127.0.0.1:8000/api/submissions/
- Upvote: httpie -A bearer -a $TOKEN POST :8000/api/submissions/1/upvote/

2) Create docs/ directory and initial guides

Create these files:

docs/architecture.md
docs/data_model.md
docs/permissions_roles.md
docs/rate_limits.md
docs/tasks_scheduling.md
docs/contributing.md

Example docs/architecture.md:

# Architecture

```mermaid
flowchart LR
Client --> DRF --> Postgres
DRF --> Celery --> Redis
```

Add similar detailed content outlining models, relationships (ERD), roles/permissions, rate limit strategy, weekly tasks, and contributor guide.

Acceptance for Phase 11:
- README provides full setup/run/reset instructions and diagrams.
- docs/ folder contains initial markdown guides.
13. Phase 12 — Wire UI minimally to login/register later (after backend is green)
Scope note: Frontend wiring is minimal in this batch. Once all backend tests are green, add template links for login/register pages backed by JWT or session auth. Do not expose admin registration; admins created via createsuperuser and have Profiles with badges as implemented.

Acceptance for Phase 12:
- Templates link to auth pages, but backend remains the focus.
14. Global — Run full test suite and start services
- poetry run pytest -q
- poetry run python manage.py runserver
- poetry run celery -A config worker -l info
- poetry run celery -A config beat -l info

Acceptance (global):
- Server boots against Postgres using .env.
- Redis broker works; Celery worker/beat start without errors.
- All migrations applied.
- Tests pass.
15. Acceptance Criteria Checklist
- Postgres and Redis configuration via .env; server starts clean.
- Slug routing /s/&lt;slug&gt;, reserved words enforced, case-insensitive uniqueness.
- registered_only flag respected for guests.
- Roles owner/editor/viewer with owner member management endpoints.
- Profile.blocked_users prevents viewing submissions and shows clear forbidden message; badges exposed.
- Hierarchical folders under submissions; file operations restricted to owner/editors.
- Voting endpoints work; rating maps to 0–5 stars; 0-vote returns None/“No rating yet”.
- Reports persisted and manageable via Django admin; no outbound notifications.
- Weekly Celery tasks run; trending_score updated; soft-deleted items older than 30 days purged.
- Rate limits enforced for submission create/edit, comments, messaging per .env seconds.
- README and docs/ updated with diagrams and instructions.
- Safer scripts/reset.sh replaces flush.sh.
- Test suite passes locally.
16. Appendix — Commands quick reference
- Environment
  - pyenv install -s 3.11.14
  - pyenv local 3.11.14
  - poetry env use 3.11.14
  - poetry install

- Dependencies
  - poetry add markdown==3.7 bleach==6.2.0
  - poetry add django-celery-beat@^2.8.1

- DB and cache
  - sudo -u postgres psql -c "CREATE USER file_forum_user WITH PASSWORD 'file_forum_pass';"
  - sudo -u postgres psql -c "CREATE DATABASE file_forum OWNER file_forum_user;"
  - sudo apt-get install -y redis-server

- Migrations and run
  - poetry run python manage.py makemigrations
  - poetry run python manage.py migrate
  - poetry run python manage.py runserver

- Celery
  - poetry run celery -A config worker -l info
  - poetry run celery -A config beat -l info

- Tests
  - poetry run pytest -q

- Reset
  - bash scripts/reset.sh

UpdateTodos: 16 items
Acknowledged. I’ll proceed with this backend-first plan and begin implementing in phases.

Do you want me to start by fixing the messaging permission bug and switching settings to Postgres/Redis with a .env scaffold, then add the slug routing and tests?
```
