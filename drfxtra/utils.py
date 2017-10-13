from allauth.account.models import EmailAddress

def user_verify_email(user):
    EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)

def user_verify_email_with_check_existing(user):
    emailaddress, created = EmailAddress.objects.get_or_create(user=user, email=user.email, primary=True)
    if not emailaddress.verified:
        emailaddress.verified = True
        emailaddress.save()