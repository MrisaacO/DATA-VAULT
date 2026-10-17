from django.urls import path

from . import views

app_name = "notes"

urlpatterns = [
    path("", views.note_list, name="list"),
    path("new/", views.note_create, name="create"),
    path("new/in/<int:folder_pk>/", views.note_create, name="create_in_folder"),
    path("<int:pk>/", views.note_detail, name="detail"),
    path("<int:pk>/edit/", views.note_edit, name="edit"),
    path("<int:pk>/favourite/", views.note_toggle_favourite, name="toggle_favourite"),
    path("<int:pk>/delete/", views.note_delete, name="delete"),
    path("<int:pk>/restore/", views.note_restore, name="restore"),
    path("<int:pk>/delete-permanently/", views.note_permanent_delete, name="permanent_delete"),
]
