# apps/users/tests.py

from django.contrib.auth import get_user_model
from django.urls import reverse  # Used to get URL by name instead of hardcoding
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationAPITest(APITestCase):
    """Tests for the user registration endpoint."""

    def setUp(self):
        """Define the URL for the tests."""
        self.register_url = reverse("auth_register")  # Gets '/api/v1/auth/register/'

    def test_register_user_success(self):
        """
        Ensure we can register a new user successfully.
        """
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPassword123",
            "password2": "StrongPassword123",
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post(self.register_url, data, format="json")

        # Check response status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that the user was actually created in the database
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(User.objects.filter(username="testuser").exists())
        user = User.objects.get(username="testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "Test")
        # Check password was hashed (cannot check exact hash easily)
        self.assertTrue(user.has_usable_password())

    def test_register_user_password_mismatch(self):
        """
        Ensure registration fails if passwords don't match.
        """
        data = {
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "StrongPassword123",
            "password2": "WrongPassword",  # Mismatched password
        }
        response = self.client.post(self.register_url, data, format="json")

        # Check response status code indicates a bad request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check that no user was created
        self.assertEqual(User.objects.count(), 0)
        # Check specific error message (optional but good)
        self.assertIn(
            "password",
            response.data,  # type: ignore
        )  # Check if 'password' field has an error
        self.assertEqual(response.data["password"][0], "Password fields didn't match.")  # type: ignore

    def test_register_user_missing_fields(self):
        """
        Ensure registration fails if required fields are missing (e.g., email).
        """
        data = {
            "username": "testuser3",
            # 'email': 'test3@example.com', # Missing email
            "password": "StrongPassword123",
            "password2": "StrongPassword123",
        }
        response = self.client.post(self.register_url, data, format="json")

        # Check response status code indicates a bad request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check that no user was created
        self.assertEqual(User.objects.count(), 0)
        # Check specific error message
        self.assertIn("email", response.data)  # type: ignore
        self.assertEqual(response.data["email"][0], "This field is required.")  # type: ignore

    # Add more tests: duplicate username, duplicate email, invalid email format, weak password etc.


# --- Add New Test Class for Login ---
class LoginAPITest(APITestCase):
    """Tests for the user login endpoint (TokenObtainPairView)."""

    def setUp(self):
        """Set up a test user and the login URL."""
        self.login_url = reverse("token_obtain_pair")  # Gets '/api/v1/auth/login/'
        self.username = "testloginuser"
        self.email = "login@example.com"
        self.password = "StrongPassword123"

        # Create a user directly in the test database
        self.user = User.objects.create_user(
            username=self.username, email=self.email, password=self.password
        )

    def test_login_success(self):
        """
        Ensure a registered user can log in and receive tokens.
        """
        data = {
            "username": self.username,  # Or 'email' if using email as username field
            "password": self.password,
        }
        response = self.client.post(self.login_url, data, format="json")

        # Check successful response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that access and refresh tokens are in the response data
        self.assertIn("access", response.data)  # type: ignore
        self.assertIn("refresh", response.data)  # type: ignore
        self.assertIsNotNone(response.data["access"])  # type: ignore
        self.assertIsNotNone(response.data["refresh"])  # type: ignore

    def test_login_invalid_password(self):
        """
        Ensure login fails with an incorrect password.
        """
        data = {
            "username": self.username,
            "password": "WrongPassword",  # Incorrect password
        }
        response = self.client.post(self.login_url, data, format="json")

        # Check unauthorized response
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)  # type: ignore
        self.assertNotIn("refresh", response.data)  # type: ignore

    def test_login_nonexistent_user(self):
        """
        Ensure login fails for a user that does not exist.
        """
        data = {"username": "nonexistentuser", "password": "AnyPassword"}
        response = self.client.post(self.login_url, data, format="json")

        # Check unauthorized response
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)  # type: ignore
        self.assertNotIn("refresh", response.data)  # type: ignore

    def test_login_missing_fields(self):
        """
        Ensure login fails if required fields (username/password) are missing.
        """
        # Test missing password
        data_no_pass = {"username": self.username}
        response_no_pass = self.client.post(self.login_url, data_no_pass, format="json")
        self.assertEqual(response_no_pass.status_code, status.HTTP_400_BAD_REQUEST)

        # Test missing username
        data_no_user = {"password": self.password}
        response_no_user = self.client.post(self.login_url, data_no_user, format="json")
        self.assertEqual(response_no_user.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileAPITest(APITestCase):
    """Tests for the user profile endpoint (/users/me/)."""

    def setUp(self):
        """Set up a test user and the profile URL."""
        self.profile_url = reverse("user-profile")  # Gets '/api/v1/users/me/'
        self.username = "profileuser"
        self.email = "profile@example.com"
        self.password = "StrongPassword123"
        self.first_name = "Profile"
        self.last_name = "User"

        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            first_name=self.first_name,
            last_name=self.last_name,
        )

    def test_get_profile_authenticated(self):
        """
        Ensure authenticated user can retrieve their profile.
        """
        # Force authenticate the client as the created user
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if key fields match the user created in setUp
        self.assertEqual(response.data["username"], self.username)
        self.assertEqual(response.data["email"], self.email)
        self.assertEqual(response.data["first_name"], self.first_name)
        self.assertEqual(response.data["last_name"], self.last_name)
        self.assertIn("id", response.data)
        self.assertIn("date_joined", response.data)
        self.assertIn("last_login", response.data)

    def test_get_profile_unauthenticated(self):
        """
        Ensure unauthenticated user cannot retrieve profile (gets 401).
        """
        # Do NOT authenticate the client
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_authenticated(self):
        """
        Ensure authenticated user can update their profile (e.g., first name).
        Using PATCH for partial update.
        """
        self.client.force_authenticate(user=self.user)
        new_first_name = "UpdatedFirstName"
        update_data = {"first_name": new_first_name}

        response = self.client.patch(self.profile_url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if the response data reflects the change
        self.assertEqual(response.data["first_name"], new_first_name)
        # Check if other data remained the same
        self.assertEqual(response.data["username"], self.username)
        self.assertEqual(response.data["email"], self.email)

        # Verify change in the database
        self.user.refresh_from_db()  # Reload user data from DB
        self.assertEqual(self.user.first_name, new_first_name)

    def test_update_profile_unauthenticated(self):
        """
        Ensure unauthenticated user cannot update profile (gets 401).
        """
        new_first_name = "UpdatedFirstName"
        update_data = {"first_name": new_first_name}
        # Do NOT authenticate the client
        response = self.client.patch(self.profile_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_readonly_field(self):
        """
        Ensure read-only fields (like username) cannot be updated.
        """
        self.client.force_authenticate(user=self.user)
        original_username = self.user.username
        update_data = {"username": "cannotchange"}  # Attempt to change username

        response = self.client.patch(self.profile_url, update_data, format="json")

        # Expect success (PATCH often ignores fields it can't set, unless specific validation added)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check username in response is UNCHANGED
        self.assertEqual(response.data["username"], original_username)

        # Verify username in database is UNCHANGED
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, original_username)

    # Optional: Add tests for updating email, last name, invalid data (e.g., bad email format)
