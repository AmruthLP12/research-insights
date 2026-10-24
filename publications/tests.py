import json
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
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
