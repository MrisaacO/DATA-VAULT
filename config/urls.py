from django.contrib import admin
from django.urls import include, path

# NOTE: media/ is deliberately NOT wired up with django.conf.urls.static's
# static() helper here, even in DEBUG. Per Section 16.1 and 25.2 of the
# Development Guide, a private file must always be requested by its
# application ID through an authenticated, ownership-checked view --
# never by a raw /media/<path> URL that would work for anyone who guessed
# or leaked it. storage_app.views.file_download / file_preview stream the
# bytes instead, in both development and production.

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("folders/", include("folders.urls")),
    path("notes/", include("notes.urls")),
    path("files/", include("storage_app.urls")),
    path("search/", include("search_app.urls")),
    path("archive/", include("archive_app.urls")),
]
