from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class DashboardAuthenticationTestCase(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(
            username="viewer", password="password123", role="viewer"
        )
        self.dashboard_urls = [
            reverse("dashboard:home"),
            reverse("dashboard:documents"),
            reverse("dashboard:authors"),
            reverse("dashboard:journals"),
            reverse("dashboard:departments"),
            reverse("dashboard:collaboration"),
            reverse("dashboard:trends"),
            reverse("dashboard:impact"),
            reverse("dashboard:rri_role"),
            reverse("dashboard:country_collaboration"),
            reverse("dashboard:institution_collaboration"),
        ]

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
