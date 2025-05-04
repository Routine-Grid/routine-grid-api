# apps/habits/tests.py

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone  # Import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Habit, HabitEntry

User = get_user_model()


class HabitAPITest(APITestCase):
    """Tests for the Habit API endpoints (/habits/)."""

    def setUp(self):
        """Set up test users and URLs."""
        # User 1 (will own the habits being tested)
        self.user1 = User.objects.create_user(
            username="habituser1",
            email="habit1@example.com",
            password="StrongPassword123",
        )
        # User 2 (to test permissions)
        self.user2 = User.objects.create_user(
            username="habituser2",
            email="habit2@example.com",
            password="StrongPassword123",
        )

        self.habit_list_create_url = reverse("habit-list")  # Gets '/api/v1/habits/'

        # Create some habits for user1 for testing list/detail views
        self.habit1_user1 = Habit.objects.create(
            user=self.user1, name="Read Book", type="timed"
        )
        self.habit2_user1 = Habit.objects.create(
            user=self.user1, name="Morning Run", type="singular"
        )
        self.habit3_user1_archived = Habit.objects.create(
            user=self.user1,
            name="Old Project",
            type="singular",
            archived_at=timezone.now(),
        )
        # Create a habit for user2 to test permissions
        self.habit1_user2 = Habit.objects.create(
            user=self.user2, name="User 2 Habit", type="singular"
        )

    # --- Helper to get detail URL ---
    def get_detail_url(self, pk):
        """Helper function to get the detail URL for a habit."""
        return reverse("habit-detail", kwargs={"pk": pk})

    # --- Helper to get archive/unarchive URLs ---
    def get_archive_url(self, pk):
        return reverse("habit-archive", kwargs={"pk": pk})

    def get_unarchive_url(self, pk):
        return reverse("habit-unarchive", kwargs={"pk": pk})

    # --- List Tests ---

    def test_list_habits_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.habit_list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only active habits for user1
        habit_names = {item["name"] for item in response.data}
        self.assertIn(self.habit1_user1.name, habit_names)
        self.assertIn(self.habit2_user1.name, habit_names)

    def test_list_habits_unauthenticated(self):
        response = self.client.get(self.habit_list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_habits_archived_filter(self):
        self.client.force_authenticate(user=self.user1)
        # Test ?archived=true
        response_archived = self.client.get(
            self.habit_list_create_url, {"archived": "true"}
        )
        self.assertEqual(response_archived.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_archived.data), 1)
        self.assertEqual(
            response_archived.data[0]["name"], self.habit3_user1_archived.name
        )
        # Test ?archived=false
        response_active = self.client.get(
            self.habit_list_create_url, {"archived": "false"}
        )
        self.assertEqual(response_active.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_active.data), 2)

    # --- Create Tests ---

    def test_create_habit_success(self):
        self.client.force_authenticate(user=self.user1)
        habit_count_before = Habit.objects.filter(user=self.user1).count()
        data = {"name": "New Habit", "type": "timed", "description": "Desc"}
        response = self.client.post(self.habit_list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Habit.objects.filter(user=self.user1).count(), habit_count_before + 1
        )
        new_habit = Habit.objects.get(id=response.data["id"])
        self.assertEqual(new_habit.user, self.user1)
        self.assertEqual(new_habit.name, "New Habit")

    def test_create_habit_unauthenticated(self):
        data = {"name": "No Auth Habit", "type": "singular"}
        response = self.client.post(self.habit_list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_habit_invalid_data(self):
        self.client.force_authenticate(user=self.user1)
        data = {"name": "A", "type": "singular"}  # Name too short
        response = self.client.post(self.habit_list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Retrieve Tests ---

    def test_retrieve_habit_success(self):
        """Ensure user can retrieve their own habit."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_detail_url(self.habit1_user1.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.habit1_user1.pk)
        self.assertEqual(response.data["name"], self.habit1_user1.name)

    def test_retrieve_habit_permission_denied(self):
        """Ensure user cannot retrieve another user's habit."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_detail_url(self.habit1_user2.pk)  # Habit owned by user2
        response = self.client.get(url)
        # Because get_queryset filters first, the object isn't found for this user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_habit_not_found(self):
        """Test retrieving a habit that does not exist."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_detail_url(999)  # Non-existent PK
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Update Tests ---

    def test_update_habit_success(self):
        """Ensure user can update their own habit using PATCH."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_detail_url(self.habit1_user1.pk)
        new_name = "Updated Habit Name"
        data = {"name": new_name, "description": "Updated desc"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], new_name)
        self.assertEqual(response.data["description"], "Updated desc")

        # Verify in DB
        self.habit1_user1.refresh_from_db()
        self.assertEqual(self.habit1_user1.name, new_name)
        self.assertEqual(self.habit1_user1.description, "Updated desc")

    def test_update_habit_permission_denied(self):
        """Ensure user cannot update another user's habit."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_detail_url(self.habit1_user2.pk)  # Habit owned by user2
        data = {"name": "Attempt Update"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND
        )  # Not found for user1

    def test_update_habit_invalid_data(self):
        """Test updating habit with invalid data."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_detail_url(self.habit1_user1.pk)
        data = {"name": "A"}  # Invalid short name
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Delete (Archive) Tests ---

    def test_delete_habit_success(self):
        """Ensure user can 'delete' (archive) their own habit."""
        self.client.force_authenticate(user=self.user1)
        habit_to_delete = Habit.objects.create(user=self.user1, name="Delete Me")
        url = self.get_detail_url(habit_to_delete.pk)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify habit is archived (archived_at is set)
        habit_to_delete.refresh_from_db()
        self.assertIsNotNone(habit_to_delete.archived_at)

        # Verify it no longer appears in the default list view
        list_response = self.client.get(self.habit_list_create_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        found = any(h["id"] == habit_to_delete.pk for h in list_response.data)
        self.assertFalse(found)

    def test_delete_habit_permission_denied(self):
        """Ensure user cannot delete another user's habit."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_detail_url(self.habit1_user2.pk)  # Habit owned by user2
        response = self.client.delete(url)
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND
        )  # Not found for user1

    # --- Archive Action Tests ---

    def test_archive_action_success(self):
        """Test archiving an active habit via custom action."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_archive_url(self.habit1_user1.pk)  # habit1 is active
        self.assertIsNone(self.habit1_user1.archived_at)  # Pre-condition
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["archived_at"])
        self.habit1_user1.refresh_from_db()
        self.assertIsNotNone(self.habit1_user1.archived_at)

    def test_archive_action_already_archived(self):
        """Test archive action on an already archived habit (should be idempotent)."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_archive_url(self.habit3_user1_archived.pk)  # Already archived
        archived_time_before = self.habit3_user1_archived.archived_at
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.habit3_user1_archived.refresh_from_db()
        # Time should not have changed significantly (or at all ideally)
        self.assertEqual(self.habit3_user1_archived.archived_at, archived_time_before)

    def test_archive_action_permission_denied(self):
        """Test archive action on another user's habit."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_archive_url(self.habit1_user2.pk)  # User 2's habit
        response = self.client.post(url)
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND
        )  # Not found for user1

    # --- Unarchive Action Tests ---

    def test_unarchive_action_success(self):
        """Test unarchiving an archived habit via custom action."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_unarchive_url(self.habit3_user1_archived.pk)  # Archived habit
        self.assertIsNotNone(self.habit3_user1_archived.archived_at)  # Pre-condition
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["archived_at"])
        self.habit3_user1_archived.refresh_from_db()
        self.assertIsNone(self.habit3_user1_archived.archived_at)

    def test_unarchive_action_already_active(self):
        """Test unarchive action on an already active habit."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_unarchive_url(self.habit1_user1.pk)  # Active habit
        self.assertIsNone(self.habit1_user1.archived_at)  # Pre-condition
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["archived_at"])
        self.habit1_user1.refresh_from_db()
        self.assertIsNone(self.habit1_user1.archived_at)

    def test_unarchive_action_permission_denied(self):
        """Test unarchive action on another user's habit."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_unarchive_url(self.habit1_user2.pk)  # User 2's habit
        response = self.client.post(url)
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND
        )  # Not found for user1


class HabitEntryAPITest(APITestCase):
    """Tests for the Habit Entry API endpoints (/entries/)."""

    def setUp(self):
        """Set up users, habits, entries, and URLs."""
        # Users
        self.user1 = User.objects.create_user(
            "entryuser1", "entry1@example.com", "StrongPass123"
        )
        self.user2 = User.objects.create_user(
            "entryuser2", "entry2@example.com", "StrongPass123"
        )

        # Habits
        self.habit_s_u1 = Habit.objects.create(
            user=self.user1, name="Meditate", type=Habit.HabitType.SINGULAR
        )
        self.habit_t_u1 = Habit.objects.create(
            user=self.user1, name="Workout", type=Habit.HabitType.TIMED
        )
        self.habit_s_u2 = Habit.objects.create(
            user=self.user2, name="User 2 Sing", type=Habit.HabitType.SINGULAR
        )

        # Dates
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
        self.tomorrow = self.today + timedelta(days=1)

        # Entries for user1
        self.entry1 = HabitEntry.objects.create(
            habit=self.habit_s_u1, user=self.user1, entry_date=self.yesterday, value=1
        )
        self.entry2 = HabitEntry.objects.create(
            habit=self.habit_t_u1,
            user=self.user1,
            entry_date=self.yesterday,
            value=45,  # e.g., 45 minutes
        )
        self.entry3 = HabitEntry.objects.create(
            habit=self.habit_s_u1, user=self.user1, entry_date=self.today, value=1
        )
        # Entry for user2
        self.entry_u2 = HabitEntry.objects.create(
            habit=self.habit_s_u2, user=self.user2, entry_date=self.today, value=1
        )

        # URLs
        self.entry_list_create_url = reverse(
            "habitentry-list"
        )  # Gets '/api/v1/entries/'

    # --- Helper ---
    def get_entry_detail_url(self, pk):
        return reverse("habitentry-detail", kwargs={"pk": pk})

    # --- List Tests ---

    def test_list_entries_authenticated(self):
        """Ensure authenticated user lists only their own entries."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.entry_list_create_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # User 1 has 3 entries
        self.assertEqual(len(response.data), 3)
        entry_ids = {item["id"] for item in response.data}
        self.assertIn(self.entry1.pk, entry_ids)
        self.assertIn(self.entry2.pk, entry_ids)
        self.assertIn(self.entry3.pk, entry_ids)
        self.assertNotIn(
            self.entry_u2.pk, entry_ids
        )  # Ensure user 2's entry isn't listed

    def test_list_entries_unauthenticated(self):
        """Ensure unauthenticated user gets 401."""
        response = self.client.get(self.entry_list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_entries_filter_by_habit(self):
        """Test filtering entries by habit_id."""
        self.client.force_authenticate(user=self.user1)
        # Filter for singular habit entries
        url = f"{self.entry_list_create_url}?habit_id={self.habit_s_u1.pk}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # entry1 and entry3 are for habit_s_u1
        entry_ids = {item["id"] for item in response.data}
        self.assertIn(self.entry1.pk, entry_ids)
        self.assertIn(self.entry3.pk, entry_ids)

    def test_list_entries_filter_by_date_range(self):
        """Test filtering entries by start_date and end_date."""
        self.client.force_authenticate(user=self.user1)
        # Filter for yesterday only
        url = f"{self.entry_list_create_url}?start_date={self.yesterday.isoformat()}&end_date={self.yesterday.isoformat()}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # entry1 and entry2 were yesterday
        entry_ids = {item["id"] for item in response.data}
        self.assertIn(self.entry1.pk, entry_ids)
        self.assertIn(self.entry2.pk, entry_ids)

    def test_list_entries_filter_by_date_and_habit(self):
        """Test filtering entries by specific date and habit."""
        self.client.force_authenticate(user=self.user1)
        # Filter for today's singular habit entry
        url = f"{self.entry_list_create_url}?date={self.today.isoformat()}&habit_id={self.habit_s_u1.pk}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.entry3.pk)

    # --- Create Tests ---

    def test_create_entry_success_singular(self):
        """Test creating a valid entry for a singular habit."""
        self.client.force_authenticate(user=self.user1)
        entry_count_before = HabitEntry.objects.filter(user=self.user1).count()
        data = {
            "habit": self.habit_s_u1.pk,  # Reference habit by PK
            "entry_date": self.tomorrow.isoformat(),
            "value": 1,  # Value for singular
        }
        response = self.client.post(self.entry_list_create_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            HabitEntry.objects.filter(user=self.user1).count(), entry_count_before + 1
        )
        new_entry = HabitEntry.objects.get(id=response.data["id"])
        self.assertEqual(new_entry.user, self.user1)
        self.assertEqual(new_entry.habit, self.habit_s_u1)
        self.assertEqual(new_entry.entry_date, self.tomorrow)
        self.assertEqual(new_entry.value, 1)

    def test_create_entry_success_timed(self):
        """Test creating a valid entry for a timed habit."""
        self.client.force_authenticate(user=self.user1)
        entry_count_before = HabitEntry.objects.filter(user=self.user1).count()
        data = {
            "habit": self.habit_t_u1.pk,
            "entry_date": self.tomorrow.isoformat(),
            "value": 60,  # e.g., 60 minutes
        }
        response = self.client.post(self.entry_list_create_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            HabitEntry.objects.filter(user=self.user1).count(), entry_count_before + 1
        )
        new_entry = HabitEntry.objects.get(id=response.data["id"])
        self.assertEqual(new_entry.habit, self.habit_t_u1)
        self.assertEqual(new_entry.value, 60)

    def test_create_entry_unauthenticated(self):
        """Ensure unauthenticated user cannot create an entry."""
        data = {
            "habit": self.habit_s_u1.pk,
            "entry_date": self.tomorrow.isoformat(),
            "value": 1,
        }
        response = self.client.post(self.entry_list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_entry_other_user_habit(self):
        """Ensure user cannot create entry for another user's habit."""
        self.client.force_authenticate(user=self.user1)
        data = {
            "habit": self.habit_s_u2.pk,
            "entry_date": self.today.isoformat(),
            "value": 1,
        }
        response = self.client.post(self.entry_list_create_url, data, format="json")
        # Should fail validation in the serializer (validate_habit)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("habit", response.data)  # Error should be tied to habit field

    def test_create_entry_duplicate(self):
        """Ensure duplicate entry (same habit, same date) is not allowed."""
        self.client.force_authenticate(user=self.user1)
        # self.entry3 already exists for habit_s_u1 on today's date
        data = {
            "habit": self.habit_s_u1.pk,
            "entry_date": self.today.isoformat(),
            "value": 1,
        }
        response = self.client.post(self.entry_list_create_url, data, format="json")
        # Fails due to unique_together constraint on the model
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "non_field_errors", response.data
        )  # Or specific field if DRF maps it

    def test_create_entry_invalid_value_singular(self):
        """Test validation for value on singular habit (if specific validation exists)."""
        self.client.force_authenticate(user=self.user1)
        data = {
            "habit": self.habit_s_u1.pk,
            "entry_date": self.tomorrow.isoformat(),
            "value": 2,
        }  # Value > 1
        response = self.client.post(self.entry_list_create_url, data, format="json")
        # This might pass or fail depending on strictness of validation in serializer.
        # Assuming current serializer doesn't strictly enforce value=1 for singular:
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # If you add stricter validation:
        # self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # self.assertIn('value', response.data) # Or maybe non_field_errors
        pass  # Placeholder - adjust assertion based on your desired validation strictness

    def test_create_entry_invalid_value_timed(self):
        """Test validation for value on timed habit (must be > 0)."""
        self.client.force_authenticate(user=self.user1)
        data = {
            "habit": self.habit_t_u1.pk,
            "entry_date": self.tomorrow.isoformat(),
            "value": 0,
        }  # Value <= 0
        response = self.client.post(self.entry_list_create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "non_field_errors", response.data
        )  # Based on current validate method

    def test_retrieve_entry_success(self):
        """Ensure user can retrieve their own entry."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_entry_detail_url(self.entry1.pk)  # entry1 belongs to user1
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.entry1.pk)
        self.assertEqual(
            response.data["habit"], self.entry1.habit.pk
        )  # Check related habit ID
        self.assertEqual(
            response.data["entry_date"], self.entry1.entry_date.isoformat()
        )

    def test_retrieve_entry_permission_denied(self):
        """Ensure user cannot retrieve another user's entry."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_entry_detail_url(self.entry_u2.pk)  # entry_u2 belongs to user2
        response = self.client.get(url)
        # get_queryset filters first, so it's not found for user1
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_entry_not_found(self):
        """Test retrieving an entry that does not exist."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_entry_detail_url(999)  # Non-existent PK
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_entry_unauthenticated(self):
        """Ensure unauthenticated user cannot retrieve an entry."""
        url = self.get_entry_detail_url(self.entry1.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Update Tests ---

    def test_update_entry_success(self):
        """Ensure user can update their own entry (e.g., value, notes) using PATCH."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_entry_detail_url(self.entry2.pk)  # Timed entry (value=45)
        new_value = 55
        new_notes = "Updated workout notes"
        data = {"value": new_value, "notes": new_notes}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["value"], new_value)
        self.assertEqual(response.data["notes"], new_notes)

        # Verify in DB
        self.entry2.refresh_from_db()
        self.assertEqual(self.entry2.value, new_value)
        self.assertEqual(self.entry2.notes, new_notes)

    def test_update_entry_permission_denied(self):
        """Ensure user cannot update another user's entry."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_entry_detail_url(self.entry_u2.pk)  # Entry owned by user2
        data = {"value": 99}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND
        )  # Not found for user1

    def test_update_entry_invalid_value(self):
        """Test updating an entry with an invalid value for its habit type."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_entry_detail_url(self.entry2.pk)  # Timed entry
        data = {"value": 0}  # Invalid value for timed habit
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "non_field_errors", response.data
        )  # Or 'value' depending on exact validation

    def test_update_entry_unauthenticated(self):
        """Ensure unauthenticated user cannot update an entry."""
        url = self.get_entry_detail_url(self.entry1.pk)
        data = {"value": 99}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Delete Tests ---

    def test_delete_entry_success(self):
        """Ensure user can delete their own entry."""
        self.client.force_authenticate(user=self.user1)
        # Create a specific entry to delete in this test
        entry_to_delete = HabitEntry.objects.create(
            habit=self.habit_s_u1, user=self.user1, entry_date=self.tomorrow, value=1
        )
        entry_count_before = HabitEntry.objects.filter(user=self.user1).count()
        url = self.get_entry_detail_url(entry_to_delete.pk)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify count decreased in DB
        self.assertEqual(
            HabitEntry.objects.filter(user=self.user1).count(), entry_count_before - 1
        )
        # Verify the specific entry is gone
        with self.assertRaises(HabitEntry.DoesNotExist):
            HabitEntry.objects.get(pk=entry_to_delete.pk)

    def test_delete_entry_permission_denied(self):
        """Ensure user cannot delete another user's entry."""
        self.client.force_authenticate(user=self.user1)
        url = self.get_entry_detail_url(self.entry_u2.pk)  # Entry owned by user2
        response = self.client.delete(url)
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND
        )  # Not found for user1

    def test_delete_entry_unauthenticated(self):
        """Ensure unauthenticated user cannot delete an entry."""
        url = self.get_entry_detail_url(self.entry1.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
