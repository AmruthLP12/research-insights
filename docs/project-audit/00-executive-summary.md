# Executive Summary: RRI Publications Dashboard ("Research Insights")

## 1. Project Identification and Overview

| Attribute | Project Details | Evidence / Repository Reference |
| :--- | :--- | :--- |
| **Project Name** | RRI Publications Dashboard / Research Insights | [`README.md:1`](../../README.md#L1), [`rri_publications_dashboard/settings.py:2`](../../rri_publications_dashboard/settings.py#L2), [`dashboard/templates/dashboard/sidebar.html:31-32`](../../dashboard/templates/dashboard/sidebar.html#L31-L32) |
| **Django Project Package** | `rri_publications_dashboard` | [`rri_publications_dashboard/`](../../rri_publications_dashboard/) |
| **Primary Domain** | Academic bibliometrics, publication tracking, citation analysis, and institutional research intelligence | [`publications/models.py:12-210`](../../publications/models.py#L12-L210), [`dashboard/views.py:17-2112`](../../dashboard/views.py#L17-L2112) |
| **Target Institution** | Raman Research Institute (RRI), Bangalore, India | [`dashboard/templates/dashboard/sidebar.html:32`](../../dashboard/templates/dashboard/sidebar.html#L32), [`publications/views.py:32-42`](../../publications/views.py#L32-L42) |
| **Current Repository Status** | Active Development / Late Prototype / Early Internal Alpha | Commit history, 0 automated tests, hardcoded `DEBUG=True` |
| **Primary Frameworks** | Django 6.0.6, Python 3.12, Tailwind CSS 4.3.0, DaisyUI 5.5.23 | [`requirements.txt:9`](../../requirements.txt#L9), [`theme/static_src/package.json:17-25`](../../theme/static_src/package.json#L17-L25) |

The **RRI Publications Dashboard** (internally designated as *Research Insights*) is an institutional web-based bibliometric intelligence platform designed for the **Raman Research Institute (RRI)**. Its core purpose is to ingest, standardize, analyze, and visualize scientific publications authored by RRI researchers, faculty, research fellows, scholars, and staff.

The system processes export files from academic indexing databases (specifically Clarivate **Web of Science** tab-delimited formats), extracts bibliographic metadata, institutional affiliations, and authorship details, and serves interactive analytics dashboards covering publication trends, journal impact factors, domestic and international collaborations, department productivity, and author metrics.

---

## 2. Target Users and Primary Use Cases

1. **RRI Institutional Leadership & Academic Deans**:
   - Monitor high-level institutional scientific output, publication growth, and year-over-year citation impact.
   - Evaluate departmental performance across physics, astronomy, optics, theoretical sciences, and soft matter.
   - Track national and international research collaborations across global academic institutions.

2. **RRI Library and Information Officers**:
   - Ingest Web of Science (`.txt` TSV) export files into the institutional database.
   - Review imported publication drafts, verify detected RRI affiliations, correct metadata, and assign internal roles.
   - Maintain author identity mappings, journal impact factor registries, and department taxonomies.

3. **Faculty, Scientists, and Researchers**:
   - Browse comprehensive publication listings filtered by year, document type, collaboration scope, and journal.
   - Inspect individual author profiles, publication records, and citation histories.

4. **Public Visitors and Academic Collaborators**:
   - Search the public catalog of RRI research publications without requiring login credentials.

---

## 3. Current Development and Deployment Status

Based on code-level and operational evidence:

- **Maturity Level**: **Late Prototype / Functional Pre-Production MVP**. Core ingestion, parsing, querying, filtering, and chart rendering workflows are functionally operational. However, production readiness is hindered by critical operational gaps.
- **Verification of Running State**: The project runs successfully under Django 6.0.6 / Python 3.12 on development environments using the built-in SQLite database (`db.sqlite3`).
- **Deployment State**:
  - Apache deployment commands in [`makefile:142-160`](../../makefile#L142-L160) are currently **broken**: `make conf` calls `generate_apache_conf.py`, which is missing from the repository root.
  - Cron management commands in [`makefile:130-138`](../../makefile#L130-L138) rely on `django-crontab`, which is not declared in `requirements.txt` or configured in `settings.py`.
  - Static file collection (`make collectstatic`) fails due to a missing `STATIC_ROOT` directive in `settings.py`.

---

## 4. Main Architectural Characteristics

The project follows a classic server-side rendered (SSR) Django monolith architecture augmented by modern client-side reactive components:

```
+--------------------------------------------------------------------------------+
|                                Browser Client                                  |
|   Tailwind CSS v4 + DaisyUI 5 (Theme) | Alpine.js (State) | Chart.js (Charts)  |
+--------------------------------------------------------------------------------+
                                       |
                                HTTP Requests
                                       v
+--------------------------------------------------------------------------------+
|                        Django WSGI / Middleware Layer                          |
|    SecurityMiddleware -> SessionMiddleware -> CsrfMiddleware -> AuthMiddleware |
+--------------------------------------------------------------------------------+
           |                                  |                        |
           v                                  v                        v
+----------------------+           +----------------------+  +-------------------+
|    `accounts` App    |           |  `publications` App  |  |  `dashboard` App  |
| - CustomUser (RBAC)  |           | - WoS TSV Ingestion  |  | - 11 Dashboard    |
| - Auth & Session     |           | - Catalog & Details  |  |   Views + Details |
| - Password Reset     |           | - Bibliometrics Data |  | - DynamicFilter   |
+----------------------+           +----------------------+  +-------------------+
           |                                  |                        |
           +----------------------------------+------------------------+
                                       |
                                       v
+--------------------------------------------------------------------------------+
|                            Django ORM / SQLite3                                |
|   CustomUser | Publication | Author | Affiliation | Journal | Department       |
+--------------------------------------------------------------------------------+
```

Key architectural traits include:
- **Clean Application Boundaries**: Clear separation between user authentication (`accounts`), data storage and ingestion (`publications`), analytics and visualization (`dashboard`), and frontend asset pipeline (`theme`).
- **Dynamic Query Filtering Pattern**: Custom `DynamicFilter` class ([`dashboard/filters.py:27-164`](../../dashboard/filters.py#L27-L164)) wrapping `django-filter` to generate runtime querysets based on view attributes (`exact_filters`, `date_filters`, `sortable_columns`, `search_fields`).
- **In-Memory Post-Processing Pipeline**: Due to schema limitations in author identity matching, analytical views ([`dashboard/views.py:358-387`](../../dashboard/views.py#L358-L387)) perform extensive Python-level grouping, string sanitization, and deduplication in server memory before pagination.

---

## 5. Summary Technology Inventory

| Tier | Component | Installed / Declared Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | Django | `6.0.6` | Web framework, ORM, authentication, admin |
| **Runtime Language** | Python | `3.12` / `3.13` compatible | Core programming environment |
| **Database Engine** | SQLite 3 | Embedded | Local development persistence (`db.sqlite3`) |
| **Query Filtering** | `django-filter` | `25.2` | URL query parameter parsing and ORM filtering |
| **Frontend Styling** | Tailwind CSS | `4.3.0` | Utility-first CSS framework |
| **Component Library** | DaisyUI | `5.5.23` | Tailwind component classes (cards, stats, badges, nav) |
| **Client Reactivity** | Alpine.js | `3.x` (minified bundle) | Sidebar collapse, hamburger menu, UI toggles |
| **Charting Engine** | Chart.js | `4.x` (minified bundle) | Canvas-based bar charts, line graphs, trends |
| **Iconography** | Lucide Icons | Latest (minified bundle) | SVG iconography for navigation and UI elements |
| **Build & Tooling** | PostCSS, djLint | PostCSS `8.5.15`, djLint `1.40.8` | CSS pipeline compilation, template linting |

---

## 6. Key Implemented Features

1. **Web of Science (WoS) Batch File Ingestion**:
   - Direct upload of `.txt` full-record TSV files exported from Web of Science ([`publications/views.py:201-218`](../../publications/views.py#L201-L218)).
   - Regex-based address and authorship parser ([`publications/utils/wos_parser.py:31-97`](../../publications/utils/wos_parser.py#L31-L97)) extracting author names, affiliation addresses, and countries.
   - Automatic RRI affiliation detection using heuristic matching (`raman`, `raman res inst`, `raman research institute`, `rri`).
   - Multi-step interactive review and staging workflow ([`publications/views.py:225-300`](../../publications/views.py#L225-L300)) allowing manual verification of publication attributes and author roles prior to database insertion.
   - Atomic database commit with `transaction.atomic` ([`publications/views.py:304`](../../publications/views.py#L304)).

2. **Publications Catalog & Filtering**:
   - Searchable, sortable, and paginated master list of publications ([`publications/views.py:48-171`](../../publications/views.py#L48-L171)).
   - Comprehensive detail page with journal metrics, author roster, institutional affiliations, and citation metrics ([`publications/views.py:173-195`](../../publications/views.py#L173-L195)).

3. **Bibliometrics Analytics Dashboards (11 Distinct Views)**:
   - **Executive Dashboard** (`dashboard:home`): KPI summary cards, publication types bar chart, YoY publication line chart, recent publications feed.
   - **Document Types** (`dashboard:documents`): Breakdown across Journal Articles, Conference Papers, Book Chapters, Letters, Patents, and Reviews.
   - **Authors Analysis** (`dashboard:authors`): Author productivity leaderboard, total impact factors, affiliated institutions, and per-author drill-downs (`dashboard:author_detail`).
   - **Journals Intelligence** (`dashboard:journals`): Journal output rankings, publisher tracking, and impact factor analytics.
   - **Departmental Productivity** (`dashboard:departments`): Research output categorized by academic department.
   - **Collaboration Analytics** (`dashboard:collaboration`): Categorization by National, International, National/International, and Departmental.
   - **Geographic Collaboration** (`dashboard:country_collaboration`): International co-authorship distributions mapped across partner countries.
   - **Institutional Collaboration** (`dashboard:institution_collaboration`): Academic co-authorship mapped across partner universities and research centers.
   - **Historical Trends** (`dashboard:trends`): Multi-year publication trajectories and citation growth metrics.
   - **Impact Factor Analysis** (`dashboard:impact`): Journal impact factor distributions and high-impact publication tracking.
   - **RRI Institutional Roles** (`dashboard:rri_role`): Output categorized by Faculty, Retired Faculty, Adjunct Faculty, Research Scholars, PDFs, RAs, and Staff.

4. **Account Management & Authentication**:
   - Custom user model (`CustomUser`) with defined roles (`admin`, `user`, `viewer`).
   - "Remember Me" session handling ([`accounts/views.py:14-16`](../../accounts/views.py#L14-L16)).
   - Standard password change and reset URL scaffolding.

---

## 7. Key Strengths

- **Cohesive, Modern UI/UX**: DaisyUI 5 and Tailwind CSS 4 deliver a clean, responsive layout with dark-mode scaffolding, sticky headers, collapsible navigation, and responsive typography.
- **Fast Client-Side Interactions**: Alpine.js and Chart.js eliminate heavyweight single-page application (SPA) framework overhead while maintaining rapid chart rendering and seamless sidebar toggling.
- **Rich Bibliometric Data Model**: The database schema captures crucial academic relationships: `Publication`, `Author`, `Affiliation`, `AuthorAffiliation` (linking authors to specific papers with distinct affiliations), `Journal`, `Department`, and `Citation`.
- **Dynamic Filter Reusability**: The `DynamicFilter` architecture reduces boilerplate across 11+ views by translating view-level configuration into Django ORM lookups.

---

## 8. Major Technical Risks

1. **Author Entity Duplication and Proliferation**:
   - In [`publications/views.py:334-340`](../../publications/views.py#L334-L340), `wos_save` calls `author = form.save()`, creating a *new* `Author` record for every author on every paper, even if that author already exists in the database.
   - This leads to severe database bloat, fragments author foreign keys, and forces [`dashboard/views.py:358-387`](../../dashboard/views.py#L358-L387) to merge authors in Python memory on every request.
2. **Database Schema Drift**:
   - Migration `0002_alter_publication_options_publication_article_number.py` added the `article_number` field to the `publications_publication` table.
   - However, `article_number` is missing from `Publication` in [`publications/models.py`](../../publications/models.py). Running `makemigrations` detects this as a deletion and prompts a destructive schema drop.
3. **Broken Static Asset and Deployment Tooling**:
   - `STATIC_ROOT` is not configured in `settings.py`, causing `manage.py collectstatic` to fail.
   - The deployment target in `makefile` depends on a nonexistent script (`generate_apache_conf.py`) and an uninstalled package (`django-crontab`).
4. **Complete Absence of Automated Tests**:
   - Test files in `accounts/tests.py`, `publications/tests.py`, and `dashboard/tests.py` contain 0 test cases. Regression prevention is currently manual.

---

## 9. Major Security Concerns

| Risk ID | Vulnerability / Concern | Severity | Confidence | Reference |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Hardcoded Insecure `SECRET_KEY` in `settings.py` | **High** | Confirmed | [`settings.py:13`](../../rri_publications_dashboard/settings.py#L13) |
| **SEC-02** | Hardcoded `DEBUG = True` and Wildcard `ALLOWED_HOSTS = ['*']` | **High** | Confirmed | [`settings.py:14-15`](../../rri_publications_dashboard/settings.py#L14-L15) |
| **SEC-03** | Missing Authentication / Authorization on All Dashboard Views | **Medium** | Confirmed | [`dashboard/views.py:17-2112`](../../dashboard/views.py#L17-L2112) |
| **SEC-04** | Role-Based Access Control (RBAC) Completely Unenforced | **Medium** | Confirmed | [`accounts/models.py:13`](../../accounts/models.py#L13) |
| **SEC-05** | Unrestricted WoS File Upload and Session Denial-of-Service | **Medium** | Confirmed | [`publications/views.py:201-218`](../../publications/views.py#L201-L218) |
| **SEC-06** | Insecure Session and CSRF Cookies (`SECURE = False`) | **Low** | Confirmed | `manage.py check --deploy` |
| **SEC-07** | Unconfigured Email Backend Causing 500 on Password Reset | **Low** | Confirmed | [`settings.py:1-122`](../../rri_publications_dashboard/settings.py#L1-L122) |

---

## 10. Modernization Opportunities

1. **Environment Configuration Architecture**: Integrate `python-dotenv` or `django-environ` so `settings.py` dynamically ingests `.env` parameters (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `PORT`).
2. **Author Canonicalization & Disambiguation Service**: Introduce a master author deduplication model or service that matches incoming WoS names against existing institutional faculty records instead of creating duplicate rows.
3. **Model & Migration Reconciliation**: Restore `article_number` to `Publication` model to eliminate schema drift.
4. **Asynchronous Ingestion Pipeline**: Replace session-serialized WoS staging with a temporary database staging model (`StagedPublicationBatch`) and background parsing.
5. **Query Optimization & Database Indexing**: Add database indexes on frequently queried fields (`date_published`, `doi`, `document_type`, `collaboration_type`) and replace Python in-memory post-processing with PostgreSQL or SQLite window functions / subqueries.
6. **Comprehensive Automated Test Suite**: Implement pytest/Django TestCase coverage for WoS parser edge cases, dynamic filters, dashboard metrics calculations, and auth workflows.

---

## 11. Areas Requiring Further Verification

1. **Production Infrastructure Intent**: Whether the target production deployment will use Apache WSGI (`mod_wsgi`), Gunicorn + Nginx, or Docker containerization.
2. **Orphaned Source Code**: Determine if [`publications/views_dashboard.py`](../../publications/views_dashboard.py) and [`dashboard/tables.py`](../../dashboard/tables.py) should be deprecated or removed.
3. **Unlinked CRUD Templates**: Determine if manual publication entry/edit workflows (`create_publication.html`, `edit_publication.html`) are intended for future implementation or were abandoned in favor of WoS upload.
4. **Production Database Engine**: Confirm whether RRI plans to remain on SQLite or migrate to PostgreSQL/MySQL for multi-user concurrency in production.

