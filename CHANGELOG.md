# Changelog

All notable changes to the RRI Publications Dashboard (*Research Insights*) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Fixed - 2026-10-24

#### Task 4: Configure STATIC_ROOT and Verify collectstatic
- **Static Asset Deployment Configuration**:
  - Configured `STATIC_ROOT = BASE_DIR / "staticfiles"` in [`rri_publications_dashboard/settings.py`](rri_publications_dashboard/settings.py) to define the target directory for static file collection during deployments.
  - Added `staticfiles/` to [`.gitignore`](.gitignore) to ensure collected deployment assets are not tracked in version control.
  - Preserved source static paths: `STATIC_URL = "/static/"` and `STATICFILES_DIRS = [BASE_DIR / "static"]` remain intact, distinct, and conflict-free.
- **Files Modified**:
  - `rri_publications_dashboard/settings.py`
  - `.gitignore`
- **Verification Performed**:
  - `venv/bin/python manage.py check`: Passed with 0 issues.
  - `venv/bin/python manage.py collectstatic --noinput --dry-run`: Succeeded (simulated collection of 136 static assets across admin, theme, and custom JS).
  - `venv/bin/python manage.py collectstatic --noinput`: Succeeded (copied 136 static files to `/home/amruth/pro/django/research-insights/staticfiles`).
  - `venv/bin/python manage.py check --deploy`: 0 static files warnings; only 4 expected SSL/cookie warnings remain.
  - `git diff --check`: 0 whitespace or formatting errors.
- **Limitations & Known Concerns**:
  - `staticfiles/` contains generated assets for deployment and is purposefully ignored by version control. Apache/Nginx web server configurations must alias `/static/` to `BASE_DIR / "staticfiles"` in production.

#### Task 3: Restore the Missing Publication.article_number Model Field
- **Model & Schema Reconciliation**:
  - Restored `article_number = models.CharField(max_length=50, blank=True, null=True)` to `Publication` in [`publications/models.py`](publications/models.py), matching applied migration `0002_alter_publication_options_publication_article_number.py` and the existing `db.sqlite3` column definition.
  - Reconciled `Publication.Meta.ordering = ["-date_published", "title"]` with migration `0002`, eliminating all schema drift detected by Django.
  - No new migration was required; `makemigrations --check --dry-run` reports zero changes.
- **Workflow & Interface Integration**:
  - Registered `article_number` in `PublicationForm` ([`publications/forms.py`](publications/forms.py)) with Tailwind styling.
  - Added `article_number` to Django Admin `PublicationAdmin.fieldsets` metadata section ([`publications/admin.py`](publications/admin.py)).
  - Updated Web of Science parser ([`publications/utils/wos_parser.py`](publications/utils/wos_parser.py)) to populate `article_number` from `AR` / `ARTN` tags.
  - Updated review workflow initial form binding ([`publications/views.py`](publications/views.py)) to propagate parsed article numbers into `PublicationForm`.
- **Files Modified**:
  - `publications/models.py`
  - `publications/forms.py`
  - `publications/admin.py`
  - `publications/utils/wos_parser.py`
  - `publications/views.py`
- **Verification Performed**:
  - `venv/bin/python manage.py check`: Passed with 0 issues.
  - `venv/bin/python manage.py makemigrations --check --dry-run`: Passed (`No changes detected`).
  - `venv/bin/python manage.py showmigrations`: Confirmed all migrations applied up to `publications.0002`.
  - Focused field test suite (`scratch/test_article_number.py`):
    - Verified field attributes: `CharField(max_length=50, blank=True, null=True)`.
    - Verified ORM query compilation references `article_number`.
    - Verified `PublicationForm` validation and clean data mapping.
    - Verified `wos_parser` parses `AR` tag to `article_number`.
    - Verified SQLite database schema `publications_publication` table structure.
  - `venv/bin/python manage.py test`: Ran with 0 errors.
  - `git diff --check`: 0 whitespace or formatting errors.
- **Limitations & Known Concerns**:
  - Existing database currently contains 0 publication records (`SELECT COUNT(*) FROM publications_publication` returned 0). Verified that the schema column exists and matches expected definitions.

### Changed - 2026-10-24

#### Task 2.2: Refactor Django Environment Configuration into env.py
- **Extraction of Environment Helpers**:
  - Created [`rri_publications_dashboard/env.py`](rri_publications_dashboard/env.py) containing all environment-variable parsing, validation, and loading logic (`load_env_file`, `parse_bool`, `get_bool`, `parse_list`, `get_list`, `get_secret_key`, `get_allowed_hosts`).
  - Simplified [`rri_publications_dashboard/settings.py`](rri_publications_dashboard/settings.py) to purely declarative settings statements (`DEBUG = get_bool(...)`, `SECRET_KEY = get_secret_key(...)`, `ALLOWED_HOSTS = get_allowed_hosts(...)`).
  - Standard library and Django exceptions (`ImproperlyConfigured`) used exclusively; zero external dependencies added.
- **Verification & Precedence Guarantees**:
  - Verified process environment variables take strict precedence over `.env` file entries via `os.environ.setdefault`.
  - Maintained all fail-closed security rules for production (`DEBUG=False`): missing/insecure secret key and empty/wildcard `ALLOWED_HOSTS` raise `ImproperlyConfigured`.
  - Maintained legacy `SECRET_KEY` compatibility fallback and stable local development key (`DEV_SECRET_KEY_FALLBACK`).
- **Files Modified / Created**:
  - `rri_publications_dashboard/env.py` (created)
  - `rri_publications_dashboard/settings.py` (modified)
- **Verification Performed**:
  - Comprehensive unit test suite (`scratch/test_settings.py`):
    - Tested valid and invalid booleans (`parse_bool`, `get_bool`).
    - Tested process environment precedence over `.env` files.
    - Tested production validation failure modes (missing secret, short secret, insecure prefix, empty hosts, wildcard hosts).
    - Tested production valid configurations and legacy `SECRET_KEY` fallback.
    - Tested development defaults and stable fallback key.
  - `venv/bin/python manage.py check`: Passed with 0 issues.
  - `venv/bin/python manage.py check --deploy`: 0 warnings for `SECRET_KEY` and `DEBUG`; only 4 expected SSL/cookie warnings remain.
  - `venv/bin/python manage.py test`: 0 tests ran, 0 errors.
  - `git diff --check`: 0 whitespace or formatting errors.

#### Task 2.1: Refactor Django Settings for Readability
- **Code Cleanliness & Modular Structure**:
  - Moved all imports (`os`, `pathlib.Path`, `django.core.exceptions.ImproperlyConfigured`) to the top of `rri_publications_dashboard/settings.py`.
  - Reorganized settings into clean, well-delimited thematic sections with consistent double-quoted strings and section banners (`BASE DIRECTORIES`, `ENVIRONMENT LOADING & HELPERS`, `CORE SECURITY SETTINGS`, `APPLICATION DEFINITION`, `MIDDLEWARE`, `URLS & WSGI`, `TEMPLATES`, `AUTHENTICATION & USERS`, `DATABASE`, `INTERNATIONALIZATION`, `STATIC FILES`, `DEFAULT AUTO FIELD`, `TAILWIND & THEME`).
  - Extracted helper logic into clean functions (`_load_env_file`, `_parse_bool`, `_parse_list`) without introducing external dependencies or unnecessary abstractions.
- **Strict Boolean Parsing**:
  - Updated `_parse_bool` to be strict: unrecognized/invalid boolean values (e.g. `DEBUG=maybe`, `DEBUG=2`) now raise `django.core.exceptions.ImproperlyConfigured` rather than silently converting to `False`.
  - Unset or empty values safely default to `False`.
- **Stable Development Secret Key**:
  - Eliminated per-process random secret key generation (`secrets.token_urlsafe`) which previously invalidated active sessions and CSRF tokens across local `runserver` reloads.
  - Replaced with a stable, fixed development fallback (`DEV_SECRET_KEY_FALLBACK`) used strictly when `DEBUG=True` and no environment key is supplied.
  - Production (`DEBUG=False`) continues to strictly reject insecure, short, or missing keys with `ImproperlyConfigured`.
- **Environment & Deployment Compatibility**:
  - Canonical secret variable remains `DJANGO_SECRET_KEY`, with backward-compatible fallback to `SECRET_KEY`.
  - Updated `.env.example` comments to document the stable development fallback and canonical variables.
- **Files Modified**:
  - `rri_publications_dashboard/settings.py`
  - `.env.example`
- **Verification Performed**:
  - `test_boolean_parser`: Tested valid truthy (`true`, `1`, `yes`, `t`, `on`), valid falsy (`false`, `0`, `no`, `f`, `off`), empty/None defaults, and invalid values (`maybe`, `2`, `foo`) raising `ImproperlyConfigured`.
  - `test_production_and_development`:
    - Production missing secret -> `ImproperlyConfigured` (passed).
    - Production insecure key (<50 chars or `django-insecure-...`) -> `ImproperlyConfigured` (passed).
    - Production empty or wildcard `ALLOWED_HOSTS` (`*`, `example.com, *`) -> `ImproperlyConfigured` (passed).
    - Production valid config -> booted successfully with exact host parsing (passed).
    - Development stable fallback -> identical stable key across multiple process invocations (passed).
    - Documented `.env` setup -> loaded valid dev values correctly (passed).
  - `venv/bin/python manage.py check`: Passed with 0 issues.
  - `venv/bin/python manage.py check --deploy`: 0 warnings for `SECRET_KEY` and `DEBUG`; only 4 expected SSL/cookie warnings remain.
  - Settings comparison: Verified all application definitions, middleware, authentication models, database engines, and static configurations remain identical.
  - `git diff --check`: 0 whitespace or formatting errors.

### Added - 2026-10-24

#### Task 2: Secure Django Settings and Environment Configuration
- **Environment-Driven Configuration**:
  - Replaced hardcoded insecure settings in `rri_publications_dashboard/settings.py` with standard-library environment variable loading.
  - Added lightweight `.env` parser reading `.env` from repository root if present, preserving existing OS environment variables, without introducing third-party dependencies (`django-environ`).
  - Added explicit boolean parsing helper `_parse_bool` recognizing standard truthy/falsy values, defaulting safely to `False`.
  - Added comma-separated list parsing helper `_parse_list` with whitespace stripping.
- **Fail-Closed Security Protections**:
  - `SECRET_KEY`: Resolved from `DJANGO_SECRET_KEY` or `SECRET_KEY`. In production (`DEBUG=False`), raises `django.core.exceptions.ImproperlyConfigured` if unset, shorter than 50 characters, or starts with `django-insecure-`. For local development (`DEBUG=True`), generates an ephemeral random secret key (`django-insecure-dev-...`) per process if none is provided.
  - `DEBUG`: Environment-driven with default `False`. Enables `django_browser_reload` only when explicitly set to truthy values.
  - `ALLOWED_HOSTS`: In production (`DEBUG=False`), requires a non-empty, comma-separated host list and strictly rejects wildcards (`*`) with `ImproperlyConfigured`. In development (`DEBUG=True`), defaults to `['localhost', '127.0.0.1', '[::1]']` merged with any user-configured hosts.
- **Environment Template & Documentation**:
  - Updated `.env.example` with clear comments explaining each security variable, development vs. production requirements, and security rules.
  - Verified `.env` remains ignored by Git.
- **Files Modified**:
  - `rri_publications_dashboard/settings.py`
  - `.env.example`
- **Verification Performed**:
  - `venv/bin/python manage.py check`: Passed with 0 issues.
  - `venv/bin/python manage.py check --deploy`: Verified `security.W009` (SECRET_KEY) and `security.W018` (DEBUG) are completely eliminated.
  - Boolean parsing matrix test: Verified `true`, `1`, `yes`, `t`, `on` evaluate to `True`; `false`, `0`, `no`, `f`, `off`, `""`, and random strings evaluate to `False`.
  - Fail-closed tests (`DEBUG=False`):
    - Missing `DJANGO_SECRET_KEY`: Verified `ImproperlyConfigured` raised.
    - Insecure `DJANGO_SECRET_KEY` (`django-insecure-...` or `<50` chars): Verified `ImproperlyConfigured` raised.
    - Empty `ALLOWED_HOSTS`: Verified `ImproperlyConfigured` raised.
    - Wildcard `ALLOWED_HOSTS=*`: Verified `ImproperlyConfigured` raised.
  - Development convenience tests (`DEBUG=True`):
    - Unset secret key: Ephemeral dev key generated and allowed startup.
    - Unset hosts: Defaulted to `['localhost', '127.0.0.1', '[::1]']`.
  - `git diff --check`: 0 whitespace or formatting errors.
- **Known Limitations & Remaining Issues**:
  - `manage.py check --deploy` still reports 4 expected deployment warnings (`security.W004` SECURE_HSTS_SECONDS, `security.W008` SECURE_SSL_REDIRECT, `security.W012` SESSION_COOKIE_SECURE, `security.W016` CSRF_COOKIE_SECURE) which belong to downstream HTTPS/cookie hardening tasks.
  - `STATIC_ROOT` remains unconfigured (identified in Task 1 audit baseline; to be addressed in subsequent static files remediation).

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
