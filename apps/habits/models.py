from django.conf import settings
from django.db import models


# Create your models here.
class Habit(models.Model):
    class HabitType(models.TextChoices):
        SINGULAR = "singular", "Singular"
        TIMED = "timed", "Timed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(
        max_length=10,
        choices=HabitType.choices,
        default=HabitType.SINGULAR,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(blank=True, null=True, default=None)

    color = models.CharField(max_length=7, blank=True, null=True)
    goal_value = models.PositiveIntegerField(blank=True, null=True)
    goal_unit = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    class Meta:
        ordering = ["name"]


class HabitEntry(models.Model):
    habit = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habit_entries",
    )
    entry_date = models.DateField()

    value = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.habit.name} - {self.entry_date} ({self.value})"

    class Meta:
        ordering = ["-entry_date", "habit__name"]
        unique_together = [["habit", "entry_date"]]
        indexes = [models.Index(fields=["habit", "entry_date"])]
