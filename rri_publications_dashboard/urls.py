from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings


def root_redirect(request):
    return redirect("dashboard:home")


urlpatterns = [
    path("", root_redirect, name="root"),
    path("admin/", admin.site.urls),
    path("publications/", include("publications.urls")),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
]

if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
