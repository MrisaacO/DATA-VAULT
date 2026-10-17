from django.urls import path

from . import views

app_name = "folders"

urlpatterns = [
    path("", views.folder_detail, name="root"),
    path("new/", views.folder_create, name="create"),
    path("<int:pk>/", views.folder_detail, name="detail"),
    path("<int:pk>/new/", views.folder_create, name="create_child"),
    path("<int:pk>/rename/", views.folder_rename, name="rename"),
    path("<int:pk>/move/", views.folder_move, name="move"),
    path("<int:pk>/delete/", views.folder_delete, name="delete"),
    path("<int:pk>/restore/", views.folder_restore, name="restore"),
    path("<int:pk>/delete-permanently/", views.folder_permanent_delete, name="permanent_delete"),
]
