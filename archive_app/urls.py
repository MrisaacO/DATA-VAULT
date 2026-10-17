from django.urls import path

from . import views

app_name = "archive_app"

urlpatterns = [
    path("", views.archive_list, name="archive_list"),
    path("<int:pk>/archive/", views.archive_file, name="archive_file"),
    path("<int:pk>/unarchive/", views.unarchive_file, name="unarchive_file"),
]
