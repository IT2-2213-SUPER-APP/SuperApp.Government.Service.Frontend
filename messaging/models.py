from django.db import models
from config.settings import AUTH_USER_MODEL

class Message(models.Model):
    sender = models.ForeignKey(AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.subject
