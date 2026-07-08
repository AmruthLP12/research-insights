from django.urls import path
from . import views

app_name = "publications"

urlpatterns = [
    # 📄 Publications list (MAIN PAGE)
    path("", views.publications_list, name="list"),
    path("<int:pk>/", views.PublicationDetailView.as_view(), name="publication_detail1"),

    # ⬆ Web of Science workflow
    path("wos/upload/", views.wos_upload, name="wos_upload"),
    path("wos/review/", views.wos_review, name="wos_review"),
    path("wos/save/", views.wos_save, name="wos_save"),
    path("wos/success/", views.wos_success, name="wos_success"),
]
