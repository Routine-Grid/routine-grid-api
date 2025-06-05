import json

from django.conf import settings
from django.views.generic import TemplateView
from django_rest_passwordreset.views import (
    ResetPasswordConfirm,
    ResetPasswordRequestToken,
    ResetPasswordValidateToken,
)
from drf_spectacular.utils import extend_schema


class ScalarDocumentationView(TemplateView):
    template_name = "api_docs/scalar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        schema_url = self.request.build_absolute_uri("/api/schema.yaml")
        context["schema_url"] = schema_url

        # Dynamic server configuration
        if settings.DEBUG:
            servers = [
                {
                    "url": self.request.build_absolute_uri("/")[:-1],
                    "description": "Development",
                },
                {"url": "https://api.routinegrid.com", "description": "Production"},
            ]
        else:
            servers = [
                {"url": "https://api.routinegrid.com", "description": "Production"}
            ]

        context["servers"] = json.dumps(servers)
        return context


# Tagged Password Reset Views
@extend_schema(
    tags=["Authentication"],
    summary="Request password reset",
    description="Request a password reset token to be sent to the user's email address.",
)
class TaggedResetPasswordRequestToken(ResetPasswordRequestToken):
    pass


@extend_schema(
    tags=["Authentication"],
    summary="Confirm password reset",
    description="Reset password using the token received via email.",
)
class TaggedResetPasswordConfirm(ResetPasswordConfirm):
    pass


@extend_schema(
    tags=["Authentication"],
    summary="Validate reset token",
    description="Validate that a password reset token is valid before using it.",
)
class TaggedResetPasswordValidateToken(ResetPasswordValidateToken):
    pass
