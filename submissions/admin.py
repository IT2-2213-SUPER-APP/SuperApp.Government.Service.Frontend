from django.contrib import admin
from safedelete.admin import SafeDeleteAdmin, highlight_deleted

from .models import Submission, SubmissionFile, SubmissionReport


class SubmissionFileInline(admin.TabularInline):
    """
    Allows editing files directly within the Submission admin page.
    This provides a more integrated and convenient admin experience.
    """
    model = SubmissionFile
    extra = 1  # Show one extra empty slot for uploading a new file.
    readonly_fields = ('uploaded_at',)


@admin.register(Submission)
class SubmissionAdmin(SafeDeleteAdmin):
    """
    Admin interface configuration for the Submission model.
    """
    # Use SafeDeleteAdmin to manage soft-deleted objects
    list_display = (
        highlight_deleted,  # Visually strike through deleted items
        'title',
        'owner',
        'visibility',
        'slug',
        'registered_only',
        'created_at',
    )
    search_fields = ('title', 'owner__username')
    list_filter = ('visibility', 'registered_only', 'deleted', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SubmissionFileInline]  # Nest the file editor

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            ro.append('slug')
        return ro


@admin.register(SubmissionFile)
class SubmissionFileAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for the SubmissionFile model.
    """
    list_display = ('id', 'submission', 'file', 'uploaded_at')
    search_fields = ('submission__title',)
    list_filter = ('uploaded_at',)
    readonly_fields = ('uploaded_at',)


@admin.register(SubmissionReport)
class SubmissionReportAdmin(admin.ModelAdmin):
    list_display = ("id","submission","reporter","status","created_at")
    list_filter = ("status","created_at")
    search_fields = ("submission__title","reporter__username","reason")
