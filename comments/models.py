from django.db import models
from config.settings import AUTH_USER_MODEL
from submissions.models import Submission

class Comment(models.Model):
    submission = models.ForeignKey(Submission, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)

    def __str__(self):
        return f'Comment by {self.author} on {self.submission}'
