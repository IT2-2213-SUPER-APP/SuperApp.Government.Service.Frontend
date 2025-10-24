from django.db.models import Q
from rest_framework import viewsets, permissions
from .models import Message
from .serializers import MessageSerializer
from .permissions import IsSenderOrRecipient
from django.utils.decorators import method_decorator
from django.conf import settings
from django_ratelimit.decorators import ratelimit

class MessageViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing messages and sending new ones.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsSenderOrRecipient]

    def get_queryset(self):
        """
        This view should return a list of all messages
        sent to or from the currently authenticated user.
        """
        user = self.request.user
        return Message.objects.filter(Q(sender=user) | Q(recipient=user))

    @method_decorator(
        ratelimit(
            key='user_or_ip',
            rate=f"1/{getattr(settings, 'MESSAGE_COOLDOWN_SECONDS', 2)}s",
            method='POST',
            block=True,
        )
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    def perform_create(self, serializer):
        """
        Set the current user as the sender of the message.
        """
        serializer.save(sender=self.request.user)
