from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class PublicationsAccessControlTestCase(TestCase):
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
        self.wos_urls = [
            reverse("publications:wos_upload"),
            reverse("publications:wos_review"),
            reverse("publications:wos_save"),
            reverse("publications:wos_success"),
        ]

    def test_publications_list_is_public(self):
        # Anonymous users can access the publication catalog
        response = self.client.get(reverse("publications:list"))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_redirected_from_wos_endpoints(self):
        for url in self.wos_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                302,
                f"Expected redirect for anonymous access to {url}",
            )
            self.assertIn(reverse("accounts:login"), response.url)

    def test_viewer_role_forbidden_from_wos_endpoints(self):
        self.client.login(username="viewer", password="password123")
        for url in self.wos_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                403,
                f"Expected 403 Forbidden for viewer role on {url}",
            )

    def test_authorized_roles_can_access_wos_upload(self):
        # User role
        self.client.login(username="editor", password="password123")
        response = self.client.get(reverse("publications:wos_upload"))
        self.assertEqual(response.status_code, 200)

        # Admin role
        self.client.login(username="admin", password="password123")
        response = self.client.get(reverse("publications:wos_upload"))
        self.assertEqual(response.status_code, 200)

    def test_upload_button_visibility(self):
        upload_link = reverse("publications:wos_upload")

        # Anonymous user should not see upload button
        response = self.client.get(reverse("publications:list"))
        self.assertNotContains(response, upload_link)

        # Viewer role user should not see upload button
        self.client.login(username="viewer", password="password123")
        response = self.client.get(reverse("publications:list"))
        self.assertNotContains(response, upload_link)

        # User role user should see upload button
        self.client.login(username="editor", password="password123")
        response = self.client.get(reverse("publications:list"))
        self.assertContains(response, upload_link)
