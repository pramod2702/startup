from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.utils import timezone
from .models import UserProfile

@receiver(user_logged_in)
def update_user_profile_last_login(sender, request, user, **kwargs):
    """
    Update the UserProfile last_login field when a user logs in
    """
    try:
        profile = user.profile
        old_last_login = profile.last_login
        profile.last_login = timezone.now()
        profile.save(update_fields=['last_login'])
        print(f"Signal: Updated last_login for user {user.username} from {old_last_login} to {profile.last_login}")
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = UserProfile.objects.create(
            user=user,
            last_login=timezone.now(),
            login_method='unknown'
        )
        print(f"Signal: Created profile for user {user.username} with last_login {profile.last_login}")
    except Exception as e:
        print(f"Signal error updating profile for user {user.username}: {str(e)}")

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile when a new User is created
    """
    if created:
        UserProfile.objects.create(
            user=instance,
            login_method='unknown'
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile when the User is saved
    """
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        UserProfile.objects.create(
            user=instance,
            login_method='unknown'
        )
