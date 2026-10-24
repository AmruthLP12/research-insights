# Improvement Roadmap: RRI Publications Dashboard

## 1. Roadmap Overview and Phasing Strategy

This roadmap outlines a structured, phased modernization plan for the RRI Publications Dashboard. It prioritizes urgent security risks and schema integrity issues before addressing architectural debt, performance optimizations, and new features.

```
+---------------------------------------------------------------------------------------+
|  Phase 0: Immediate Security & Data-Integrity Fixes (Urgent / Next Sprint)            |
|  - Load SECRET_KEY, DEBUG, and ALLOWED_HOSTS from environment                        |
|  - Restore article_number to Publication model (resolve schema drift)                 |
|  - Add STATIC_ROOT to settings.py (unblock collectstatic)                             |
|  - Change Publication.created_by on_delete from CASCADE to PROTECT                    |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|  Phase 1: Low-Risk Stability & Hygiene Improvements (Short-Term)                      |
|  - Enforce RBAC on WoS upload, review, and save endpoints                             |
|  - Fix duplicate DOCTYPE in dashboard/templates/base.html                             |
|  - Fix pagination filter drop bug in pagination.html                                  |
|  - Prune unused packages from requirements.txt and delete dead code                   |
|  - Configure console email backend for development password resets                    |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|  Phase 2: Structural Architecture & Quality Improvements (Medium-Term)                |
|  - Build automated test suite (pytest-django) for parser, filters, and views          |
|  - Implement database-level Author canonicalization (eliminate in-memory merging)     |
|  - Decompose monolithic 2,112-line dashboard/views.py into a modular view package     |
|  - Add database indexes on frequently queried Publication fields                      |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|  Phase 3: UI/UX & Functional Enhancements (Feature Polish)                           |
|  - Implement manual Publication Create & Edit views (wire up orphan templates)        |
|  - Add CSV and Excel export capabilities for filtered publication sets                |
|  - Harmonize form styles with DaisyUI design tokens across all views                  |
|  - Implement dark mode theme toggle switch in navbar                                  |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|  Phase 4: Scalability & Enterprise Modernization (Long-Term)                          |
|  - Migrate SQLite datastore to PostgreSQL with connection pooling                     |
|  - Move Web of Science file ingestion to an asynchronous worker queue (Celery/Redis)  |
|  - Implement headless REST API endpoints (Django Ninja / DRF) for institutional APIs   |
+---------------------------------------------------------------------------------------+
```

---

## 2. Detailed Work Package Specifications

### Phase 0: Immediate Security and Data-Integrity Concerns

#### Item 0.1: Environment Variable Decoupling & Secret Key Security
- **Priority**: **Critical (P0)**
- **Problem**: Insecure `SECRET_KEY`, `DEBUG = True`, and wildcard `ALLOWED_HOSTS = ['*']` are hardcoded in source code ([`settings.py:13-15`](../../rri_publications_dashboard/settings.py#L13-L15)).
- **Proposed Change**: Install `django-environ`. Refactor `settings.py` to ingest values from `.env`. Refuse startup in production if `DJANGO_SECRET_KEY` is undefined or matches insecure defaults.
- **Expected Benefit**: Mitigates session forgery, traceback information disclosure, and Host header poisoning.
- **Risk**: Low. Local development retains fallback defaults.
- **Complexity**: **Small** (1-2 hours).
- **Validation**: Run `python manage.py check --deploy`. Verify `settings.py` reads `.env` dynamically.

#### Item 0.2: Reconcile Model Schema Drift (`article_number`)
- **Priority**: **Critical (P0)**
- **Problem**: Migration `0002` added column `article_number` to `publications_publication`, but the field was accidentally omitted from `Publication` in [`publications/models.py`](../../publications/models.py). Running `makemigrations` prompts dropping the column.
- **Proposed Change**: Add `article_number = models.CharField(max_length=50, blank=True, null=True)` to `Publication`.
- **Expected Benefit**: Prevents accidental data destruction and unblocks clean future migrations.
- **Risk**: Extremely low.
- **Complexity**: **Small** (15 minutes).
- **Validation**: Execute `python manage.py makemigrations --dry-run` and verify "No changes detected".

#### Item 0.3: Fix Static Files Deployment Configuration
- **Priority**: **Critical (P0)**
- **Problem**: Missing `STATIC_ROOT` in [`settings.py`](../../rri_publications_dashboard/settings.py) causes `python manage.py collectstatic` to crash.
- **Proposed Change**: Add `STATIC_ROOT = BASE_DIR / "staticfiles"` to `settings.py`. Ensure `staticfiles/` is ignored in `.gitignore`.
- **Expected Benefit**: Unblocks deployment pipelines and production web server static file serving.
- **Risk**: None.
- **Complexity**: **Small** (15 minutes).
- **Validation**: Execute `python manage.py collectstatic --noinput` successfully.

#### Item 0.4: Eliminate Catastrophic CASCADE Deletion on `Publication.created_by`
- **Priority**: **Critical (P0)**
- **Problem**: `Publication.created_by` specifies `on_delete=models.CASCADE` ([`publications/models.py:182-185`](../../publications/models.py#L182-L185)). Deleting a user in Django Admin permanently destroys all publications created by that user.
- **Proposed Change**: Alter to `on_delete=models.PROTECT`. Generate and apply migration.
- **Expected Benefit**: Protects institutional research records from accidental administrative deletion.
- **Risk**: Low. Prevents user deletion if publications are associated.
- **Complexity**: **Small** (30 minutes).
- **Validation**: Attempt to delete a user with linked publications in admin; verify Django blocks deletion.

---

### Phase 1: Low-Risk Stability & Hygiene Improvements

#### Item 1.1: Role-Based Authorization Enforcement
- **Priority**: **High (P1)**
- **Problem**: `CustomUser.role` is defined (`admin`, `user`, `viewer`) but completely unenforced. A "viewer" account can currently upload and modify publication records.
- **Proposed Change**: Create a custom decorator `@role_required("admin", "user")` and apply it to `wos_upload`, `wos_review`, and `wos_save`.
- **Expected Benefit**: Enforces least-privilege access and safeguards data modification.
- **Complexity**: **Small** (2-4 hours).
- **Validation**: Verify that users with role `"viewer"` receive an HTTP 403 Forbidden when accessing `/publications/wos/upload/`.

#### Item 1.2: Fix Filter Drop in Pagination Component
- **Priority**: **High (P1)**
- **Problem**: [`components/pagination.html`](../../dashboard/templates/components/pagination.html) only appends `&search={{ request.GET.search }}` to pagination links, permanently dropping active date and category filters upon page navigation.
- **Proposed Change**: Implement a template tag (e.g., `{% query_transform page=page_obj.next_page_number %}`) that copies all current GET parameters while updating the `page` key.
- **Expected Benefit**: Seamless multi-page browsing of filtered publication sets.
- **Complexity**: **Small** (1-2 hours).
- **Validation**: Filter publications by document type and date range, click page 2, and verify filters remain active.

#### Item 1.3: Dead Code and Unused Package Purge
- **Priority**: **Medium (P1)**
- **Problem**: Unused libraries (`requests`, `arrow`, `cookiecutter`, `honcho`, `pytailwindcss`) in `requirements.txt`; dead files `publications/views_dashboard.py` and `dashboard/tables.py`.
- **Proposed Change**: Prune `requirements.txt` and delete dead source files.
- **Expected Benefit**: Cleaner repository, faster package installation, smaller attack surface.
- **Complexity**: **Small** (1 hour).
- **Validation**: Verify application builds and runs cleanly after removal.

#### Item 1.4: HTML Doctype Fix in Base Layout
- **Priority**: **Medium (P1)**
- **Problem**: Duplicated `<!doctype html>` and `<html>` tags in [`dashboard/templates/base.html:1-6`](../../dashboard/templates/base.html#L1-L6).
- **Proposed Change**: Remove duplicated opening tags and matching closing tags.
- **Complexity**: **Small** (15 minutes).
- **Validation**: Validate generated HTML with W3C validator.

---

### Phase 2: Structural Architecture & Quality Improvements

#### Item 2.1: Establish Automated Test Suite
- **Priority**: **High (P2)**
- **Problem**: 0% automated test coverage across all modules.
- **Proposed Change**: Add `pytest` and `pytest-django` to dev dependencies. Create unit tests for `wos_parser.py`, `DynamicFilter`, metric calculations, and authentication flows.
- **Expected Benefit**: Safe future refactoring and regression prevention.
- **Complexity**: **Medium** (2-3 days).
- **Validation**: Execute `pytest` with 80%+ coverage on `publications` and `dashboard/filters.py`.

#### Item 2.2: Database-Level Author Canonicalization
- **Priority**: **High (P2)**
- **Problem**: `wos_save` creates duplicate `Author` records for every paper, requiring `dashboard/views.py` to pull thousands of rows into Python memory for merging and sorting.
- **Proposed Change**:
  1. Create a data migration script to deduplicate existing `Author` records by `(first_name, last_name)`.
  2. Update `wos_save` to match existing authors using `get_or_create` or a disambiguation heuristic.
  3. Refactor `AuthorsView` to execute standard SQL `GROUP BY` and SQL `ORDER BY`.
- **Expected Benefit**: Reduces view execution time from hundreds of milliseconds to under 20ms; cuts memory consumption by 90%.
- **Complexity**: **Large** (3-5 days).
- **Validation**: Verify author leaderboard rankings match pre-migration counts exactly.

#### Item 2.3: Decompose Monolithic `dashboard/views.py`
- **Priority**: **Medium (P2)**
- **Problem**: 2,112-line single file containing 21 CBVs with duplicated aggregation logic.
- **Proposed Change**: Convert `dashboard/views.py` into a package: `dashboard/views/` containing `home.py`, `authors.py`, `journals.py`, `collaborations.py`, `trends.py`, and `mixins.py`.
- **Expected Benefit**: High maintainability, easier code review, clear module boundaries.
- **Complexity**: **Medium** (1-2 days).
- **Validation**: All URL patterns continue resolving without route regressions.

---

### Phase 3: UI/UX & Functional Enhancements

#### Item 3.1: Implement Manual Publication Create & Edit Views
- **Priority**: **Medium (P3)**
- **Problem**: Templates `create_publication.html` and `edit_publication.html` exist with functional JavaScript but are not wired up to views or URLs.
- **Proposed Change**: Implement `PublicationCreateView` and `PublicationUpdateView` with `AuthorFormSet` handling.
- **Expected Benefit**: Allows library staff to manually record non-indexed publications or make quick corrections without re-uploading WoS files.
- **Complexity**: **Medium** (2 days).

#### Item 3.2: Export to CSV and Excel
- **Priority**: **Medium (P3)**
- **Problem**: Users cannot export filtered publication lists for institutional reporting.
- **Proposed Change**: Add an "Export to CSV" button on `publications:list` streaming filtered records.
- **Complexity**: **Small** (1 day).

---

### Phase 4: Scalability & Enterprise Modernization

#### Item 4.1: Production PostgreSQL Migration
- **Priority**: **Low / Deployment Dependent (P4)**
- **Problem**: SQLite file locking prohibits concurrent write operations during batch imports.
- **Proposed Change**: Add `psycopg[binary]` to requirements. Configure `DATABASES` in `settings.py` to support PostgreSQL via `DATABASE_URL`.
- **Expected Benefit**: True multi-user concurrency, connection pooling, enterprise backup tooling.
- **Complexity**: **Medium** (1-2 days).

#### Item 4.2: Asynchronous File Processing Queue
- **Priority**: **Low (P4)**
- **Problem**: Large WoS files risk HTTP gateway timeouts during synchronous parsing.
- **Proposed Change**: Integrate Celery or Django-Q with Redis to parse export files in the background.
- **Complexity**: **Large** (3-4 days).

