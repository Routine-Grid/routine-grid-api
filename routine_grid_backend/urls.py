from django.contrib import admin
from django.urls import include, path
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users.views import RegisterView

from .views import (
    ScalarDocumentationView,
    TaggedResetPasswordConfirm,
    TaggedResetPasswordRequestToken,
    TaggedResetPasswordValidateToken,
)


class TaggedTokenObtainPairView(TokenObtainPairView):
    @extend_schema(
        tags=["Authentication"],
        summary="Login",
        description="Obtain access and refresh JWT tokens using username and password.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TaggedTokenRefreshView(TokenRefreshView):
    @extend_schema(
        tags=["Authentication"],
        summary="Refresh token",
        description="Obtain a new access token using a valid refresh token.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.habits.urls")),
    path(
        "api/v1/auth/login/",
        TaggedTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/v1/auth/refresh/", TaggedTokenRefreshView.as_view(), name="token_refresh"
    ),
    path("api/v1/auth/register/", RegisterView.as_view(), name="auth_register"),
    path(
        "api/v1/auth/password_reset/",
        TaggedResetPasswordRequestToken.as_view(),
        name="reset_password_request",
    ),
    path(
        "api/v1/auth/password_reset/confirm/",
        TaggedResetPasswordConfirm.as_view(),
        name="reset_password_confirm",
    ),
    path(
        "api/v1/auth/password_reset/validate_token/",
        TaggedResetPasswordValidateToken.as_view(),
        name="reset_password_validate",
    ),
    path("api/v1/users/", include("apps.users.urls")),
    path("api/schema.yaml", SpectacularAPIView.as_view(), name="schema"),
    path("", ScalarDocumentationView.as_view(), name="scalar-docs"),
]
