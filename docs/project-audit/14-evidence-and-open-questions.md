# Evidence Register and Open Questions: RRI Publications Dashboard

## 1. Traceable Evidence Register

This register correlates every major finding, architectural conclusion, and security assessment to specific source code, migration files, or executed CLI commands.

| Finding / Claim | Category | Evidence Source | Relative File Path & Line Numbers | Confidence Level | Remaining Uncertainty | Verification Method |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`SECRET_KEY` is hardcoded with insecure default** | Security | Django settings file | [`rri_publications_dashboard/settings.py:13`](../../rri_publications_dashboard/settings.py#L13) | **Confirmed** | None | Inspected file; verified with `manage.py check --deploy` warning `(security.W009)` |
| **`DEBUG=True` and `ALLOWED_HOSTS=['*']` hardcoded** | Security | Django settings file | [`rri_publications_dashboard/settings.py:14-15`](../../rri_publications_dashboard/settings.py#L14-L15) | **Confirmed** | None | Inspected file; verified with `manage.py check --deploy` warning `(security.W018)` |
| **All 21 dashboard views lack authentication** | Security | View classes in dashboard | [`dashboard/views.py:17-2112`](../../dashboard/views.py#L17-L2112) | **Confirmed** | None | Verified all 21 classes inherit `TemplateView`; 0 `LoginRequiredMixin` imports |
| **`CustomUser.role` is completely unenforced** | Security / Auth | Full repository search | [`accounts/models.py:13`](../../accounts/models.py#L13), `dashboard/views.py` | **Confirmed** | None | `grep -rn "role" dashboard/ publications/ accounts/` shows 0 checks on `request.user.role` |
| **`article_number` exists in DB but missing in `models.py`** | Data / Schema | Migration 0002 & `models.py` | [`publications/migrations/0002_...py:19-21`](../../publications/migrations/0002_alter_publication_options_publication_article_number.py#L19-L21), [`publications/models.py:125-200`](../../publications/models.py#L125-L200) | **Confirmed** | None | Verified with `python3 -c "import sqlite3; PRAGMA table_info"` and `makemigrations --dry-run` |
| **`STATIC_ROOT` is undefined, breaking `collectstatic`** | Configuration | Settings & command run | [`rri_publications_dashboard/settings.py:104-110`](../../rri_publications_dashboard/settings.py#L104-L110) | **Confirmed** | None | Executed `python manage.py collectstatic --dry-run`; threw `ImproperlyConfigured` |
| **0 automated tests exist in repository** | Quality | Test files & test runner | [`accounts/tests.py`](../../accounts/tests.py), [`dashboard/tests.py`](../../dashboard/tests.py), [`publications/tests.py`](../../publications/tests.py) | **Confirmed** | None | Executed `python manage.py test`; returned `Found 0 test(s). Ran 0 tests in 0.000s` |
| **Author duplication forced in-memory merging** | Performance | Ingestion view & dashboard view | [`publications/views.py:334-340`](../../publications/views.py#L334-L340), [`dashboard/views.py:358-387`](../../dashboard/views.py#L358-L387) | **Confirmed** | None | Followed code path: `form.save()` creates new row; `AuthorsView` merges by `(first_name, last_name)` dict |
| **`requests`, `arrow`, `honcho`, `cookiecutter` are unused** | Dependencies | Dependency file & code search | [`requirements.txt:1, 7, 15, 30`](../../requirements.txt#L1) | **Confirmed** | None | Executed `grep -rn "import requests\|import arrow" accounts dashboard publications theme` (0 matches) |
| **`django-tables2` is phantom code** | Dependencies | Table file & requirements | [`dashboard/tables.py:1`](../../dashboard/tables.py#L1), [`requirements.txt`](../../requirements.txt) | **Confirmed** | None | `tables.py` imports `django_tables2`, which is neither in `requirements.txt` nor imported in views |
| **`views_dashboard.py` is dead code** | Architecture | Publications views & urls | [`publications/views_dashboard.py:1-109`](../../publications/views_dashboard.py#L1-L109), [`publications/urls.py`](../../publications/urls.py) | **Confirmed** | None | `grep -rn "views_dashboard"` confirmed unreferenced; target template does not exist |
| **Orphan manual creation & edit templates exist** | Features | Template directory & urls | [`templates/publications/create_publication.html`](../../templates/publications/create_publication.html), [`edit_publication.html`](../../templates/publications/edit_publication.html) | **Confirmed** | Intent of original developer | Found complete form templates with vanilla JS author cloner, but 0 views/routes wired up |
| **`generate_apache_conf.py` missing from repository** | Deployment | Makefile & file system | [`makefile:146`](../../makefile#L146) | **Confirmed** | None | Executed `ls generate_apache_conf.py`; file does not exist |
| **`django-crontab` commands in makefile are broken** | Deployment | Makefile & requirements | [`makefile:130-138`](../../makefile#L130-L138), [`requirements.txt`](../../requirements.txt) | **Confirmed** | None | Package not in `requirements.txt` or `INSTALLED_APPS` |
| **DOCTYPE duplicated in root base layout** | UI / Markup | Root HTML template | [`dashboard/templates/base.html:1-6, 79-80`](../../dashboard/templates/base.html#L1-L6) | **Confirmed** | None | Read lines 1-6 and 79-80; confirmed duplicated opening and closing tags |
| **Pagination drops active filters** | UI / Filtering | Pagination partial | [`dashboard/templates/components/pagination.html:20, 27, 43`](../../dashboard/templates/components/pagination.html#L20) | **Confirmed** | None | Inspected template; links only append `&search={{ request.GET.search }}` |
| **Unbounded WoS upload and session bloat** | Security / DoS | File upload view | [`publications/views.py:201-218`](../../publications/views.py#L201-L218) | **Confirmed** | None | Code reads entire uploaded file into memory and serializes parsed dicts to `request.session` |
| **CASCADE deletion vulnerability on publication creator** | Data Integrity | Publication model definition | [`publications/models.py:182-185`](../../publications/models.py#L182-L185) | **Confirmed** | None | Code shows `created_by = models.ForeignKey(..., on_delete=models.CASCADE)` |

---

## 2. Explicit List of Open Questions

The following questions cannot be resolved from the repository contents alone and require human institutional clarification:

1. **Target Production Hosting Infrastructure**:
   - The Makefile suggests Apache 2 with `mod_wsgi` (`/etc/apache2/sites-available`), but references a missing script `generate_apache_conf.py`.
   - *Question for Stakeholders*: Will the production deployment use Apache on virtual machines, or will it be containerized using Docker with Gunicorn/Uvicorn behind Nginx?
2. **Database Engine in Production**:
   - The repository only contains local SQLite configuration (`db.sqlite3`).
   - *Question for Stakeholders*: Is RRI intending to deploy on PostgreSQL or MySQL for production, and are credentials/hosts already provisioned?
3. **Institutional Email Service (SMTP)**:
   - Password reset functionality currently crashes with a 500 error because no SMTP server is configured.
   - *Question for Stakeholders*: Does RRI maintain an institutional SMTP relay (e.g. `mail.rri.res.in`), or will an external provider (SendGrid, AWS SES) be configured?
4. **Fate of Orphaned Manual Entry Forms**:
   - Complete templates for creating and editing publications manually (`create_publication.html`, `edit_publication.html`) exist in the template folder with extensive vanilla JS author cloning.
   - *Question for Stakeholders*: Were these templates abandoned because all publications must originate from Web of Science, or should views and routes be created to enable manual entry?
5. **Dashboard Public vs Internal Privacy Policy**:
   - Currently, all 21 analytical dashboard views are accessible without authentication.
   - *Question for Stakeholders*: Is the dashboard intended to be a public-facing institutional showcase for RRI, or an internal administrative analytics tool requiring login?

---

## 3. Comprehensive Repository Inspection Log

### 3.1 Inspected Areas
- **Project Configuration**:
  - `manage.py`, `rri_publications_dashboard/settings.py`, `rri_publications_dashboard/urls.py`, `wsgi.py`, `asgi.py`.
  - `.env.example`, `.env`, `makefile`, `requirements.txt`, `pyproject.toml`, `.djlintrc`, `.gitignore`, `exclude_me.txt`.
- **Applications & Python Code**:
  - `accounts/`: `models.py`, `views.py`, `forms.py`, `admin.py`, `apps.py`, `urls.py`, `tests.py`, `migrations/0001_initial.py`.
  - `publications/`: `models.py`, `views.py`, `views_dashboard.py`, `forms.py`, `admin.py`, `apps.py`, `urls.py`, `tests.py`, `utils/wos_parser.py`, `templatetags/json_extras.py`, `migrations/0001_initial.py`, `migrations/0002_alter_publication_options_publication_article_number.py`.
  - `dashboard/`: `models.py`, `views.py` (all 2,112 lines), `filters.py`, `tables.py`, `context_processors.py`, `admin.py`, `apps.py`, `urls.py`, `tests.py`.
  - `theme/`: `apps.py`, `static_src/package.json`, `package-lock.json`, `postcss.config.js`, `src/styles.css`, `static/css/dist/styles.css`.
- **Templates & Static Assets**:
  - All 15 templates under `templates/publications/` and `templates/registration/`.
  - All 33 templates under `dashboard/templates/` (`base.html`, `components/*`, `dashboard/*`, `tables/*`).
  - Static vendor scripts: `static/js/alpine.min.js`, `chart.min.js`, `lucide.min.js`.
- **Database**:
  - Verified table list and column PRAGMA schema in `db.sqlite3` via Python `sqlite3`.

### 3.2 Excluded Areas
- Python virtual environment internals (`venv/lib/`, `venv/include/`, `venv/bin/`).
- Python bytecode caches (`__pycache__/` and `*.pyc`).
- Git version control metadata (`.git/`).
- Compiled Node modules (ignored via `.gitignore`).

