from rest_framework import permissions
from .models import SubmissionMember

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class IsOwnerOrEditor(permissions.BasePermission):
    """Allow write for owner or editors; read for safe methods."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user == obj.owner:
            return True
        return SubmissionMember.is_editor(request.user, obj)
