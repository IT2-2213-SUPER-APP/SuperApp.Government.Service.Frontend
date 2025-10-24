from rest_framework import serializers

from .models import Submission, SubmissionFile


class SubmissionFileSerializer(serializers.ModelSerializer):
    """
    Serializer for the SubmissionFile model.

    Handles the serialization of file objects, providing the file URL
    and upload timestamp. The `submission` field is implicitly handled by the
    nested URL structure in the viewset, so it's not included here.
    """
    # Use SerializerMethodField to return the full URL of the file.
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = SubmissionFile
        fields = [
            'id',
            'file',
            'file_url',
            'uploaded_at'
        ]
        # The 'file' field is write-only because we want to receive the upload,
        # but we will serve the URL via 'file_url'.
        extra_kwargs = {
            'file': {'write_only': True}
        }

    def get_file_url(self, obj):
        """
        Returns the absolute URL for the file.
        """
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None


class SubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Submission model.

    Provides a detailed view of a submission, including its owner, associated
    files, and other metadata. It uses a nested serializer to display a list
    of files within the submission.
    """
    # Make the owner field read-only and display the username for clarity.
    owner = serializers.ReadOnlyField(source='owner.username')

    # Use the SubmissionFileSerializer to nest the associated files.
    # This will render a list of file objects within the submission JSON.
    # `many=True` indicates it's a list of objects.
    # `read_only=True` means you cannot create/update files through this serializer;
    # that is handled by the dedicated SubmissionFileViewSet.
    files = SubmissionFileSerializer(many=True, read_only=True)

    class Meta:
        model = Submission
        fields = [
            'id',
            'title',
            'description',
            'owner',
            'visibility',
            'slug',
            'files',  # The nested list of files
            'created_at',
            'updated_at',
        ]
        # Mark fields that should not be editable by the client as read-only.
        read_only_fields = [
            'slug',
            'created_at',
            'updated_at',
        ]

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
