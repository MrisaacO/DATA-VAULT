from django.urls import path

from . import views

app_name = "storage_app"

urlpatterns = [
    path("upload/", views.upload, name="upload"),
    path("upload/in/<int:folder_pk>/", views.upload, name="upload_to_folder"),
    path("favourites/", views.favourites, name="favourites"),
    path("recycle-bin/", views.recycle_bin, name="recycle_bin"),
    path("<int:pk>/", views.file_detail, name="detail"),
    path("<int:pk>/download/", views.file_download, name="download"),
    path("<int:pk>/preview/", views.file_preview, name="preview"),
    path("<int:pk>/rename/", views.file_rename, name="rename"),
    path("<int:pk>/tags/", views.file_tags, name="tags"),
    path("<int:pk>/move/", views.file_move, name="move"),
    path("<int:pk>/favourite/", views.file_toggle_favourite, name="toggle_favourite"),
    path("<int:pk>/delete/", views.file_delete, name="delete"),
    path("<int:pk>/restore/", views.file_restore, name="restore"),
    path("<int:pk>/delete-permanently/", views.file_permanent_delete, name="permanent_delete"),
]
