from rest_framework import serializers
from .models import Comment

class RecursiveField(serializers.Serializer):
    """
    A field that recursively serializes its parent's data.
    Used to display nested comments (replies).
    """
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Comment model.
    """
    author = serializers.ReadOnlyField(source='author.username')
    replies = RecursiveField(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id',
            'author',
            'content',
            'created_at',
            'parent',
            'replies'
        ]
        read_only_fields = ['created_at', 'author', 'replies']
        extra_kwargs = {
            'parent': {'write_only': True, 'required': False}
        }
