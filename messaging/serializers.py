from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.ReadOnlyField(source='sender.username')
    recipient = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )

    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'subject', 'body', 'sent_at', 'read_at']
        read_only_fields = ['sent_at', 'read_at']
