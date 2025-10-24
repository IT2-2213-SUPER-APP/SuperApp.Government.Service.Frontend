from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden
from submissions.models import Submission
from users.models import Profile

def home_view(request):
    """
    Renders the homepage with public submissions.
    """
    public_submissions = Submission.objects.filter(visibility='public').order_by('-created_at')
    context = {
        'submissions': public_submissions
    }
    return render(request, 'home.html', context)

def is_blocked(owner, user):
    if not user.is_authenticated:
        return False
    try:
        owner_profile = owner.profile
    except Profile.DoesNotExist:
        return False
    blocked = getattr(owner_profile, 'blocked_users', None)
    if blocked is None:
        return False
    return blocked.filter(id=user.id).exists()


def can_view_submission(user, submission: Submission):
    if is_blocked(submission.owner, user):
        return False
    if submission.visibility == Submission.Visibility.PUBLIC:
        if getattr(submission, 'registered_only', False) and not user.is_authenticated:
            return False
        return True
    if user.is_authenticated:
        if user == submission.owner:
            return True
        # Allow editors/viewers
        try:
            from submissions.models import SubmissionMember
            if SubmissionMember.is_viewer(user, submission):
                return True
        except Exception:
            pass
    return False


def submission_detail_view_by_slug(request, slug):
    """
    Renders the detail page for a single submission by slug.
    """
    submission = get_object_or_404(
        Submission.objects.prefetch_related('files', 'comments__replies'),
        slug__iexact=slug
    )
    if not can_view_submission(request.user, submission):
        if request.user.is_authenticated and is_blocked(submission.owner, request.user):
            return HttpResponseForbidden("You are blocked by this user.")
        return HttpResponseForbidden("You do not have permission to view this.")

    context = {
        'submission': submission
    }
    return render(request, 'submission_detail.html', context)


def upload_view(request):
    """
    Placeholder view for the file upload page.
    """
    return render(request, 'upload.html')


def login_view(request):
    """Render a minimal login page that posts to /api/users/token/."""
    return render(request, 'login.html')


def register_view(request):
    """Render a minimal register page that posts to /api/users/register/."""
    return render(request, 'register.html')
