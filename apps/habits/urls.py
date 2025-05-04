from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HabitEntryViewSet, HabitViewSet

router = DefaultRouter()
router.register(r"habits", HabitViewSet, basename="habit")
router.register(r"entries", HabitEntryViewSet, basename="habitentry")

urlpatterns = [
    path("", include(router.urls)),
]
