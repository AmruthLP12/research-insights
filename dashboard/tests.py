import os
from urllib.parse import quote
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from django.template import Context, Template
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from publications.models import Department, Journal, Publication, Author
from dashboard.templatetags.dashboard_tags import query_transform

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


class Batch1RoutingAndFunctionalDefectsTestCase(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.viewer = User.objects.create_user(
            username="test_viewer", password="password123", role="viewer"
        )
        self.client.login(username="test_viewer", password="password123")

        self.journal = Journal.objects.create(name="Physical Review Letters", impact_factor=9.1)
        self.department = Department.objects.create(code="PHY", name="Physics")

    # --- TASK-P1-01: Pagination Query Preservation ---
    def test_query_transform_preserves_multiple_filters_and_updates_page(self):
        request = self.rf.get("/dashboard/documents/?document_type=Journal+Article&department=1&search=raman&page=1")
        context = {"request": request}
        result = query_transform(context, page=3)
        self.assertIn("page=3", result)
        self.assertIn("document_type=Journal+Article", result)
        self.assertIn("department=1", result)
        self.assertIn("search=raman", result)

    def test_query_transform_preserves_repeated_query_params(self):
        request = self.rf.get("/dashboard/documents/?tag=alpha&tag=beta&page=1")
        context = {"request": request}
        result = query_transform(context, page=2)
        self.assertIn("page=2", result)
        self.assertIn("tag=alpha", result)
        self.assertIn("tag=beta", result)

    def test_query_transform_removes_empty_values(self):
        request = self.rf.get("/dashboard/documents/?search=raman&page=1")
        context = {"request": request}
        result = query_transform(context, search="")
        self.assertNotIn("search=", result)
        self.assertIn("page=1", result)

    def test_pagination_template_renders_preserved_query_params(self):
        items = list(range(1, 35))
        paginator = Paginator(items, 10)
        page_obj = paginator.page(2)
        request = self.rf.get("/dashboard/documents/?document_type=Conference+Paper&search=laser&ordering=-date_published&page=2")

        template = Template(
            '{% include "components/pagination.html" with page_obj=page_obj object_name="items" %}'
        )
        rendered = template.render(Context({"request": request, "page_obj": page_obj, "object_name": "items"}))

        # First page link
        self.assertIn("page=1", rendered)
        # Prev page link (page 1)
        self.assertIn("page=1", rendered)
        # Next page link (page 3)
        self.assertIn("page=3", rendered)
        # Last page link (page 4)
        self.assertIn("page=4", rendered)
        # Preserved query params
        self.assertIn("document_type=Conference+Paper", rendered)
        self.assertIn("search=laser", rendered)
        self.assertIn("ordering=-date_published", rendered)

    # --- TASK-P1-02: Document Types with Slashes ---
    def test_document_type_with_slashes_reverses_and_resolves(self):
        url = reverse("dashboard:document_type_detail", kwargs={"document_type": "Book/Book Chapter"})
        self.assertEqual(url, "/dashboard/document/Book/Book%20Chapter/")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Book/Book Chapter")

    def test_document_type_detail_filters_matching_publications(self):
        pub_book = Publication.objects.create(
            title="Quantum Gravity Handbook",
            document_type="Book/Book Chapter",
            date_published="2024-01-01",
            collaboration_type="National",
            journal=self.journal,
        )
        pub_article = Publication.objects.create(
            title="Quantum Gravity Paper",
            document_type="Journal Article",
            date_published="2024-02-01",
            collaboration_type="National",
            journal=self.journal,
        )

        url = reverse("dashboard:document_type_detail", kwargs={"document_type": "Book/Book Chapter"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quantum Gravity Handbook")
        self.assertNotContains(response, "Quantum Gravity Paper")

    def test_document_type_detail_invalid_type_returns_404(self):
        url = "/dashboard/document/NonExistentTypeX/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # --- TASK-P1-03: Author Routing for Mononyms & Primary Key ---
    def test_mononym_author_detail_by_primary_key(self):
        mononym = Author.objects.create(first_name="", last_name="Aryabhata", rri_role="Faculty")
        url = reverse("dashboard:author_detail", kwargs={"pk": mononym.pk})
        self.assertEqual(url, f"/dashboard/authors/{mononym.pk}/")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aryabhata")

    def test_author_detail_with_blank_first_name_by_pk(self):
        author = Author.objects.create(first_name="", last_name="Raman", rri_role="Faculty")
        url = reverse("dashboard:author_detail", kwargs={"pk": author.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Raman")

    def test_normal_author_resolves_by_pk_and_by_name(self):
        author = Author.objects.create(first_name="C. V.", last_name="Raman", rri_role="Faculty")
        # By PK
        url_pk = reverse("dashboard:author_detail", kwargs={"pk": author.pk})
        resp_pk = self.client.get(url_pk)
        self.assertEqual(resp_pk.status_code, 200)
        self.assertContains(resp_pk, "C. V. Raman")

        # By Name
        url_name = reverse("dashboard:author_detail", kwargs={"first_name": "C. V.", "last_name": "Raman"})
        resp_name = self.client.get(url_name)
        self.assertEqual(resp_name.status_code, 200)
        self.assertContains(resp_name, "C. V. Raman")

    def test_author_detail_nonexistent_pk_returns_404(self):
        url = reverse("dashboard:author_detail", kwargs={"pk": 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_author_detail_malformed_identifier_returns_404(self):
        response = self.client.get("/dashboard/authors/not-a-pk/")
        self.assertEqual(response.status_code, 404)

    # --- TASK-P1-04: Unassigned RRI Roles ---
    def test_rri_role_overview_handles_authors_with_unassigned_roles(self):
        author = Author.objects.create(first_name="Guest", last_name="Researcher", rri_role=None)
        pub = Publication.objects.create(
            title="Unassigned Role Paper",
            document_type="Journal Article",
            date_published="2024-03-01",
            collaboration_type="National",
            journal=self.journal,
        )
        pub.authors.add(author)

        response = self.client.get(reverse("dashboard:rri_role"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unassigned")
        self.assertContains(response, reverse("dashboard:rri_role_unassigned"))

    def test_rri_role_unassigned_detail_view(self):
        author = Author.objects.create(first_name="External", last_name="Scholar", rri_role="")
        pub = Publication.objects.create(
            title="External Paper",
            document_type="Journal Article",
            date_published="2024-04-01",
            collaboration_type="National",
            journal=self.journal,
        )
        pub.authors.add(author)

        url = reverse("dashboard:rri_role_unassigned")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unassigned")
        self.assertContains(response, "External Paper")

    def test_rri_role_named_detail_view(self):
        url = reverse("dashboard:rri_role_detail", kwargs={"role": "Faculty"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Faculty")

    def test_rri_role_invalid_route_returns_404(self):
        url = reverse("dashboard:rri_role_detail", kwargs={"role": "NonExistentRoleXYZ"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # --- TASK-P1-05: Enforce Valid Journal Identifiers ---
    def test_journal_detail_with_valid_integer_id(self):
        url = reverse("dashboard:journal_detail", kwargs={"journal_id": self.journal.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.journal.name)

    def test_journal_detail_nonexistent_integer_returns_404(self):
        url = reverse("dashboard:journal_detail", kwargs={"journal_id": 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_journal_detail_non_integer_url_returns_404(self):
        response = self.client.get("/dashboard/journal/None/")
        self.assertEqual(response.status_code, 404)

        response_str = self.client.get("/dashboard/journal/invalid-slug/")
        self.assertEqual(response_str.status_code, 404)

    def test_publications_with_null_journal_do_not_produce_none_links(self):
        Publication.objects.create(
            title="Standalone Monograph Without Journal",
            document_type="Miscellaneous Article",
            date_published="2024-05-01",
            collaboration_type="National",
            journal=None,
        )
        resp_journals = self.client.get(reverse("dashboard:journals"))
        self.assertEqual(resp_journals.status_code, 200)
        self.assertNotContains(resp_journals, "/dashboard/journal/None/")

        resp_impact = self.client.get(reverse("dashboard:impact"))
        self.assertEqual(resp_impact.status_code, 200)
        self.assertNotContains(resp_impact, "/dashboard/impact/None/")


@override_settings(DEBUG=False)
class Batch2FoundationAndSharedUITestCase(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(
            username="b2_viewer", password="password123", role="viewer"
        )
        self.journal = Journal.objects.create(name="Physical Review Letters", impact_factor=9.1)

    # --- TASK-P2-01: Base Template HTML Structure ---
    def test_base_template_has_single_html_document_structure(self):
        self.client.login(username="b2_viewer", password="password123")
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Verify exactly one doctype, html, head, body, and closing tags
        self.assertEqual(content.count("<!doctype html>"), 1)
        self.assertEqual(content.count("<html"), 1)
        self.assertEqual(content.count("</html>"), 1)
        self.assertEqual(content.count("<head>"), 1)
        self.assertEqual(content.count("</head>"), 1)
        self.assertEqual(content.count("<body"), 1)
        self.assertEqual(content.count("</body>"), 1)

        # Verify essential scripts in head
        self.assertIn("chart.min.js", content)
        self.assertIn("chart-theme.js", content)
        self.assertIn("alpine.min.js", content)
        self.assertIn("lucide.min.js", content)

    # --- TASK-P2-02: Authentication Layout Decoupled from Sidebar ---
    def test_anonymous_login_page_does_not_contain_dashboard_sidebar(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Verify sidebar element and dashboard navigation links are absent
        self.assertNotIn("<aside", content)
        self.assertNotIn('x-data="sidebarSetup()"', content)
        self.assertNotIn(reverse("dashboard:home"), content)
        self.assertNotIn(reverse("dashboard:trends"), content)

        # Verify login form and CSRF token are present
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, 'Research Insights')

    def test_anonymous_password_reset_pages_do_not_contain_sidebar(self):
        reset_urls = [
            reverse("accounts:password_reset"),
            reverse("accounts:password_reset_done"),
        ]
        for url in reset_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            content = response.content.decode("utf-8")
            self.assertNotIn("<aside", content)
            self.assertNotIn('x-data="sidebarSetup()"', content)
            self.assertNotIn(reverse("dashboard:home"), content)

    def test_authenticated_dashboard_still_displays_sidebar(self):
        self.client.login(username="b2_viewer", password="password123")
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("<aside", content)
        self.assertIn("Research Dashboard", content)
        self.assertIn('x-data="sidebarSetup()"', content)
        self.assertIn(reverse("dashboard:home"), content)

    # --- TASK-P2-03: Custom Error Templates ---
    def test_custom_404_template_renders_cleanly(self):
        response = self.client.get("/nonexistent-path-that-does-not-exist-404/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "404", status_code=404)
        self.assertContains(response, "Page Not Found", status_code=404)
        self.assertContains(response, reverse("publications:list"), status_code=404)
        # Verify no sensitive stack trace or paths
        self.assertNotContains(response, "Traceback", status_code=404)
        self.assertNotContains(response, "Exception", status_code=404)

    def test_custom_403_template_renders_cleanly(self):
        rendered = render_to_string("403.html", {"user": self.viewer})
        self.assertIn("403", rendered)
        self.assertIn("Access Denied", rendered)
        self.assertIn(reverse("publications:list"), rendered)
        self.assertNotIn("Traceback", rendered)

    def test_custom_500_template_renders_without_request_context(self):
        rendered = render_to_string("500.html", {})
        self.assertIn("500", rendered)
        self.assertIn("Server Error", rendered)
        self.assertIn(reverse("publications:list"), rendered)
        self.assertNotIn("Traceback", rendered)

    # --- TASK-P2-04: Filter Reset Behavior ---
    def test_documents_filter_reset_link_uses_request_path_without_query_params(self):
        self.client.login(username="b2_viewer", password="password123")
        url = reverse("dashboard:documents") + "?document_type=Journal+Article&search=physics&page=2"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Must not use href="."
        self.assertNotContains(response, 'href="."')
        # Must point to /dashboard/documents/ without any query params
        self.assertContains(response, f'href="{reverse("dashboard:documents")}"')

    def test_authors_filter_reset_link_uses_request_path(self):
        self.client.login(username="b2_viewer", password="password123")
        url = reverse("dashboard:authors") + "?search=raman&total_publications_gt=5"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, 'href="."')
        self.assertContains(response, f'href="{reverse("dashboard:authors")}"')

    # --- TASK-P2-05: Centralized Chart.js Visual Defaults ---
    def test_chart_theme_static_asset_exists_and_defines_defaults(self):
        theme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "js", "chart-theme.js")
        self.assertTrue(os.path.exists(theme_path), "static/js/chart-theme.js must exist")
        with open(theme_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("palette", content)
        self.assertIn("ChartTheme", content)
        self.assertIn("applyDefaults", content)
        self.assertIn("Inter", content)

    def test_dashboard_templates_consume_chart_theme(self):
        self.client.login(username="b2_viewer", password="password123")
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "chart-theme.js")
        self.assertContains(response, "ChartTheme.palette")
