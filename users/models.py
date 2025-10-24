from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    email = models.EmailField(unique=True)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    blocked_users = models.ManyToManyField(User, related_name='blocked_by_profiles', blank=True)
    is_banned = models.BooleanField(default=False)
    is_silenced = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    @property
    def badge(self):
        u = self.user
        if self.is_banned:
            return "banned"
        if self.is_silenced:
            return "silenced"
        if u.is_superuser:
            return "admin"
        if u.is_staff:
            return "mod"
        return "regular"

@receiver(post_save, sender=User)
def create_profile_for_user(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
