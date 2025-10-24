from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'submission', 'content', 'created_at', 'parent')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username', 'submission__title')
