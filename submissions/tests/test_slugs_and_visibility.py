import pytest
from django.urls import reverse
from model_bakery import baker
from django.core.exceptions import ValidationError
from submissions.models import Submission


@pytest.mark.django_db
def test_submission_has_8_char_slug_by_default():
    user = baker.make("users.User")
    sub = baker.make(Submission, owner=user)
    assert sub.slug
    assert len(sub.slug) == 8
    assert sub.slug.isalnum()


@pytest.mark.django_db
def test_reserved_slug_is_rejected():
    user = baker.make("users.User")
    sub = Submission(title="X", owner=user, visibility="public", slug="admin")
    with pytest.raises(ValidationError):
        sub.save()


@pytest.mark.django_db
def test_registered_only_blocks_anonymous(client):
    user = baker.make("users.User")
    sub = baker.make(Submission, owner=user, visibility="public", registered_only=True)
    url = reverse("submission_slug_detail", kwargs={"slug": sub.slug})
    resp = client.get(url)
    assert resp.status_code in (401, 403, 302)


@pytest.mark.django_db
def test_slug_route_serves_detail_for_public_authenticated(client):
    user = baker.make("users.User")
    sub = baker.make(Submission, owner=user, visibility="public", registered_only=False)
    client.force_login(user)
    url = reverse("submission_slug_detail", kwargs={"slug": sub.slug})
    resp = client.get(url)
    assert resp.status_code == 200
    assert sub.title.encode() in resp.content
