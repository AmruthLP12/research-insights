from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from publications.models import Publication

User = get_user_model()


class PublicationOwnershipTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="researcher", password="password123", role="user"
        )
        self.publication = Publication.objects.create(
            title="Quantum Hall Effect in Graphene",
            document_type="Journal Article",
            date_published="2023-01-01",
            collaboration_type="National",
            created_by=self.user,
        )

    def test_publication_created_by_set_null_on_user_delete(self):
        user_id = self.user.id
        pub_id = self.publication.id

        # Delete the user who created the publication
        self.user.delete()

        # The publication must NOT be deleted
        self.assertTrue(Publication.objects.filter(id=pub_id).exists())

        # The publication's created_by must now be NULL (None)
        self.publication.refresh_from_db()
        self.assertIsNone(self.publication.created_by)

    def test_publication_created_without_user(self):
        anon_pub = Publication.objects.create(
            title="Cosmological Observations",
            document_type="Journal Article",
            date_published="2023-02-01",
            collaboration_type="International",
            created_by=None,
        )
        self.assertIsNone(anon_pub.created_by)
        self.assertTrue(Publication.objects.filter(id=anon_pub.id).exists())


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
