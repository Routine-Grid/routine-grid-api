# apps/users/signals.py

from django.conf import settings
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created


@receiver(reset_password_token_created)
def password_reset_token_created(
    sender, instance, reset_password_token, *args, **kwargs
):
    """
    Handles password reset tokens
    When a token is created, an email needs to be sent to the user
    """
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string

    # Generate the reset URL
    reset_password_url = (
        f"{settings.FRONTEND_URL}/reset-password?token={reset_password_token.key}"
    )

    # Email context
    context = {
        "current_user": reset_password_token.user,
        "username": reset_password_token.user.username,
        "user_email": reset_password_token.user.email,
        "reset_password_url": reset_password_url,
        "token": reset_password_token.key,
    }

    # Render email templates
    email_html_message = render_to_string(
        "django_rest_passwordreset/password_reset_token.html", context
    )
    email_plaintext_message = render_to_string(
        "django_rest_passwordreset/password_reset_token.txt", context
    )

    # Create and send email
    msg = EmailMultiAlternatives(
        # Subject
        "Reset Your Routine Grid Password",
        # Body (text)
        email_plaintext_message,
        # From email
        settings.DEFAULT_FROM_EMAIL,
        # To email list
        [reset_password_token.user.email],
    )

    # Attach HTML version
    msg.attach_alternative(email_html_message, "text/html")

    # Send the email
    msg.send()
