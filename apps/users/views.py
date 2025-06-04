# apps/users/views.py

from django.contrib.auth import get_user_model

# Import RetrieveUpdateDestroyAPIView
from rest_framework import generics, permissions

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


# Keep RegisterView as is
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer


# Modify UserProfileView
class UserProfileView(generics.RetrieveUpdateDestroyAPIView):  # <-- CHANGE HERE
    """
    API endpoint for fetching, updating, and DELETING
    the authenticated user's profile.
    Handles GET (retrieve), PUT/PATCH (update), and DELETE (delete account).
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]  # Must be logged in

    def get_object(self):
        """
        Returns the authenticated user making the request.
        """
        return self.request.user

    # No need to explicitly define a destroy method if the default behavior
    # (calling self.get_object().delete()) is what you want.
    # The get_object() method already returns request.user, so a DELETE
    # request to this view will call request.user.delete().
