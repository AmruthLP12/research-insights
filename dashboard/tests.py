from urllib.parse import quote
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from publications.models import Department, Journal, Publication

User = get_user_model()


class DashboardAuthenticationTestCase(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(
            username="viewer", password="password123", role="viewer"
        )
        self.editor = User.objects.create_user(
            username="editor", password="password123", role="user"
        )
        self.admin = User.objects.create_user(
            username="admin", password="password123", role="admin"
        )
        self.staff_user = User.objects.create_user(
            username="staff_user", password="password123", role="viewer", is_staff=True
        )
        self.superuser = User.objects.create_superuser(
            username="superuser", password="password123", role="viewer"
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

    def test_anonymous_get_redirects_to_login_with_next_param(self):
        for url in self.dashboard_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                302,
                f"Expected redirect for anonymous GET to {url}",
            )
            login_url = reverse("accounts:login")
            self.assertIn(
                login_url,
                response.url,
                f"Expected redirect to login page for {url}",
            )
            self.assertIn(
                f"?next={quote(url)}",
                response.url,
                f"Expected redirect url to preserve next parameter for {url}",
            )

    def test_anonymous_post_redirects_to_login(self):
        for url in self.dashboard_urls:
            response = self.client.post(url, {})
            self.assertEqual(
                response.status_code,
                302,
                f"Expected redirect for anonymous POST to {url}",
            )
            self.assertIn(
                reverse("accounts:login"),
                response.url,
                f"Expected redirect to login page on POST {url}",
            )

    def test_anonymous_unsupported_methods_redirect_to_login(self):
        for url in self.dashboard_urls:
            put_resp = self.client.put(url, {})
            self.assertEqual(
                put_resp.status_code,
                302,
                f"Expected redirect for anonymous PUT to {url}",
            )
            delete_resp = self.client.delete(url)
            self.assertEqual(
                delete_resp.status_code,
                302,
                f"Expected redirect for anonymous DELETE to {url}",
            )

    def test_authenticated_viewer_role_access(self):
        self.client.login(username="viewer", password="password123")
        for url in self.dashboard_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                200,
                f"Expected 200 OK for viewer role on {url}",
            )

    def test_authenticated_user_role_access(self):
        self.client.login(username="editor", password="password123")
        for url in self.dashboard_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                200,
                f"Expected 200 OK for user role on {url}",
            )

    def test_authenticated_admin_role_access(self):
        self.client.login(username="admin", password="password123")
        for url in self.dashboard_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                200,
                f"Expected 200 OK for admin role on {url}",
            )

    def test_staff_and_superuser_access(self):
        # Staff user
        self.client.login(username="staff_user", password="password123")
        for url in self.dashboard_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                200,
                f"Expected 200 OK for staff user on {url}",
            )

        # Superuser
        self.client.login(username="superuser", password="password123")
        for url in self.dashboard_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                200,
                f"Expected 200 OK for superuser on {url}",
            )

    def test_authenticated_post_rejected_with_405_method_not_allowed(self):
        self.client.login(username="viewer", password="password123")
        for url in self.dashboard_urls:
            response = self.client.post(url, {})
            self.assertEqual(
                response.status_code,
                405,
                f"Expected 405 Method Not Allowed for POST to read-only dashboard endpoint {url}",
            )

    def test_authenticated_unsupported_methods_rejected_with_405(self):
        self.client.login(username="viewer", password="password123")
        for url in self.dashboard_urls:
            put_resp = self.client.put(url, {})
            self.assertEqual(
                put_resp.status_code,
                405,
                f"Expected 405 Method Not Allowed for PUT to {url}",
            )
            delete_resp = self.client.delete(url)
            self.assertEqual(
                delete_resp.status_code,
                405,
                f"Expected 405 Method Not Allowed for DELETE to {url}",
            )

    def test_root_redirect_behavior(self):
        # Anonymous root request redirects to dashboard:home then to login
        response = self.client.get(reverse("root"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:home"))

        # Following redirect leads to login with next=/dashboard/
        follow_resp = self.client.get(reverse("root"), follow=True)
        self.assertRedirects(
            follow_resp,
            f"{reverse('accounts:login')}?next={quote(reverse('dashboard:home'))}",
        )

        # Authenticated user root request redirects to dashboard:home with 200
        self.client.login(username="viewer", password="password123")
        auth_follow_resp = self.client.get(reverse("root"), follow=True)
        self.assertRedirects(auth_follow_resp, reverse("dashboard:home"))
        self.assertEqual(auth_follow_resp.status_code, 200)

    def test_public_routes_remain_accessible_without_authentication(self):
        pub = Publication.objects.create(
            title="Publicly Accessible Paper",
            document_type="Journal Article",
            date_published="2023-01-01",
            collaboration_type="National",
            journal=self.journal,
        )

        # Public catalog list
        list_resp = self.client.get(reverse("publications:list"))
        self.assertEqual(list_resp.status_code, 200)
        self.assertContains(list_resp, "Publicly Accessible Paper")

        # Public publication detail
        detail_resp = self.client.get(
            reverse("publications:publication_detail", kwargs={"pk": pub.pk})
        )
        self.assertEqual(detail_resp.status_code, 200)
        self.assertContains(detail_resp, "Publicly Accessible Paper")

    def test_detail_views_return_404_on_invalid_identifiers(self):
        self.client.login(username="viewer", password="password123")
        invalid_urls = [
            reverse("dashboard:journal_detail", kwargs={"journal_id": 99999}),
            reverse("dashboard:department_detail", kwargs={"pk": 99999}),
            reverse("dashboard:impact_detail", kwargs={"journal_id": 99999}),
        ]
        for url in invalid_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                404,
                f"Expected 404 Not Found on invalid identifier for {url}",
            )

    def test_dashboard_handles_publications_with_null_creator(self):
        Publication.objects.create(
            title="Publication With No Creator",
            document_type="Journal Article",
            date_published="2023-01-01",
            collaboration_type="National",
            journal=self.journal,
            created_by=None,
        )

        self.client.login(username="viewer", password="password123")
        home_resp = self.client.get(reverse("dashboard:home"))
        self.assertEqual(home_resp.status_code, 200)

        docs_resp = self.client.get(reverse("dashboard:documents"))
        self.assertEqual(docs_resp.status_code, 200)

        trends_resp = self.client.get(reverse("dashboard:trends"))
        self.assertEqual(trends_resp.status_code, 200)
