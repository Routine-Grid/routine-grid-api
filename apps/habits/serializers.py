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
    habit = serializers.CharField(source="habit.name", read_only=True)

    class Meta:
        model = HabitEntry
        fields = [
            "id",
            "user",
            "habit",
            "habit_nameentry_date",
            "value",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at", "habit_name"]

    def validate(self, attrs):
        habit = attrs.get("habit", getattr(self.instance, "habit", None))
        value = attrs.get("value", getattr(self.instance, "value", None))

        if habit and value is not None:
            if habit.type == Habit.HabitType.SINGULAR and value != 1:
                raise serializers.ValidationError(
                    "Singular habits can only have a value of 1."
                )
            if habit.type == Habit.HabitType.TIMED and value <= 0:
                raise serializers.ValidationError(
                    "Timed habits must have a positive value."
                )
        request_user = self.context["request"].user
        if habit and habit.user != request_user:
            raise serializers.ValidationError(
                "You do not have permission to modify this habit entry."
            )

        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
