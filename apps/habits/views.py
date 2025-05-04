from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Habit, HabitEntry
from .serializers import HabitEntrySerializer, HabitSerializer


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):  # type: ignore
        user = self.request.user
        queryset = Habit.objects.filter(user=user)

        is_archived_param = self.request.query_params.get("is_archived")  # type: ignore
        if is_archived_param is not None:
            if is_archived_param.lower() in ["true", "1"]:
                queryset = queryset.filter(archived_at__isnull=False)
            elif is_archived_param.lower() in ["false", "0"]:
                queryset = queryset.filter(archived_at__isnull=True)
        else:
            queryset = queryset.filter(archived_at__isnull=True)

        return queryset.order_by("name")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        habit = self.get_object()
        if habit.archived_at is None:
            habit.archived_at = timezone.now()
            habit.save()
        serializer = self.get_serializer(habit)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def unarchive(self, request, pk=None):
        habit = self.get_object()
        if habit.archived_at is not None:
            habit.archived_at = None
            habit.save()
        serializer = self.get_serializer(habit)
        return Response(serializer.data)


class HabitEntryViewSet(viewsets.ModelViewSet):
    serializer_class = HabitEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):  # type: ignore
        user = self.request.user
        queryset = HabitEntry.objects.filter(user=user)

        habit_id = self.request.query_params.get("habit_id")  # type: ignore
        if habit_id:
            queryset = queryset.filter(habit__id=habit_id)

        start_date = self.request.query_params.get("start_date")  # type: ignore
        end_date = self.request.query_params.get("end_date")  # type: ignore

        if start_date:
            queryset = queryset.filter(entry_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(entry_date__lte=end_date)

        specific_date = self.request.query_params.get("date")  # type: ignore
        if specific_date:
            queryset = queryset.filter(entry_date=specific_date)

        return queryset.order_by("-entry_date")

    def perform_create(self, serializer):
        habit_instance = serializer.validated_data["habit"]
        if habit_instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have permission to create this entry.")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context
