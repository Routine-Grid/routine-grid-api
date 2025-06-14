# apps/users/management/commands/test_email.py

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Test email sending"

    def add_arguments(self, parser):
        parser.add_argument(
            "email", type=str, help="Email address to send test email to"
        )

    def handle(self, *args, **options):
        try:
            send_mail(
                "Test Email from Routine Grid",
                "This is a test email to verify SMTP configuration.",
                settings.DEFAULT_FROM_EMAIL,
                [options["email"]],
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Test email sent successfully to {options['email']}"
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email: {str(e)}"))
