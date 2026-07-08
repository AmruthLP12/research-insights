from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardHomeView.as_view(), name="home"),
    path("documents/", views.DocumentTypesView.as_view(), name="documents"),
    path("authors/", views.authors_view, name="authors"),
    path("journals/", views.journals_view, name="journals"),
    path("departments/", views.departments_view, name="departments"),
    path("collaboration/", views.CollaborationView.as_view(), name="collaboration"),
    path("trends/", views.TrendsView.as_view(), name="trends"),
    path("impact/", views.ImpactView.as_view(), name="impact"),
    path("collaboration/type/", views.CollaborationTypesView.as_view(), name="collaboration_types"),
    path("rri/role/", views.rri_role_view, name="rri_role"),
]


