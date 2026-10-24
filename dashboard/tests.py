from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from publications.models import Department, Journal

User = get_user_model()


class DashboardAuthenticationTestCase(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(
            username="viewer", password="password123", role="viewer"
        )
        self.department = Department.objects.create(code="PHY", name="Physics")
        self.journal = Journal.objects.create(name="Physical Review Letters", impact_factor=9.1)

        self.dashboard_urls = [
            reverse("dashboard:home"),
            reverse("dashboard:documents"),
            reverse("dashboard:document_type_detail", kwargs={"document_type": "Journal Article"}),
            reverse("dashboard:authors"),
            reverse("dashboard:author_detail", kwargs={"first_name": "John", "last_name": "Doe"}),
            reverse("dashboard:journals"),
            reverse("dashboard:journal_detail", kwargs={"journal_id": self.journal.pk}),
            reverse("dashboard:departments"),
            reverse("dashboard:department_detail", kwargs={"pk": self.department.pk}),
            reverse("dashboard:collaboration"),
            reverse("dashboard:collaboration_detail", kwargs={"collaboration_type": "National"}),
            reverse("dashboard:trends"),
            reverse("dashboard:trend_year_detail", kwargs={"year": 2024}),
            reverse("dashboard:impact"),
            reverse("dashboard:impact_detail", kwargs={"journal_id": self.journal.pk}),
            reverse("dashboard:rri_role"),
            reverse("dashboard:rri_role_detail", kwargs={"role": "Faculty"}),
            reverse("dashboard:country_collaboration"),
            reverse("dashboard:country_collaboration_detail", kwargs={"country": "India"}),
            reverse("dashboard:institution_collaboration"),
            reverse("dashboard:institution_collaboration_detail", kwargs={"institution": "RRI"}),
        ]

    def test_total_view_count(self):
        # Explicitly verify all 21 views are tracked
        self.assertEqual(len(self.dashboard_urls), 21)

    def test_anonymous_users_redirected_to_login(self):
        for url in self.dashboard_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                302,
                f"Expected redirect for anonymous access to {url}",
            )
            self.assertIn(
                reverse("accounts:login"),
                response.url,
                f"Expected redirect to login page for {url}",
            )

    def test_authenticated_users_can_access_dashboard(self):
        self.client.login(username="viewer", password="password123")
        for url in self.dashboard_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                200,
                f"Expected 200 OK for authenticated access to {url}",
            )
