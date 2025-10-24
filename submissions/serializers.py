from rest_framework import serializers
import markdown as md
import bleach
from django.conf import settings

from .models import Submission, SubmissionFile, submission_vote_stats, Folder


class SubmissionFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    folder_id = serializers.PrimaryKeyRelatedField(
        queryset=Folder.objects.all(), source='folder', required=False, allow_null=True
    )

    class Meta:
        model = SubmissionFile
        fields = [
            'id',
            'file',
            'file_url',
            'uploaded_at',
            'folder_id',
        ]
        extra_kwargs = {
            'file': {'write_only': True}
        }

    def validate(self, attrs):
        submission = self.context.get('submission')
        folder = attrs.get('folder')
        if folder and folder.submission_id != submission.id:
            raise serializers.ValidationError({'folder_id': 'Folder must belong to this submission.'})
        return attrs

    def get_file_url(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None


class FolderSerializer(serializers.ModelSerializer):
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Folder.objects.all(), source='parent', required=False, allow_null=True
    )

    class Meta:
        model = Folder
        fields = ['id', 'name', 'parent_id', 'created_at']


class SubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Submission model.

    Provides a detailed view of a submission, including its owner, associated
    files, and other metadata. It uses a nested serializer to display a list
    of files within the submission.
    """
    owner = serializers.ReadOnlyField(source='owner.username')
    files = SubmissionFileSerializer(many=True, read_only=True)
    description_html = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            'id',
            'title',
            'description',
            'description_html',
            'owner',
            'visibility',
            'slug',
            'files',
            'rating',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'slug',
            'created_at',
            'updated_at',
            'rating',
            'description_html',
        ]

    def get_description_html(self, obj):
        raw = obj.description or ""
        html = md.markdown(raw, extensions=["extra"])
        allowed_tags = getattr(settings, "MARKDOWN_ALLOWED_TAGS", {"p","a","em","strong"})
        allowed_attrs = getattr(settings, "MARKDOWN_ALLOWED_ATTRS", {"a": {"href","title"}})
        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)

    def get_rating(self, obj):
        return submission_vote_stats(obj)
    def create(self, validated_data):
        """
        Create and return a new `Submission` instance, given the validated data.
        """
        return Submission.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Submission` instance, given the validated data.
        """
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.visibility = validated_data.get('visibility', instance.visibility)
        instance.save()
        return instance
