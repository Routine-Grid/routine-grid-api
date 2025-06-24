from django.urls import path

from .views import UserProfileView, export_user_data

urlpatterns = [
    path("me/", UserProfileView.as_view(), name="user-profile"),
    path("me/export/", export_user_data, name="export-user-data"),
]
