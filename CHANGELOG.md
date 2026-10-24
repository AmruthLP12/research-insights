# Changelog

All notable changes to the RRI Publications Dashboard (*Research Insights*) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added - 2026-10-24

#### Task 1: Establish Reliable Change and Decision Log
- **Initial Tracking Setup**:
  - Established `CHANGELOG.md` to permanently record all remediation tasks, verified checks, affected files, and known limitations.
  - Established `DECISIONS.md` to capture architectural and procedural decisions, starting with `D-001: Incremental Remediation Workflow`.
  - Defined explicit documentation standards for all subsequent tasks: update tracking files in the same task as the code change, honestly record failed checks or unverified claims, and explicitly note when no application code is modified.

#### Baseline Project State (Audit & Independent Verification)
- **Application Context**:
  - The project is an institutional bibliometrics intelligence platform for the Raman Research Institute (RRI), Bangalore, India.
  - Stack: Django 6.0.6, Python 3.12, Tailwind CSS 4.3.0, DaisyUI 5.5.23, SQLite 3, Chart.js, Alpine.js, Lucide Icons.
  - Functional Modules: Web of Science (WoS) `.txt` full-record TSV batch ingestion, multi-record review & staging workflow, publications catalog with `DynamicFilter`, and 11 analytical dashboard views with drilldowns.

- **Audit-Reported Issues vs. Independently Verified Facts**:

  | Issue / State | Source | Verification Command / Method | Verification Status |
  | :--- | :--- | :--- | :--- |
  | Insecure `SECRET_KEY`, `DEBUG = True`, `ALLOWED_HOSTS = ['*']` hardcoded | Audit Report ([`07-authentication-authorization-and-security.md`](docs/project-audit/07-authentication-authorization-and-security.md)) | Inspected [`settings.py:13-15`](rri_publications_dashboard/settings.py#L13-L15); ran `python manage.py check --deploy` | **Verified**: 6 security warnings raised |
  | Schema drift on `Publication.article_number` | Audit Report ([`05-database-and-data-model.md`](docs/project-audit/05-database-and-data-model.md)) | Checked table info via `PRAGMA table_info(publications_publication)`; ran `python manage.py makemigrations --dry-run` | **Verified**: Column exists in DB and migration 0002, but is absent from `Publication` in `models.py`. Django detects removal. |
  | Missing `STATIC_ROOT` in `settings.py` | Audit Report ([`08-configuration-environments-and-deployment.md`](docs/project-audit/08-configuration-environments-and-deployment.md)) | Executed `python manage.py collectstatic --dry-run --noinput` | **Verified**: Throws `django.core.exceptions.ImproperlyConfigured` |
  | 0% Automated Test Coverage | Audit Report ([`09-testing-quality-and-maintainability.md`](docs/project-audit/09-testing-quality-and-maintainability.md)) | Inspected `accounts/tests.py`, `dashboard/tests.py`, `publications/tests.py`; ran `python manage.py test` | **Verified**: Test files contain 0 tests; test runner reports `Ran 0 tests in 0.000s` |
  | All 21 dashboard views lack authentication | Audit Report ([`04-routes-views-and-api-reference.md`](docs/project-audit/04-routes-views-and-api-reference.md)) | Inspected [`dashboard/views.py:17-2112`](dashboard/views.py#L17-L2112) | **Verified**: All 21 views inherit `TemplateView`; 0 `LoginRequiredMixin` imports |
  | `CustomUser.role` unenforced | Audit Report ([`07-authentication-authorization-and-security.md`](docs/project-audit/07-authentication-authorization-and-security.md)) | Inspected [`accounts/models.py:13`](accounts/models.py#L13); searched codebase for role checks | **Verified**: Zero view permissions or template checks on `request.user.role` |
  | Dangerous `CASCADE` deletion on `Publication.created_by` | Audit Report ([`05-database-and-data-model.md`](docs/project-audit/05-database-and-data-model.md)) | Inspected [`publications/models.py:182-185`](publications/models.py#L182-L185) | **Verified**: Deleting a user cascades to all publications uploaded by that user |
  | Broken Apache / Cron Makefile targets | Audit Report ([`08-configuration-environments-and-deployment.md`](docs/project-audit/08-configuration-environments-and-deployment.md)) | Checked file system for `generate_apache_conf.py`; inspected `requirements.txt` for `django-crontab` | **Verified**: `generate_apache_conf.py` missing; `django-crontab` not installed |
  | Unused dependencies declared in `requirements.txt` | Audit Report ([`01-technology-stack.md`](docs/project-audit/01-technology-stack.md)) | Grep search across Python files for `requests`, `arrow`, `honcho` | **Verified**: Zero imports in application code |
  | Dead / Phantom code in `views_dashboard.py` and `tables.py` | Audit Report ([`02-project-structure-and-architecture.md`](docs/project-audit/02-project-structure-and-architecture.md)) | Checked imports of `views_dashboard` and `tables.py` | **Verified**: Unreferenced; `tables.py` imports uninstalled `django-tables2` |
  | Duplicate DOCTYPE and HTML tags in `dashboard/templates/base.html` | Audit Report ([`06-ui-ux-and-design-system.md`](docs/project-audit/06-ui-ux-and-design-system.md)) | Inspected [`dashboard/templates/base.html:1-6, 79-80`](dashboard/templates/base.html#L1-L6) | **Verified**: Lines 1-6 duplicate opening tags; lines 79-80 duplicate closing tags |
  | Pagination drops active filter parameters | Audit Report ([`06-ui-ux-and-design-system.md`](docs/project-audit/06-ui-ux-and-design-system.md)) | Inspected [`dashboard/templates/components/pagination.html:20, 27, 43`](dashboard/templates/components/pagination.html#L20) | **Verified**: Only appends `search` query parameter, dropping dates and categories |
  | Unconfigured Email Backend causing 500 on Password Reset | Audit Report ([`07-authentication-authorization-and-security.md`](docs/project-audit/07-authentication-authorization-and-security.md)) | Inspected `settings.py` | **Verified**: No `EMAIL_BACKEND` configured; defaults to `localhost:25` |

- **Application Changes in this Task**:
  - **None**. No application source files, templates, styles, dependencies, migrations, database records, deployment configurations, or secrets were modified or created. Only `CHANGELOG.md` and `DECISIONS.md` were established.
