# apps/users/views.py

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema

# Import RetrieveUpdateDestroyAPIView
from rest_framework import generics, permissions

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


@extend_schema(
    tags=["Authentication"],
    summary="Register new user",
    description="Create a new user account with username, email, and password.",
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer


@extend_schema(
    tags=["Users"],
    summary="User profile management",
    description="Get, update, or delete the authenticated user's profile.",
)
class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for fetching, updating, and DELETING
    the authenticated user's profile.
    Handles GET (retrieve), PUT/PATCH (update), and DELETE (delete account).
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Returns the authenticated user making the request.
        """
        return self.request.user
