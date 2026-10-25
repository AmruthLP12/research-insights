import json
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from publications.models import (
    Affiliation,
    Author,
    AuthorAffiliation,
    Citation,
    Department,
    Journal,
    Publication,
)

User = get_user_model()


class PublicationRetentionAndIntegrityTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="researcher", password="password123", role="user"
        )
        self.department = Department.objects.create(code="PHY", name="Physics")
        self.journal = Journal.objects.create(name="Physical Review Letters", impact_factor=9.1)
        self.author = Author.objects.create(first_name="Raman", last_name="Chandrasekhara", rri_role="Faculty")
        self.affiliation = Affiliation.objects.create(
            name="Raman Research Institute, Bangalore", country="India"
        )

        self.publication = Publication.objects.create(
            title="Quantum Hall Effect in Graphene",
            document_type="Journal Article",
            date_published="2023-01-01",
            collaboration_type="National",
            journal=self.journal,
            created_by=self.user,
        )
        self.publication.departments.add(self.department)
        self.publication.authors.add(self.author)

        self.auth_aff = AuthorAffiliation.objects.create(
            author=self.author,
            affiliation=self.affiliation,
            publication=self.publication,
            is_primary=True,
        )
        self.citation = Citation.objects.create(
            publication=self.publication,
            year=2023,
            wos_citations=42,
            gs_citations=65,
        )

    def test_publication_created_by_set_null_on_user_delete(self):
        pub_id = self.publication.id

        # Delete the user who created the publication
        self.user.delete()

        # The publication must NOT be deleted
        self.assertTrue(Publication.objects.filter(id=pub_id).exists())

        # The publication's created_by must now be NULL (None)
        self.publication.refresh_from_db()
        self.assertIsNone(self.publication.created_by)

        # Confirm all other relationships remain intact
        self.assertEqual(self.publication.journal, self.journal)
        self.assertEqual(list(self.publication.authors.all()), [self.author])
        self.assertEqual(list(self.publication.departments.all()), [self.department])
        self.assertEqual(list(self.publication.author_affiliations.all()), [self.auth_aff])
        self.assertEqual(list(self.publication.yearly_citations.all()), [self.citation])

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

    def test_public_views_render_publications_with_null_creator(self):
        self.user.delete()
        self.publication.refresh_from_db()

        # List view handles null creator
        list_resp = self.client.get(reverse("publications:list"))
        self.assertEqual(list_resp.status_code, 200)
        self.assertContains(list_resp, "Quantum Hall Effect in Graphene")

        # Detail view handles null creator
        detail_resp = self.client.get(
            reverse("publications:publication_detail", kwargs={"pk": self.publication.pk})
        )
        self.assertEqual(detail_resp.status_code, 200)
        self.assertContains(detail_resp, "Quantum Hall Effect in Graphene")


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
        self.staff_viewer = User.objects.create_user(
            username="staff_viewer", password="password123", role="viewer", is_staff=True
        )
        self.superuser = User.objects.create_superuser(
            username="super_viewer", password="password123", role="viewer"
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

    def test_anonymous_post_wos_endpoints_redirects(self):
        post_urls = [
            reverse("publications:wos_upload"),
            reverse("publications:wos_save"),
        ]
        for url in post_urls:
            response = self.client.post(url, {})
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("accounts:login"), response.url)

    def test_viewer_role_forbidden_from_wos_endpoints(self):
        self.client.login(username="viewer", password="password123")
        for url in self.wos_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                403,
                f"Expected 403 Forbidden for viewer role on GET {url}",
            )

    def test_viewer_role_forbidden_from_wos_post_endpoints(self):
        self.client.login(username="viewer", password="password123")
        post_urls = [
            reverse("publications:wos_upload"),
            reverse("publications:wos_save"),
        ]
        for url in post_urls:
            response = self.client.post(url, {})
            self.assertEqual(
                response.status_code,
                403,
                f"Expected 403 Forbidden for viewer role on POST {url}",
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

    def test_staff_and_superuser_can_access_wos_endpoints(self):
        # Staff override
        self.client.login(username="staff_viewer", password="password123")
        response = self.client.get(reverse("publications:wos_upload"))
        self.assertEqual(response.status_code, 200)

        # Superuser override
        self.client.login(username="super_viewer", password="password123")
        response = self.client.get(reverse("publications:wos_upload"))
        self.assertEqual(response.status_code, 200)

    def test_wos_save_get_redirects_to_review(self):
        self.client.login(username="editor", password="password123")
        response = self.client.get(reverse("publications:wos_save"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("publications:wos_review"))

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


class WoSIngestionWorkflowTestCase(TestCase):
    def setUp(self):
        self.editor = User.objects.create_user(
            username="editor", password="password123", role="user"
        )
        self.client.login(username="editor", password="password123")

    def _create_wos_tsv(self, records):
        headers = ["TI", "SO", "DT", "PY", "VL", "IS", "BP", "EP", "AR", "ARTN", "DI", "AF", "C1"]
        lines = ["\t".join(headers)]
        for r in records:
            row = [
                str(r.get("TI", "")),
                str(r.get("SO", "")),
                str(r.get("DT", "")),
                str(r.get("PY", "")),
                str(r.get("VL", "")),
                str(r.get("IS", "")),
                str(r.get("BP", "")),
                str(r.get("EP", "")),
                str(r.get("AR", "")),
                str(r.get("ARTN", "")),
                str(r.get("DI", "")),
                str(r.get("AF", "")),
                str(r.get("C1", "")),
            ]
            lines.append("\t".join(row))
        return "\n".join(lines).encode("utf-8")

    def test_upload_valid_wos_file_success(self):
        tsv_bytes = self._create_wos_tsv([
            {
                "TI": "Topological Phases in Bismuth",
                "SO": "Physical Review B",
                "DT": "Journal Article",
                "PY": "2023",
                "VL": "107",
                "IS": "4",
                "BP": "045101",
                "EP": "045108",
                "DI": "10.1103/PhysRevB.107.045101",
                "AF": "Chandrasekhara, Raman; Sharma, Priya",
                "C1": "[Chandrasekhara, Raman] Raman Research Institute, Bangalore, India; [Sharma, Priya] IISc, Bangalore, India",
            }
        ])
        uploaded_file = SimpleUploadedFile("savedrecs.txt", tsv_bytes, content_type="text/plain")

        response = self.client.post(
            reverse("publications:wos_upload"),
            {"wos_file": uploaded_file},
        )
        self.assertRedirects(response, reverse("publications:wos_review"))

        session = self.client.session
        self.assertIn("wos_records", session)
        self.assertEqual(len(session["wos_records"]), 1)
        self.assertEqual(session["wos_index"], 0)

        record = session["wos_records"][0]
        self.assertEqual(record["publication"]["title"], "Topological Phases in Bismuth")
        self.assertEqual(record["publication"]["journal_name"], "Physical Review B")
        self.assertEqual(record["publication"]["date_published"], "2023-01-01")
        self.assertEqual(len(record["authors"]), 2)

    def test_upload_empty_file_fails_with_message(self):
        empty_file = SimpleUploadedFile("empty.txt", b"", content_type="text/plain")

        response = self.client.post(
            reverse("publications:wos_upload"),
            {"wos_file": empty_file},
        )
        self.assertRedirects(response, reverse("publications:wos_upload"))
        self.assertNotIn("wos_records", self.client.session)

    def test_upload_without_file_renders_page(self):
        response = self.client.post(reverse("publications:wos_upload"), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Upload")

    def test_upload_file_with_only_headers_fails(self):
        headers_only = "TI\tSO\tDT\tPY\tVL\tIS\tBP\tEP\tAR\tARTN\tDI\tAF\tC1\n".encode("utf-8")
        file_obj = SimpleUploadedFile("headers_only.txt", headers_only, content_type="text/plain")

        response = self.client.post(
            reverse("publications:wos_upload"),
            {"wos_file": file_obj},
        )
        self.assertRedirects(response, reverse("publications:wos_upload"))
        self.assertNotIn("wos_records", self.client.session)

    def test_review_page_renders_with_parsed_initial_data(self):
        session = self.client.session
        session["wos_records"] = [
            {
                "publication": {
                    "title": "Quantum Spin Hall Effect",
                    "journal_name": "Nature Physics",
                    "document_type": "Journal Article",
                    "date_published": "2023-01-01",
                    "volume": "19",
                    "issue": "2",
                    "page_number": "120-128",
                    "article_number": "120",
                    "doi": "10.1038/s41567-023-001",
                    "collaboration_type": "National",
                },
                "authors": [
                    {
                        "first_name": "Raman",
                        "last_name": "Chandrasekhara",
                        "affiliations_json": [
                            {"name": "Raman Research Institute, Bangalore", "country": "India", "is_primary": True}
                        ],
                    },
                    {
                        "first_name": "David",
                        "last_name": "Smith",
                        "affiliations_json": [
                            {"name": "Oxford University", "country": "UK", "is_primary": True}
                        ],
                    },
                ],
            }
        ]
        session["wos_index"] = 0
        session.save()

        response = self.client.get(reverse("publications:wos_review"))
        self.assertEqual(response.status_code, 200)

        # Journal is created or retrieved during review
        self.assertTrue(Journal.objects.filter(name="Nature Physics").exists())

        # Check template context
        self.assertIn("pub_form", response.context)
        self.assertIn("author_formset", response.context)
        self.assertEqual(response.context["index"], 1)
        self.assertEqual(response.context["total"], 1)

        # Check RRI role pre-population: RRI author has blank choice, External author has 'External'
        formset = response.context["author_formset"]
        self.assertEqual(formset.forms[0].initial["rri_role"], "")
        self.assertEqual(formset.forms[1].initial["rri_role"], "External")

    def test_review_page_redirects_when_session_empty_or_exhausted(self):
        # Empty session
        response = self.client.get(reverse("publications:wos_review"))
        self.assertRedirects(response, reverse("publications:wos_upload"))

        # Index >= total records
        session = self.client.session
        session["wos_records"] = [{"publication": {}, "authors": []}]
        session["wos_index"] = 1
        session.save()

        response = self.client.get(reverse("publications:wos_review"))
        self.assertRedirects(response, reverse("publications:wos_upload"))

    def test_save_valid_record_persists_publication_and_associations(self):
        session = self.client.session
        session["wos_records"] = [
            {
                "publication": {"title": "Photonic Crystals"},
                "authors": [{"first_name": "Raman", "last_name": "C"}],
            }
        ]
        session["wos_index"] = 0
        session.save()

        journal = Journal.objects.create(name="Optics Letters")
        post_data = {
            "document_type": "Journal Article",
            "date_published": "2023-05-15",
            "title": "Photonic Crystals in 2D",
            "journal": journal.id,
            "volume": "48",
            "issue": "10",
            "page_number": "2500-2503",
            "article_number": "2500",
            "doi": "10.1364/OL.48.002500",
            "collaboration_type": "National",
            # Author FormSet
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-first_name": "Raman",
            "form-0-last_name": "Chandrasekhara",
            "form-0-rri_role": "Faculty",
            "form-0-affiliations_json": json.dumps([
                {"name": "Raman Research Institute", "country": "India"}
            ]),
        }

        response = self.client.post(reverse("publications:wos_save"), post_data)
        self.assertRedirects(response, reverse("publications:wos_success"))

        # Verify DB persistence
        pub = Publication.objects.get(title="Photonic Crystals in 2D")
        self.assertEqual(pub.created_by, self.editor)
        self.assertEqual(pub.journal, journal)
        self.assertEqual(pub.volume, "48")
        self.assertEqual(pub.page_number, "2500-2503")
        self.assertEqual(pub.article_number, "2500")

        # Author and Affiliations
        self.assertEqual(pub.authors.count(), 1)
        author = pub.authors.first()
        self.assertEqual(author.first_name, "Raman")
        self.assertEqual(author.last_name, "Chandrasekhara")

        self.assertEqual(pub.author_affiliations.count(), 1)
        author_aff = pub.author_affiliations.first()
        self.assertEqual(author_aff.affiliation.name, "Raman Research Institute")
        self.assertEqual(author_aff.affiliation.country, "India")

        # Session was cleared
        self.assertNotIn("wos_records", self.client.session)
        self.assertNotIn("wos_index", self.client.session)

    def test_save_multi_record_file_advances_index_until_finished(self):
        session = self.client.session
        session["wos_records"] = [
            {"publication": {"title": "Paper One"}, "authors": []},
            {"publication": {"title": "Paper Two"}, "authors": []},
        ]
        session["wos_index"] = 0
        session.save()

        # Save record 0
        data_1 = {
            "document_type": "Journal Article",
            "date_published": "2023-01-01",
            "title": "Paper One",
            "collaboration_type": "National",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        }
        resp1 = self.client.post(reverse("publications:wos_save"), data_1)
        self.assertRedirects(resp1, reverse("publications:wos_review"))
        self.assertEqual(self.client.session["wos_index"], 1)
        self.assertEqual(Publication.objects.count(), 1)

        # Save record 1 (final)
        data_2 = {
            "document_type": "Journal Article",
            "date_published": "2023-02-01",
            "title": "Paper Two",
            "collaboration_type": "International",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        }
        resp2 = self.client.post(reverse("publications:wos_save"), data_2)
        self.assertRedirects(resp2, reverse("publications:wos_success"))
        self.assertNotIn("wos_records", self.client.session)
        self.assertEqual(Publication.objects.count(), 2)

    def test_save_invalid_form_rolls_back_and_preserves_session(self):
        session = self.client.session
        session["wos_records"] = [
            {"publication": {"title": "Incomplete Record"}, "authors": []}
        ]
        session["wos_index"] = 0
        session.save()

        # Missing required title and date_published
        invalid_data = {
            "document_type": "Journal Article",
            "title": "",
            "collaboration_type": "National",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        }

        response = self.client.post(reverse("publications:wos_save"), invalid_data)
        self.assertRedirects(response, reverse("publications:wos_review"))

        # Database must not contain any new publication or author
        self.assertEqual(Publication.objects.count(), 0)
        self.assertEqual(Author.objects.count(), 0)

        # Session index must remain 0
        self.assertEqual(self.client.session["wos_index"], 0)

    def test_save_deduplicates_journals_and_affiliations(self):
        journal = Journal.objects.create(name="Physical Review B")
        aff = Affiliation.objects.create(name="Raman Research Institute", country="India")

        session = self.client.session
        session["wos_records"] = [{"publication": {}, "authors": []}]
        session["wos_index"] = 0
        session.save()

        post_data = {
            "document_type": "Journal Article",
            "date_published": "2023-03-01",
            "title": "Deduplication Test Publication",
            "journal": journal.id,
            "collaboration_type": "National",
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-first_name": "Raman",
            "form-0-last_name": "C",
            "form-0-rri_role": "Faculty",
            "form-0-affiliations_json": json.dumps([
                {"name": "Raman Research Institute", "country": "India"}
            ]),
        }

        self.client.post(reverse("publications:wos_save"), post_data)

        # Journal and Affiliation must not duplicate
        self.assertEqual(Journal.objects.filter(name="Physical Review B").count(), 1)
        self.assertEqual(Affiliation.objects.filter(name="Raman Research Institute", country="India").count(), 1)


class PublicPublicationPagesTestCase(TestCase):
    def test_publication_list_empty_database(self):
        response = self.client.get(reverse("publications:list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["publication_count"], 0)
        self.assertEqual(response.context["publication_total_impact"], 0)
        self.assertEqual(response.context["publication_average_impact"], 0)
        self.assertEqual(len(response.context["page_obj"]), 0)

    def test_publication_list_pagination(self):
        # Create 15 publications
        for i in range(15):
            Publication.objects.create(
                title=f"Publication Number {i:02d}",
                document_type="Journal Article",
                date_published=f"2023-01-{i+1:02d}",
                collaboration_type="National",
            )

        # Page 1 has 10
        resp1 = self.client.get(reverse("publications:list"))
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(len(resp1.context["page_obj"]), 10)

        # Page 2 has 5
        resp2 = self.client.get(reverse("publications:list") + "?page=2")
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(len(resp2.context["page_obj"]), 5)

    def test_publication_list_search_and_filters(self):
        journal_nature = Journal.objects.create(name="Nature", impact_factor=50.0)
        journal_prb = Journal.objects.create(name="Physical Review B", impact_factor=3.5)

        pub1 = Publication.objects.create(
            title="Superconductivity in Graphene",
            document_type="Journal Article",
            date_published="2023-01-01",
            collaboration_type="National",
            journal=journal_nature,
        )
        pub2 = Publication.objects.create(
            title="Cosmological Dark Energy",
            document_type="Book/Book Chapter",
            date_published="2023-06-01",
            collaboration_type="International",
            journal=journal_prb,
        )

        # Search by title keyword
        resp_search = self.client.get(reverse("publications:list") + "?search=Superconductivity")
        self.assertContains(resp_search, pub1.title)
        self.assertNotContains(resp_search, pub2.title)

        # Filter by document_type
        resp_doc = self.client.get(reverse("publications:list") + "?document_type=Book%2FBook+Chapter")
        self.assertContains(resp_doc, pub2.title)
        self.assertNotContains(resp_doc, pub1.title)

        # Filter by collaboration_type
        resp_collab = self.client.get(reverse("publications:list") + "?collaboration_type=International")
        self.assertContains(resp_collab, pub2.title)
        self.assertNotContains(resp_collab, pub1.title)

        # Ordering
        resp_ord = self.client.get(reverse("publications:list") + "?ordering=title")
        self.assertEqual(resp_ord.status_code, 200)
        pubs = list(resp_ord.context["page_obj"])
        self.assertEqual(pubs[0].title, "Cosmological Dark Energy")
        self.assertEqual(pubs[1].title, "Superconductivity in Graphene")

    def test_publication_detail_view_success(self):
        journal = Journal.objects.create(name="Science", impact_factor=45.0)
        dept = Department.objects.create(code="ASTRO", name="Astronomy")
        author = Author.objects.create(first_name="Subrahmanyan", last_name="Chandrasekhar", rri_role="External")
        aff = Affiliation.objects.create(name="University of Chicago", country="USA")

        pub = Publication.objects.create(
            title="The Mathematical Theory of Black Holes",
            document_type="Book/Book Chapter",
            date_published="2023-01-01",
            collaboration_type="International",
            journal=journal,
            volume="1",
            issue="1",
            doi="10.1093/acprof:oso/999",
        )
        pub.departments.add(dept)
        pub.authors.add(author)
        AuthorAffiliation.objects.create(
            author=author,
            affiliation=aff,
            publication=pub,
        )
        Citation.objects.create(
            publication=pub,
            year=2023,
            wos_citations=100,
            gs_citations=250,
        )

        response = self.client.get(reverse("publications:publication_detail", kwargs={"pk": pub.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, pub.title)
        self.assertContains(response, journal.name)
        self.assertContains(response, author.last_name)
        self.assertContains(response, dept.name)
        self.assertContains(response, aff.name)

    def test_publication_detail_view_not_found(self):
        response = self.client.get(reverse("publications:publication_detail", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, 404)

    def test_publication_detail_view_minimal_metadata(self):
        pub = Publication.objects.create(
            title="Minimal Paper Without Optional Fields",
            document_type="Journal Article",
            date_published="2023-01-01",
            collaboration_type="National",
            created_by=None,
        )
        response = self.client.get(reverse("publications:publication_detail", kwargs={"pk": pub.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, pub.title)


class WoSUploadSecurityAndLimitsTestCase(TestCase):
    """
    Test suite for Web of Science upload security, file size boundaries,
    batch record limits, file type validation, encoding, and safe error handling.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="wos_uploader", password="password123", role="user"
        )
        self.client.force_login(self.user)

    def _generate_wos_tsv(self, records: list[dict], extra_padding: int = 0) -> bytes:
        headers = ["PT", "TI", "SO", "DT", "PY", "VL", "IS", "BP", "EP", "DI", "AF", "C1"]
        lines = ["\t".join(headers)]
        for r in records:
            row = [
                r.get("PT", "J"),
                r.get("TI", "Title"),
                r.get("SO", "Journal"),
                r.get("DT", "Article"),
                r.get("PY", "2023"),
                r.get("VL", "1"),
                r.get("IS", "1"),
                r.get("BP", "10"),
                r.get("EP", "20"),
                r.get("DI", "10.1000/123"),
                r.get("AF", "Raman, C"),
                r.get("C1", "[Raman, C] Raman Research Institute, Bangalore, India"),
            ]
            lines.append("\t".join(row))

        base_content = "\n".join(lines) + "\n"
        if extra_padding > 0:
            base_content += "# " + ("x" * (extra_padding - 3)) + "\n"
        return base_content.encode("utf-8")

    def test_upload_file_size_boundary_below_limit(self):
        """Files immediately below the 5 MB limit (5 MB - 100 bytes) are accepted."""
        target_size = 5 * 1024 * 1024 - 100
        headers = "PT\tTI\tSO\tDT\tPY\tAF\tC1\n"
        row_prefix = "J\tValid Paper Below Limit\tNature\tArticle\t2023\tAuthor, A\t[Author, A] RRI, Bangalore, India "
        row_suffix = "\n"
        current_len = len((headers + row_prefix + row_suffix).encode("utf-8"))
        padding_needed = target_size - current_len
        tsv_content = (headers + row_prefix + ("x" * padding_needed) + row_suffix).encode("utf-8")
        self.assertEqual(len(tsv_content), target_size)

        uploaded_file = SimpleUploadedFile("wos_below.txt", tsv_content, content_type="text/plain")
        response = self.client.post(
            reverse("publications:wos_upload"),
            {"wos_file": uploaded_file},
        )
        self.assertRedirects(response, reverse("publications:wos_review"))
        self.assertIn("wos_records", self.client.session)
        self.assertEqual(len(self.client.session["wos_records"]), 1)

    def test_upload_file_size_boundary_at_limit(self):
        """Files exactly at the 5 MB limit (5 MB) are accepted."""
        target_size = 5 * 1024 * 1024
        headers = "PT\tTI\tSO\tDT\tPY\tAF\tC1\n"
        row_prefix = "J\tValid Paper At Limit\tNature\tArticle\t2023\tAuthor, A\t[Author, A] RRI, Bangalore, India "
        row_suffix = "\n"
        current_len = len((headers + row_prefix + row_suffix).encode("utf-8"))
        padding_needed = target_size - current_len
        tsv_content = (headers + row_prefix + ("x" * padding_needed) + row_suffix).encode("utf-8")
        self.assertEqual(len(tsv_content), target_size)

        uploaded_file = SimpleUploadedFile("wos_at_limit.txt", tsv_content, content_type="text/plain")
        response = self.client.post(
            reverse("publications:wos_upload"),
            {"wos_file": uploaded_file},
        )
        self.assertRedirects(response, reverse("publications:wos_review"))
        self.assertIn("wos_records", self.client.session)
        self.assertEqual(len(self.client.session["wos_records"]), 1)

    def test_upload_file_size_boundary_above_limit_rejected(self):
        """Files immediately above the 5 MB limit (5 MB + 1 byte) are rejected before parsing."""
        target_size = 5 * 1024 * 1024 + 1
        headers = "PT\tTI\tSO\tDT\tPY\tAF\tC1\n"
        row_prefix = "J\tOversized Paper\tNature\tArticle\t2023\tAuthor, A\t[Author, A] RRI, Bangalore, India "
        row_suffix = "\n"
        current_len = len((headers + row_prefix + row_suffix).encode("utf-8"))
        padding_needed = target_size - current_len
        tsv_content = (headers + row_prefix + ("x" * padding_needed) + row_suffix).encode("utf-8")
        self.assertEqual(len(tsv_content), target_size)

        uploaded_file = SimpleUploadedFile("wos_oversized.txt", tsv_content, content_type="text/plain")
        response = self.client.post(
            reverse("publications:wos_upload"),
            {"wos_file": uploaded_file},
            follow=True,
        )
        self.assertRedirects(response, reverse("publications:wos_upload"))
        self.assertNotIn("wos_records", self.client.session)
        self.assertContains(response, "exceeds the maximum allowed size of 5 MB")

    @override_settings(MAX_WOS_FILE_SIZE=1024)
    def test_upload_file_size_custom_setting_boundary(self):
        """Custom MAX_WOS_FILE_SIZE setting enforces boundary correctly."""
        headers = "PT\tTI\tSO\tDT\tPY\tAF\tC1\n"
        row_prefix = "J\tBoundary\tNature\tArticle\t2023\tA\t[A] RRI "
        row_suffix = "\n"
        current_len = len((headers + row_prefix + row_suffix).encode("utf-8"))

        # Exactly 1024 bytes -> accepted
        content_1024 = (headers + row_prefix + ("x" * (1024 - current_len)) + row_suffix).encode("utf-8")
        self.assertEqual(len(content_1024), 1024)
        file_1024 = SimpleUploadedFile("exact_1024.txt", content_1024, content_type="text/plain")
        resp = self.client.post(reverse("publications:wos_upload"), {"wos_file": file_1024})
        self.assertRedirects(resp, reverse("publications:wos_review"))

        # Clean session
        session = self.client.session
        session.pop("wos_records", None)
        session.pop("wos_index", None)
        session.save()

        # 1025 bytes -> rejected
        content_1025 = (headers + row_prefix + ("x" * (1025 - current_len)) + row_suffix).encode("utf-8")
        self.assertEqual(len(content_1025), 1025)
        file_1025 = SimpleUploadedFile("exceed_1025.txt", content_1025, content_type="text/plain")
        resp = self.client.post(reverse("publications:wos_upload"), {"wos_file": file_1025}, follow=True)
        self.assertRedirects(resp, reverse("publications:wos_upload"))
        self.assertNotIn("wos_records", self.client.session)
        self.assertContains(resp, "exceeds the maximum allowed size")

    def test_upload_invalid_file_extension_rejected(self):
        """Disallowed extensions (.pdf, .csv, .exe, .bin) are rejected before parsing."""
        tsv_bytes = b"PT\tTI\tSO\nJ\tTest\tJournal\n"
        for bad_filename in ["records.pdf", "records.csv", "records.exe", "records.bin"]:
            with self.subTest(filename=bad_filename):
                file_obj = SimpleUploadedFile(bad_filename, tsv_bytes, content_type="text/plain")
                response = self.client.post(
                    reverse("publications:wos_upload"),
                    {"wos_file": file_obj},
                    follow=True,
                )
                self.assertRedirects(response, reverse("publications:wos_upload"))
                self.assertNotIn("wos_records", self.client.session)
                self.assertContains(response, "Invalid file format")

    def test_upload_valid_tsv_extension_accepted(self):
        """Files with .tsv extension are accepted."""
        tsv_content = b"PT\tTI\tSO\tDT\tPY\tAF\nJ\tTSV Paper\tScience\tArticle\t2023\tAuthor, T\n"
        file_obj = SimpleUploadedFile("records.tsv", tsv_content, content_type="text/tab-separated-values")
        response = self.client.post(
            reverse("publications:wos_upload"),
            {"wos_file": file_obj},
        )
        self.assertRedirects(response, reverse("publications:wos_review"))
        self.assertIn("wos_records", self.client.session)
        self.assertEqual(self.client.session["wos_records"][0]["publication"]["title"], "TSV Paper")

    def test_upload_disallowed_mime_type_rejected(self):
        """Files with dangerous or non-text MIME types are rejected before parsing."""
        tsv_bytes = b"PT\tTI\tSO\nJ\tTest\tJournal\n"
        for bad_mime in ["application/pdf", "image/png", "application/zip", "application/x-sh"]:
            with self.subTest(mime=bad_mime):
                file_obj = SimpleUploadedFile("records.txt", tsv_bytes, content_type=bad_mime)
                response = self.client.post(
                    reverse("publications:wos_upload"),
                    {"wos_file": file_obj},
                    follow=True,
                )
                self.assertRedirects(response, reverse("publications:wos_upload"))
                self.assertNotIn("wos_records", self.client.session)
                self.assertContains(response, "Invalid file type")

    def test_upload_utf8_with_bom_parsed_successfully(self):
        """Windows UTF-8 export with Byte Order Mark (\\ufeff) is parsed cleanly."""
        bom_content = "\ufeffPT\tTI\tSO\tDT\tPY\tAF\nJ\tPaper with BOM\tNature Physics\tArticle\t2023\tBOM, Author\n".encode("utf-8")
        file_obj = SimpleUploadedFile("wos_bom.txt", bom_content, content_type="text/plain")
        response = self.client.post(
            reverse("publications:wos_upload"),
            {"wos_file": file_obj},
        )
        self.assertRedirects(response, reverse("publications:wos_review"))
        self.assertIn("wos_records", self.client.session)
        record = self.client.session["wos_records"][0]
        self.assertEqual(record["publication"]["title"], "Paper with BOM")
        self.assertEqual(record["publication"]["journal_name"], "Nature Physics")

    def test_upload_non_wos_tsv_rejected(self):
        """Arbitrary TSV files lacking standard Web of Science headers are rejected."""
        arbitrary_tsv = b"Name\tEmail\tDepartment\nAlice\talice@example.com\tPhysics\n"
        file_obj = SimpleUploadedFile("users.tsv", arbitrary_tsv, content_type="text/tab-separated-values")
        response = self.client.post(
            reverse("publications:wos_upload"),
            {"wos_file": file_obj},
            follow=True,
        )
        self.assertRedirects(response, reverse("publications:wos_upload"))
        self.assertNotIn("wos_records", self.client.session)
        self.assertContains(response, "no publication records were detected")

    def test_upload_batch_record_limit_exceeded_rejected(self):
        """Files exceeding the maximum batch record limit (500 records) are rejected."""
        records = [
            {"TI": f"Batch Paper #{i}", "SO": "Test Journal", "AF": f"Author, {i}"}
            for i in range(501)
        ]
        tsv_content = self._generate_wos_tsv(records)
        file_obj = SimpleUploadedFile("large_batch.txt", tsv_content, content_type="text/plain")
        response = self.client.post(
            reverse("publications:wos_upload"),
            {"wos_file": file_obj},
            follow=True,
        )
        self.assertRedirects(response, reverse("publications:wos_upload"))
        self.assertNotIn("wos_records", self.client.session)
        self.assertContains(response, "exceeds the maximum limit of 500 records per batch")

    @override_settings(MAX_WOS_RECORDS=5)
    def test_upload_custom_batch_record_limit_override(self):
        """Custom MAX_WOS_RECORDS limit is enforced before session staging."""
        # 5 records -> accepted
        records_5 = [{"TI": f"Paper #{i}", "SO": "Journal", "AF": "Author, A"} for i in range(5)]
        tsv_5 = self._generate_wos_tsv(records_5)
        file_5 = SimpleUploadedFile("batch_5.txt", tsv_5, content_type="text/plain")
        resp_5 = self.client.post(reverse("publications:wos_upload"), {"wos_file": file_5})
        self.assertRedirects(resp_5, reverse("publications:wos_review"))
        self.assertEqual(len(self.client.session["wos_records"]), 5)

        # Clean session
        session = self.client.session
        session.pop("wos_records", None)
        session.pop("wos_index", None)
        session.save()

        # 6 records -> rejected
        records_6 = [{"TI": f"Paper #{i}", "SO": "Journal", "AF": "Author, A"} for i in range(6)]
        tsv_6 = self._generate_wos_tsv(records_6)
        file_6 = SimpleUploadedFile("batch_6.txt", tsv_6, content_type="text/plain")
        resp_6 = self.client.post(reverse("publications:wos_upload"), {"wos_file": file_6}, follow=True)
        self.assertRedirects(resp_6, reverse("publications:wos_upload"))
        self.assertNotIn("wos_records", self.client.session)
        self.assertContains(resp_6, "exceeds the maximum limit of 5 records per batch")

    def test_upload_parser_exception_handled_safely(self):
        """Exceptions in the parser are caught cleanly and do not crash the view with a 500."""
        valid_tsv = b"PT\tTI\tSO\nJ\tPaper\tJournal\n"
        file_obj = SimpleUploadedFile("valid.txt", valid_tsv, content_type="text/plain")
        with patch("publications.views.parse_wos_file", side_effect=ValueError("Corrupt stream error")):
            response = self.client.post(
                reverse("publications:wos_upload"),
                {"wos_file": file_obj},
                follow=True,
            )
            self.assertRedirects(response, reverse("publications:wos_upload"))
            self.assertNotIn("wos_records", self.client.session)
            self.assertContains(response, "Error processing Web of Science file")
