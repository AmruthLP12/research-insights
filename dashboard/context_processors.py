# dashboard/context_processors.py

from django.urls import reverse


def dashboard_sidebar(request):
    return {
        "dashboard_sidebar": [
            {
                "title": "Analytics",
                "icon": "chart-bar",
                "items": [
                    {
                        "title": "Dashboard",
                        "url": reverse("dashboard:home"),
                        "url_name": "home",
                        "icon": "layout-dashboard",
                    },
                    {
                        "title": "Trends",
                        "url": reverse("dashboard:trends"),
                        "url_name": "trends",
                        "icon": "trending-up",
                    },
                    {
                        "title": "Impact Analysis",
                        "url": reverse("dashboard:impact"),
                        "url_name": "impact",
                        "icon": "activity",
                    },
                ],
            },
            {
                "title": "Publications",
                "icon": "book-open",
                "items": [
                    {
                        "title": "Document Types",
                        "url": reverse("dashboard:documents"),
                        "url_name": "documents",
                        "icon": "file-text",
                    },
                    {
                        "title": "Collaboration",
                        "url": reverse("dashboard:collaboration"),
                        "url_name": "collaboration",
                        "icon": "handshake",
                    },
                    {
                        "title": "Collaboration Types",
                        "url": reverse("dashboard:collaboration_types"),
                        "url_name": "collaboration_types",
                        "icon": "network",
                    },
                ],
            },
            {
                "title": "Management",
                "icon": "users",
                "items": [
                    {
                        "title": "Authors",
                        "url": reverse("dashboard:authors"),
                        "url_name": "authors",
                        "icon": "users",
                    },
                    {
                        "title": "Journals",
                        "url": reverse("dashboard:journals"),
                        "url_name": "journals",
                        "icon": "book",
                    },
                    {
                        "title": "Departments",
                        "url": reverse("dashboard:departments"),
                        "url_name": "departments",
                        "icon": "building",
                    },
                    {
                        "title": "RRI Roles",
                        "url": reverse("dashboard:rri_role"),
                        "url_name": "rri_role",
                        "icon": "badge-check",
                    },
                ],
            },
        ],
    }