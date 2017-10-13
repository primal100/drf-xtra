from .utils import user_verify_email, user_verify_email_with_check_existing

def user_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    if not update_fields or any(f in update_fields for f in ["is_superuser", "is_staff"]):
            if instance.is_staff or instance.is_superuser:
                if created:
                    user_verify_email(instance)
                else:
                    user_verify_email_with_check_existing(instance)