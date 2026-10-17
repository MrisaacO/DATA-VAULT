from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.VaultLoginView.as_view(), name="login"),
    path("logout/", views.VaultLogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path(
        "profile/password/",
        views.VaultPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "profile/password/done/",
        views.VaultPasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
]
