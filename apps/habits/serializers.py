from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Habit, HabitEntry

User = get_user_model()


class HabitSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Habit
        fields = [
            "id",
            "user",
            "name",
            "description",
            "type",
            "created_at",
            "updated_at",
            "archived_at",
            "color",
            "goal_value",
            "goal_unit",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Name is required.")
        if len(value) < 3:
            raise serializers.ValidationError(
                "Name must be at least 3 characters long."
            )
        return value


class HabitEntrySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    habit = serializers.PrimaryKeyRelatedField(queryset=Habit.objects.all())
    habit_name = serializers.CharField(source="habit.name", read_only=True)

    class Meta:
        model = HabitEntry
        fields = [
            "id",
            "user",
            "habit",
            "habit_name",
            "entry_date",
            "value",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at", "habit_name"]

    def validate_habit(self, habit_instance):
        request_user = self.context["request"].user
        if habit_instance.user != request_user:
            raise serializers.ValidationError(
                "You can only create entries for your own habits."
            )
        if habit_instance.archived_at is not None:
            raise serializers.ValidationError(
                "Cannot create entries for archived habits."
            )
        return habit_instance

    def validate(self, data):  # type: ignore
        habit_instance = data.get("habit")
        value = data.get("value")

        if habit_instance and value is not None:
            if habit_instance.type == Habit.HabitType.SINGULAR and value != 1:
                raise serializers.ValidationError(
                    "Value for singular habits must be 1."
                )
            elif habit_instance.type == Habit.HabitType.TIMED and value <= 0:
                raise serializers.ValidationError(
                    "Value for timed habits must be greater than 0."
                )

        return data

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
