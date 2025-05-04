from django.contrib import admin

from .models import Habit, HabitEntry


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "type", "created_at", "archived_at")
    search_fields = ("name", "user__username", "user__email", "description")
    list_filter = ("user", "type", "archived_at")


@admin.register(HabitEntry)
class HabitEntryAdmin(admin.ModelAdmin):
    list_display = ("habit", "user", "entry_date", "value", "created_at")
    list_filter = ("user", "entry_date", "habit__type")
    search_fields = ("habit__name", "user__username", "user__email", "notes")
    date_hierarchy = "entry_date"
