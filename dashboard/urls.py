from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardHomeView.as_view(), name="home"),
    path("documents/", views.DocumentTypesView.as_view(), name="documents"),
    path("authors/", views.AuthorsView.as_view(), name="authors"),
    path("authors/<first_name>/<last_name>/", views.AuthorDetailView.as_view(), name="author_detail"),
    path("journals/", views.JournalsView.as_view(), name="journals"),
    path("departments/", views.DepartmentsView.as_view(), name="departments"),
    path("collaboration/", views.CollaborationView.as_view(), name="collaboration"),
    path("trends/", views.TrendsView.as_view(), name="trends"),
    path("impact/", views.ImpactView.as_view(), name="impact"),
    path("rri/role/", views.RRIRoleView.as_view(), name="rri_role"),
    path("country/collaboration/", views.CountryCollaborationView.as_view(), name="country_collaboration"),
    path("institution/collaboration/", views.InstitutionCollaborationView.as_view(), name="institution_collaboration"),
]


