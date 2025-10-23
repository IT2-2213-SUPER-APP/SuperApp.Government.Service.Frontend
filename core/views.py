from django.shortcuts import render
from submissions.models import Submission

def home_view(request):
    """
    Renders the homepage.

    Fetches all submissions that are marked as 'public' to display on the feed.
    """
    # We only want to show public submissions on the main feed.
    public_submissions = Submission.objects.filter(visibility='public').order_by('-created_at')

    context = {
        'submissions': public_submissions
    }
    return render(request, 'home.html', context)
