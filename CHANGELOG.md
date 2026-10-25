# Changelog

All notable changes to the RRI Publications Dashboard (*Research Insights*) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Security & Authorization - 2026-10-25

#### Step 7: Audit and Enforce Dashboard Endpoint Permissions
- **Dashboard Authorization Audit & Systematic Verification**:
  - Audited all 21 class-based views in `dashboard/views.py` against the access control policy established in D-005.
  - Confirmed all 21 views inherit from `LoginRequiredMixin` and `TemplateView`, establishing server-side authentication enforcement on all analytical endpoints.
  - Confirmed that dashboard views are read-only analytics interfaces accessible by all authenticated roles (`viewer`, `user`, `admin`, `staff`, `superuser`).
  - Confirmed that mutation attempts (POST, PUT, DELETE, PATCH) on read-only dashboard endpoints fail closed with HTTP 405 Method Not Allowed.
  - Confirmed that anonymous requests across all 21 endpoints redirect to `accounts:login` preserving the `?next=<url>` query parameter for post-login return.
  - Confirmed that public routes (`/publications/` catalog list, `/publications/<pk>/` detail) remain accessible to anonymous traffic without restriction.
  - Confirmed invalid object identifiers on detail endpoints (`journal_detail`, `department_detail`, `impact_detail`) return HTTP 404 Not Found.
- **Regression Test Coverage (`dashboard/tests.py`)**:
  - Expanded `dashboard/tests.py` from 4 to 14 tests:
    - `test_total_view_count`: Verifies all 21 dashboard endpoints are mapped and tracked.
    - `test_anonymous_get_redirects_to_login_with_next_param`: Verifies 302 redirect with preserved `?next=` query parameter across all 21 endpoints.
    - `test_anonymous_post_redirects_to_login`: Verifies anonymous POST attempts redirect to login.
    - `test_anonymous_unsupported_methods_redirect_to_login`: Verifies anonymous PUT and DELETE attempts redirect to login.
    - `test_authenticated_viewer_role_access`: Verifies HTTP 200 OK across all 21 endpoints for `viewer` role.
    - `test_authenticated_user_role_access`: Verifies HTTP 200 OK across all 21 endpoints for `user` role.
    - `test_authenticated_admin_role_access`: Verifies HTTP 200 OK across all 21 endpoints for `admin` role.
    - `test_staff_and_superuser_access`: Verifies HTTP 200 OK across all 21 endpoints for staff and superusers.
    - `test_authenticated_post_rejected_with_405_method_not_allowed`: Verifies HTTP 405 Method Not Allowed on POST across all 21 endpoints.
    - `test_authenticated_unsupported_methods_rejected_with_405`: Verifies HTTP 405 Method Not Allowed on PUT and DELETE across all 21 endpoints.
    - `test_root_redirect_behavior`: Verifies root URL `/` redirects to `/dashboard/` and follows to login for anonymous visitors or to home for authenticated users.
    - `test_public_routes_remain_accessible_without_authentication`: Verifies publication list and detail views remain public.
    - `test_detail_views_return_404_on_invalid_identifiers`: Verifies HTTP 404 on invalid journal/department IDs.
    - `test_dashboard_handles_publications_with_null_creator`: Verifies aggregation views handle unowned publications.
- **Verification Results**:
  - Test suite ran **67 tests** across `accounts` (25 tests), `publications` (28 tests), and `dashboard` (14 tests) with 0 failures and 0 errors.
  - `manage.py check` identified 0 issues.
  - `makemigrations --check --dry-run` detected 0 schema drift.
- **Files Modified**:
  - `dashboard/tests.py`
  - `CHANGELOG.md`

### Testing & Quality Assurance - 2026-10-24

#### Task 7: Comprehensive Publication Workflow Testing and Security Regression Coverage
- **Web of Science (WoS) Ingestion Workflow Test Suite**:
  - **Upload Verification (`wos_upload`)**: Added tests for valid TSV file upload initializing session records (`wos_records`, `wos_index=0`) and redirecting to review.
  - **Negative & Edge Cases**: Added tests for 0-byte empty files, header-only files without data rows, missing `wos_file` in POST, verifying appropriate validation error messages and absence of session corruption.
  - **Review Page Verification (`wos_review`)**: Added tests verifying form initial data extraction, dynamic `Journal` creation/retrieval, `AuthorFormSet` pre-population (RRI affiliation heuristic setting internal vs external roles), decoded affiliations JSON, and redirection to upload if session is empty or index is out of bounds.
  - **Persistence & Atomic Save (`wos_save`)**: Added tests verifying full database persistence of `Publication` (with `created_by=request.user`), `Author`, `Affiliation`, and `AuthorAffiliation`; session cleanup upon completion; multi-record files advancing `wos_index` iteratively; deduplication of existing `Journal` and `Affiliation` records; and author filtering via `DELETE=True`.
  - **Transaction Rollback**: Verified invalid form submissions trigger atomic rollback, leave database unmodified (0 records created), and preserve session state.
  - **Method Enforcement**: Verified GET requests to `wos_save` redirect to `wos_review`.
- **Sensitive Endpoint Security & Role-Based Access Control**:
  - Verified anonymous user redirection (302 to login) on GET and POST requests across all WoS endpoints (`wos_upload`, `wos_review`, `wos_save`, `wos_success`).
  - Verified server-side 403 Forbidden enforcement on GET and POST requests for `viewer` role users across all WoS endpoints.
  - Verified authorized access for `user` and `admin` roles, and staff/superuser role overrides for `viewer` accounts.
- **Publication Retention & Data Integrity**:
  - Verified `Publication.created_by` is set to `NULL` upon user account deletion, with all associated relationships (`authors`, `departments`, `journal`, `author_affiliations`, `yearly_citations`) remaining completely intact.
  - Verified public publication list and detail views render publications with `created_by=None` without error.
  - Verified dashboard aggregation views (`dashboard:home`, `dashboard:documents`, `dashboard:trends`) execute correctly with null creator publications.
- **Public Publication Catalog & Detail Views**:
  - `publications:list`: Verified empty database state (renders 0 counts cleanly without 500 error), pagination across multiple pages (10 items per page), keyword search (`?search=`), exact filters (`document_type`, `collaboration_type`), and ordering (`ordering=title`, `ordering=-title`).
  - `publications:publication_detail`: Verified 200 OK rendering of comprehensive metadata (journal, authors, departments, affiliations, citations), 404 Not Found on invalid primary keys, and graceful rendering of minimal records lacking optional metadata.
- **Authentication & Password Management Regressions**:
  - Verified `accounts:login` GET renders form, POST logs in and checks session `_auth_user_id`, `remember_me` checkbox controls browser-close session expiry (`get_expire_at_browser_close()`), invalid credentials return form error, inactive users fail to authenticate, and authenticated users visiting login redirect.
  - Verified `accounts:logout` clears user session.
  - Verified password reset confirmation lifecycle: valid token redirects to `set-password` and renders form with `validlink=True`, POST updates password and redirects to `password_reset_complete`, user logs in with new password, invalid/tampered tokens render invalid link message, and tokens cannot be reused.
  - Verified `accounts:password_change`: anonymous redirect to login, authenticated form rendering, successful password change redirecting to `password_change_done`, and invalid old password validation.
  - Fixed latent broken URL reference `{% url 'dashboard' %}` in [`templates/registration/password_change_done.html`](templates/registration/password_change_done.html) to `{% url 'dashboard:home' %}`.
- **Test Metrics**:
  - Expanded total automated tests from 20 to **57 passing tests** across `accounts` (25 tests), `publications` (28 tests), and `dashboard` (4 tests).
- **Files Modified**:
  - `accounts/tests.py` (modified)
  - `dashboard/tests.py` (modified)
  - `publications/tests.py` (modified)
  - `templates/registration/password_change_done.html` (modified)
  - `CHANGELOG.md` (modified)

### Security & Reliability - 2026-10-24

#### Task 6: Resolve Security Gaps: Publication Ownership, Password Reset Workflow, and Production Transport Security
- **Publication Ownership Protection**:
  - Changed `Publication.created_by` relationship from `on_delete=models.CASCADE` to `on_delete=models.SET_NULL, null=True, blank=True` in [`publications/models.py`](publications/models.py).
  - Generated and applied migration `0003_alter_publication_created_by` to decouple publication record lifespan from user accounts, preventing catastrophic data loss when user accounts are deleted.
- **Password Reset Workflow & Filter Repair**:
  - Resolved `TemplateSyntaxError: Invalid filter: 'add_class'` on password reset templates by implementing the `add_class` filter in [`accounts/templatetags/form_tags.py`](accounts/templatetags/form_tags.py) and registering `accounts.templatetags.form_tags` in `TEMPLATES[0]['OPTIONS']['builtins']` in [`rri_publications_dashboard/settings.py`](rri_publications_dashboard/settings.py).
  - Resolved `NoReverseMatch: Reverse for 'password_reset_done' not found` and `NoReverseMatch: Reverse for 'password_reset_confirm' not found` across the namespaced `accounts` URL patterns by configuring explicit namespaced `success_url`s in [`accounts/urls.py`](accounts/urls.py) (`accounts:password_reset_done`, `accounts:password_reset_complete`, `accounts:password_change_done`) and creating [`templates/registration/password_reset_email.html`](templates/registration/password_reset_email.html) referencing `accounts:password_reset_confirm`.
  - Configured environment-driven email settings in [`rri_publications_dashboard/settings.py`](rri_publications_dashboard/settings.py) and [`rri_publications_dashboard/env.py`](rri_publications_dashboard/env.py): default to console backend in development (`DEBUG=True`) and SMTP backend in production (`DEBUG=False`), with fail-fast validation against conflicting TLS/SSL options or missing `EMAIL_HOST`.
- **Production Transport Security & Cookie Hardening**:
  - Configured HTTPS/cookie environment toggles in [`rri_publications_dashboard/settings.py`](rri_publications_dashboard/settings.py): `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`, and `SECURE_PROXY_SSL_HEADER` (`HTTP_X_FORWARDED_PROTO` support via `USE_X_FORWARDED_PROTO`).
  - Added `"testserver"` to dev `ALLOWED_HOSTS` in [`rri_publications_dashboard/env.py`](rri_publications_dashboard/env.py) to avoid `DisallowedHost` errors during test runs.
  - Updated [`.env.example`](.env.example) with complete documentation and production guidelines for email and HTTPS security variables.
- **Test Coverage Expansion**:
  - Expanded test suite from 9 to 20 automated tests across `publications`, `accounts`, and `dashboard`, all passing in ~28.7s:
    - `publications/tests.py`: Added `PublicationOwnershipTestCase` verifying that deleting a user sets `publication.created_by` to `None` without deleting the publication, and that publications can be created without a user.
    - `accounts/tests.py`: Added `FormTagsFilterTestCase`, `PasswordResetWorkflowTestCase` (verifying form rendering without template syntax error, email dispatch to `mail.outbox`, and protection against user enumeration on non-existent emails), and `EmailAndSecurityConfigTestCase` (verifying configuration validation and proxy header parsing).
    - `dashboard/tests.py`: Expanded `DashboardAuthenticationTestCase` to exhaustively test all 21 dashboard views (11 main views and 10 detail views) for anonymous redirect to login and authenticated 200 OK.
  - Ran `manage.py check` (0 issues), `manage.py makemigrations --check --dry-run` (0 changes detected), and `manage.py check --deploy` (passed with 0 issues in simulated production environment).
- **Files Modified / Created**:
  - `publications/models.py` (modified)
  - `publications/migrations/0003_alter_publication_created_by.py` (created)
  - `accounts/templatetags/__init__.py` (created)
  - `accounts/templatetags/form_tags.py` (created)
  - `accounts/urls.py` (modified)
  - `templates/registration/password_reset_email.html` (created)
  - `rri_publications_dashboard/settings.py` (modified)
  - `rri_publications_dashboard/env.py` (modified)
  - `.env.example` (modified)
  - `publications/tests.py` (modified)
  - `accounts/tests.py` (modified)
  - `dashboard/tests.py` (modified)
- **Remaining Production Considerations**:
  - In production deployments, set `DEBUG=False`, configure valid SMTP credentials (`EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`), provide a 50+ character random `DJANGO_SECRET_KEY`, and enable `SECURE_SSL_REDIRECT=True` and `SECURE_HSTS_SECONDS=31536000` behind an HTTPS reverse proxy (with `USE_X_FORWARDED_PROTO=True` if proxying over TLS).

### Security - 2026-10-24

#### Task 5: Enforce Dashboard Authentication and Role-Based Authorization
- **Dashboard Authentication Enforcement**:
  - Protected all 21 class-based views in [`dashboard/views.py`](dashboard/views.py) with Django's `LoginRequiredMixin`.
  - Unauthenticated access to `/dashboard/` and all drilldowns now redirects safely to `accounts:login` (`/accounts/login/?next=...`).
  - Preserved public access to the institutional publications catalog (`publications:list`, `publications:publication_detail`) and authentication entry points (`accounts:login`, password reset).
- **Role-Based Access Control (RBAC)**:
  - Created [`accounts/permissions.py`](accounts/permissions.py) implementing `has_role`, `@role_required(*allowed_roles)` decorator, and `RoleRequiredMixin`.
  - Secured Web of Science ingestion endpoints (`publications:wos_upload`, `publications:wos_review`, `publications:wos_save`, and `publications:wos_success`) in [`publications/views.py`](publications/views.py) requiring `admin` or `user` roles (or staff/superuser).
  - Enforced server-side HTTP 403 Forbidden when authenticated users with insufficient permissions (`role="viewer"`) attempt to access or modify data via WoS endpoints.
  - Updated [`templates/publications/publications_list.html`](templates/publications/publications_list.html) to conditionally render the "+ Upload WoS File" action only for users with upload permissions (`admin`, `user`, staff, superuser).
- **Automated Security Test Suite**:
  - Added unit and integration tests across [`accounts/tests.py`](accounts/tests.py), [`dashboard/tests.py`](dashboard/tests.py), and [`publications/tests.py`](publications/tests.py) (9 tests total, all passing).
  - Verified anonymous user redirection across 11 core dashboard endpoints and 4 WoS endpoints.
  - Verified 403 Forbidden enforcement on `viewer` accounts attempting WoS upload, review, save, and success routes.
  - Verified authorized access (HTTP 200) for `admin` and `user` accounts on WoS upload, and `viewer` accounts on dashboard views.
  - Verified UI conditional rendering of action controls based on role permissions.
- **Files Modified / Created**:
  - `accounts/permissions.py` (created)
  - `dashboard/views.py` (modified)
  - `publications/views.py` (modified)
  - `templates/publications/publications_list.html` (modified)
  - `accounts/tests.py` (modified)
  - `dashboard/tests.py` (modified)
  - `publications/tests.py` (modified)
- **Remaining Security Gaps**:
  - SSL/HTTPS and Secure Cookies (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`) remain disabled for local HTTP development; must be enabled in production environments.
  - `CASCADE` deletion on `Publication.created_by`: deleting a user deletes all publications uploaded by that user. Should be migrated to `SET_NULL` or `PROTECT` in a dedicated migration.
  - Email SMTP backend for password resets remains unconfigured (causes 500 when users submit password reset form).

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
