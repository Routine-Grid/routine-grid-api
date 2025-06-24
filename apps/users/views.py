# apps/users/views.py

import csv
import json
from datetime import datetime

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.habits.models import Habit, HabitEntry

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


@extend_schema(
    tags=["Users"],
    summary="Export user data",
    description="Export all user data (profile, habits, and entries) in CSV or JSON format.",
    parameters=[
        OpenApiParameter(
            name="format",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Export format: 'csv' or 'json'",
            required=True,
            enum=["csv", "json"],
        ),
    ],
    responses={
        200: {
            "description": "Data export file",
            "content": {
                "text/csv": {"schema": {"type": "string"}},
                "application/json": {"schema": {"type": "object"}},
            },
        },
        400: {"description": "Invalid format parameter"},
    },
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def export_user_data(request):
    """
    Export all user data including profile, habits, and entries.

    Supports CSV and JSON formats. CSV exports separate files for habits and entries,
    while JSON exports everything in a single structured file.
    """
    export_format = request.query_params.get("format", "").lower()

    if export_format not in ["csv", "json"]:
        return Response({"error": "Invalid format. Use 'csv' or 'json'."}, status=400)

    user = request.user

    # Get user data
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "date_joined": user.date_joined.isoformat() if user.date_joined else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }

    # Get habits data (both active and archived)
    habits = Habit.objects.filter(user=user).order_by("created_at")
    habits_data = []
    for habit in habits:
        habits_data.append(
            {
                "id": habit.id,
                "name": habit.name,
                "description": habit.description,
                "type": habit.type,
                "color": habit.color,
                "goal_value": habit.goal_value,
                "goal_unit": habit.goal_unit,
                "created_at": habit.created_at.isoformat(),
                "updated_at": habit.updated_at.isoformat(),
                "archived_at": habit.archived_at.isoformat()
                if habit.archived_at
                else None,
            }
        )

    # Get entries data
    entries = (
        HabitEntry.objects.filter(user=user)
        .select_related("habit")
        .order_by("entry_date")
    )
    entries_data = []
    for entry in entries:
        entries_data.append(
            {
                "id": entry.id,
                "habit_id": entry.habit.id,
                "habit_name": entry.habit.name,
                "entry_date": entry.entry_date.isoformat(),
                "value": entry.value,
                "notes": entry.notes,
                "created_at": entry.created_at.isoformat(),
                "updated_at": entry.updated_at.isoformat(),
            }
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if export_format == "json":
        # JSON export - single file with all data
        export_data = {
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "format": "json",
                "version": "1.0",
            },
            "user": user_data,
            "habits": habits_data,
            "entries": entries_data,
            "summary": {
                "total_habits": len(habits_data),
                "total_entries": len(entries_data),
                "active_habits": len([h for h in habits_data if not h["archived_at"]]),
                "archived_habits": len([h for h in habits_data if h["archived_at"]]),
            },
        }

        response = HttpResponse(
            json.dumps(export_data, indent=2), content_type="application/json"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="routine_grid_export_{timestamp}.json"'
        )

    else:  # CSV export
        # CSV export - habits and entries in a single CSV with clear sections
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="routine_grid_export_{timestamp}.csv"'
        )

        writer = csv.writer(response)

        # Write export info
        writer.writerow(["# Routine Grid Data Export"])
        writer.writerow(["# Exported at:", datetime.now().isoformat()])
        writer.writerow(["# User:", user.username])
        writer.writerow([])

        # Write user information
        writer.writerow(["## USER INFORMATION"])
        writer.writerow(["Field", "Value"])
        writer.writerow(["ID", user_data["id"]])
        writer.writerow(["Username", user_data["username"]])
        writer.writerow(["Email", user_data["email"]])
        writer.writerow(["First Name", user_data["first_name"]])
        writer.writerow(["Last Name", user_data["last_name"]])
        writer.writerow(["Date Joined", user_data["date_joined"]])
        writer.writerow(["Last Login", user_data["last_login"]])
        writer.writerow([])

        # Write habits
        writer.writerow(["## HABITS"])
        if habits_data:
            habit_headers = [
                "ID",
                "Name",
                "Description",
                "Type",
                "Color",
                "Goal Value",
                "Goal Unit",
                "Created At",
                "Updated At",
                "Archived At",
            ]
            writer.writerow(habit_headers)

            for habit in habits_data:
                writer.writerow(
                    [
                        habit["id"],
                        habit["name"],
                        habit["description"] or "",
                        habit["type"],
                        habit["color"] or "",
                        habit["goal_value"] or "",
                        habit["goal_unit"] or "",
                        habit["created_at"],
                        habit["updated_at"],
                        habit["archived_at"] or "",
                    ]
                )
        else:
            writer.writerow(["No habits found"])

        writer.writerow([])

        # Write entries
        writer.writerow(["## HABIT ENTRIES"])
        if entries_data:
            entry_headers = [
                "ID",
                "Habit ID",
                "Habit Name",
                "Entry Date",
                "Value",
                "Notes",
                "Created At",
                "Updated At",
            ]
            writer.writerow(entry_headers)

            for entry in entries_data:
                writer.writerow(
                    [
                        entry["id"],
                        entry["habit_id"],
                        entry["habit_name"],
                        entry["entry_date"],
                        entry["value"],
                        entry["notes"] or "",
                        entry["created_at"],
                        entry["updated_at"],
                    ]
                )
        else:
            writer.writerow(["No entries found"])

    return response


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
