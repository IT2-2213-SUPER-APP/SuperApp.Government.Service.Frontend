from rest_framework import permissions

class IsSenderOrRecipient(permissions.BasePermission):
    """
    Allow access only to sender or recipient of the Message object.
    For create: any authenticated user can create (sender becomes request.user).
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return request.user == obj.sender or request.user == obj.recipient
