# Technology Stack: RRI Publications Dashboard

## 1. Overview and Stack Architecture

The **RRI Publications Dashboard** is built on a server-rendered Django foundation paired with a modern utility-first CSS and reactive JavaScript frontend. This document inventories every technology, library, tool, and service identified in the codebase, detailing versions, declaration sources, actual verification status, architectural role, and modernization considerations.

```
+---------------------------------------------------------------------------------------+
|                                    Frontend Layer                                     |
|  - HTML: Django Templates (TemplateView / DetailView / formsets)                      |
|  - Styling: Tailwind CSS v4.3.0 + DaisyUI v5.5.23 (PostCSS 8.5.15)                   |
|  - Client Reactivity: Alpine.js v3.x (DOM state, sidebar toggles)                     |
|  - Visualization: Chart.js v4.x (Interactive canvas charts)                           |
|  - Icons: Lucide Icons v0.x (SVG iconography)                                         |
+---------------------------------------------------------------------------------------+
                                           |
+---------------------------------------------------------------------------------------+
|                                   Application Layer                                   |
|  - Runtime: Python 3.12 / 3.13                                                        |
|  - Core Framework: Django 6.0.6 (ASGI/WSGI)                                           |
|  - Query Filter Engine: django-filter 25.2                                            |
|  - Theme Integration: django-tailwind 4.5.0 + django-browser-reload 1.21.0            |
|  - Ingestion Utility: Custom TSV/Regex Parser (Python standard library `csv`, `re`)   |
+---------------------------------------------------------------------------------------+
                                           |
+---------------------------------------------------------------------------------------+
|                                    Data Layer                                         |
|  - Engine: SQLite 3 (file-based: `db.sqlite3`)                                        |
|  - Driver: Built-in Python `sqlite3` driver                                           |
|  - Migrations: Django native migration framework                                      |
+---------------------------------------------------------------------------------------+
                                           |
+---------------------------------------------------------------------------------------+
|                                Tooling & Build Layer                                  |
|  - Build Automation: GNU Make (`makefile`)                                            |
|  - Node Package Management: npm (`theme/static_src/package.json`)                      |
|  - Template Linting: djLint 1.40.8 (`.djlintrc`, `pyproject.toml`)                    |
|  - Python Linter: Ruff (configured in `pyproject.toml`, uninstalled in venv)          |
+---------------------------------------------------------------------------------------+
```

---

## 2. Comprehensive Technology Inventory

### 2.1 Backend Runtime and Core Framework

| Technology | Category | Declared / Installed Version | Declaration Location | Actual Usage Verified? | Purpose & Modules Dependent | Upgrade & Maintenance Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Python** | Runtime | `3.12.x` (system environment) | Implicit; tested with Python 3.12 | **Yes** (Virtualenv runtime) | Core language runtime for all backend apps | Supports Python 3.10 through 3.13. Tested in active venv under Linux. |
| **Django** | Web Framework | `6.0.6` | [`requirements.txt:9`](../../requirements.txt#L9) | **Yes** (`INSTALLED_APPS`, ORM, views) | Complete application architecture, ORM, URL routing, authentication, admin | Django 6.0 is the latest modern release. Code uses modern features like `BigAutoField` and class-based views. |
| **asgiref** | ASGI Interface | `3.11.1` | [`requirements.txt:2`](../../requirements.txt#L2) | **Yes** (Django core dependency) | Underpins Django's asynchronous request handling and ASGI server interface | Standard transitive dependency of Django. |
| **sqlparse** | SQL Parser | `0.5.5` | [`requirements.txt:33`](../../requirements.txt#L33) | **Yes** (Django core dependency) | Formats and parses SQL statements in Django management commands | Standard transitive dependency of Django. |
| **tzdata** | Timezone Data | `2026.2` | [`requirements.txt:35`](../../requirements.txt#L35) | **Yes** (Django timezone engine) | IANA time zone database for Django `USE_TZ = True` | Standard transitive dependency. |

---

### 2.2 Django Extensions and Plugins

| Extension | Declared / Installed Version | Declaration Location | Verified In Code? | Purpose & Implementation Reference | Maintenance & Alternatives |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **django-filter** | `25.2` | [`requirements.txt:11`](../../requirements.txt#L11), [`settings.py:31`](../../rri_publications_dashboard/settings.py#L31) | **Yes** | Powers dynamic URL query parameter filtering across catalog and dashboard views ([`dashboard/filters.py:27`](../../dashboard/filters.py#L27)) | Current major release (25.2). Essential to the project; highly maintained by the Jazzband community. |
| **django-tailwind** | `4.5.0` | [`requirements.txt:12`](../../requirements.txt#L12), [`settings.py:25`](../../rri_publications_dashboard/settings.py#L25) | **Yes** | Orchestrates Tailwind CSS build processes and template tag `{% tailwind_css %}` ([`dashboard/templates/base.html:15`](../../dashboard/templates/base.html#L15)) | Works with standalone Tailwind or npm. The repo uses npm via `theme/static_src`. |
| **django-browser-reload** | `1.21.0` | [`requirements.txt:10`](../../requirements.txt#L10), [`settings.py:37`](../../rri_publications_dashboard/settings.py#L37) | **Yes** | Automatically reloads the browser when templates or static files change during local development | Development only. Properly gated by `if DEBUG:` in [`settings.py:36-39`](../../rri_publications_dashboard/settings.py#L36-L39) and [`urls.py:21-24`](../../rri_publications_dashboard/urls.py#L21-L24). |
| **django-tables2** | *Not in requirements* | None | **Phantom / Unused Import** | Imported in [`dashboard/tables.py:1`](../../dashboard/tables.py#L1), but `PublicationTable` is never instantiated or imported in views | **Dead Code**: Should be removed from `dashboard/tables.py` or formally declared in `requirements.txt` if intended for use. |

---

### 2.3 Database Layer

| Component | Technology | Version | Configuration Location | Verification | Usage Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Database Engine** | SQLite 3 | Embedded | [`rri_publications_dashboard/settings.py:81-86`](../../rri_publications_dashboard/settings.py#L81-L86) | **Verified** (`db.sqlite3`, 232 KB) | Default local datastore for development and testing. Contains all 20 standard and custom tables. |
| **DB Driver** | Python `sqlite3` | Built-in | Standard Library | **Verified** | Standard native driver; requires zero external system package dependencies. |
| **Production DB Readiness** | PostgreSQL / MySQL | *Not configured* | Mentioned in [`README.MD:16`](../../README.MD#L16) | **Unverified / Absent** | Production database drivers (`psycopg` or `mysqlclient`) are neither installed nor configured in `settings.py`. |

---

### 2.4 Frontend CSS and Styling Pipeline

| Package | Version | Configuration Location | Verification | Implementation & Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Tailwind CSS** | `4.3.0` | [`theme/static_src/package.json:25`](../../theme/static_src/package.json#L25) | **Verified** | Core utility-first CSS framework. Compiled via PostCSS into [`theme/static/css/dist/styles.css`](../../theme/static/css/dist/styles.css) (144 KB). |
| **DaisyUI** | `5.5.23` | [`theme/static_src/package.json:18`](../../theme/static_src/package.json#L18) | **Verified** | Component layer loaded as `@plugin "daisyui";` in [`styles.css:2`](../../theme/static_src/src/styles.css#L2). Supplies `stats`, `card`, `table`, `btn`, `badge`, `navbar` classes. |
| **@tailwindcss/postcss** | `4.3.0` | [`theme/static_src/package.json:17`](../../theme/static_src/package.json#L17) | **Verified** | Official Tailwind v4 PostCSS plugin. |
| **PostCSS** | `8.5.15` | [`theme/static_src/package.json:20`](../../theme/static_src/package.json#L20) | **Verified** | PostCSS transformation engine executing in Node.js build pipeline. |
| **postcss-cli** | `11.0.1` | [`theme/static_src/package.json:21`](../../theme/static_src/package.json#L21) | **Verified** | Command-line interface executing `npm run build` and `npm run dev`. |
| **postcss-simple-vars** | `7.0.1` | [`theme/static_src/package.json:23`](../../theme/static_src/package.json#L23) | **Verified** | PostCSS variable expansion plugin. |
| **postcss-nested** | `7.0.2` | [`theme/static_src/package.json:22`](../../theme/static_src/package.json#L22) | **Verified** | Enables CSS nesting rules. |
| **rimraf** | `6.1.3` | [`theme/static_src/package.json:24`](../../theme/static_src/package.json#L24) | **Verified** | Utility used in `npm run build:clean` to remove `../static/css/dist`. |
| **cross-env** | `10.1.0` | [`theme/static_src/package.json:19`](../../theme/static_src/package.json#L19) | **Verified** | Cross-platform environment variable setting for `NODE_ENV=production`. |

---

### 2.5 Frontend JavaScript Libraries (Vendor Bundles)

Static JavaScript libraries are vendor-bundled directly in [`static/js/`](../../static/js/) rather than loaded via CDN, ensuring complete offline development capability:

| Library | Distribution | Local Path | Verified In Code? | Purpose & Application |
| :--- | :--- | :--- | :--- | :--- |
| **Alpine.js** | Minified script bundle | [`static/js/alpine.min.js`](../../static/js/alpine.min.js) | **Yes** | Client-side reactive UI state: sidebar collapse toggling, mobile drawer visibility, localStorage persistence (`dashboard/templates/base.html:70-84`) |
| **Chart.js** | Minified script bundle | [`static/js/chart.min.js`](../../static/js/chart.min.js) | **Yes** | Canvas charts rendering bar charts and trend lines across dashboard views and publication catalog (`dashboard/templates/dashboard/dashboard.html:98-164`) |
| **Lucide Icons** | Minified script bundle | [`static/js/lucide.min.js`](../../static/js/lucide.min.js) | **Yes** | Replaces `<i data-lucide="...">` elements with inline SVG iconography on DOM load and Alpine transitions |

---

### 2.6 Declared But Unused or Transitive Dependencies

The project's [`requirements.txt`](../../requirements.txt) contains several packages that are either legacy remnants, unused tooling, or transitive dependencies of previous installations:

| Package | Version | Source / Status | Verification Result | Recommended Action |
| :--- | :--- | :--- | :--- | :--- |
| **requests** | `2.34.2` | `requirements.txt:30` | **Unused** (0 imports in project) | Retain only if external API integrations are introduced; otherwise remove. |
| **arrow** | `1.4.0` | `requirements.txt:1` | **Unused** (0 imports in project) | Date manipulation is handled using standard `datetime` and Django ORM. Remove. |
| **cookiecutter** | `2.7.1` | `requirements.txt:7` | **Tooling Artifact** | Installed by `django-tailwind` during initial theme app generation (`python manage.py tailwind init`). Safe to remove from runtime dependencies. |
| **pytailwindcss** | `0.3.1` | `requirements.txt:26` | **Redundant** | Standalone Python Tailwind binary wrapper. The project uses standard Node.js/npm for Tailwind v4. |
| **honcho** | `2.0.0` | `requirements.txt:15` | **Unused** | Procfile/multi-process manager. Not referenced in `makefile` or root files. |
| **binaryornot** | `0.6.0` | `requirements.txt:3` | **Transitive** | Transitive dependency of `cookiecutter`. |
| **Jinja2** / **MarkupSafe** | `3.1.6` / `3.0.3` | `requirements.txt:17, 21` | **Transitive** | Transitive dependencies of `cookiecutter`. Django uses its own `DjangoTemplates` backend. |
| **python-slugify** | `8.0.4` | `requirements.txt:28` | **Transitive** | Transitive dependency of `cookiecutter`. |
| **rich** / **markdown-it-py** / **Pygments** | `15.0.0` / `4.2.0` / `2.20.0` | `requirements.txt:31, 20, 25` | **Tooling** | Dependencies of `djlint` CLI. |
| **cssbeautifier** / **jsbeautifier** | `2.0.3` / `2.0.3` | `requirements.txt:8, 18` | **Tooling** | Dependencies of `djlint`. |

---

### 2.7 Code Quality and Linting Tools

| Tool | Version | Configuration File | Verified Execution? | Description |
| :--- | :--- | :--- | :--- | :--- |
| **djLint** | `1.40.8` | [`.djlintrc:1-4`](../../.djlintrc#L1-L4), [`pyproject.toml:1-3`](../../pyproject.toml#L1-L3) | **Configured** | HTML template linter and formatter tailored for Django templates. Configured to ignore rules `H030`, `T003`, `H031`, etc. |
| **Ruff** | *Not installed in venv* | [`pyproject.toml:4-5`](../../pyproject.toml#L4-L5) | **Configured Only** | Fast Python linter configured with ignore list (`RUF012`, `RUF010`, `BLE001`, `TRY004`, etc.), but `ruff` is not declared in `requirements.txt`. |

---

### 2.8 Deployment and Infrastructure Components

| Component | Target Technology | Verification Status | Code Reference | Findings & Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Web Server** | Apache (`mod_wsgi` / `mod_proxy`) | **Broken / Missing Script** | [`makefile:142-160`](../../makefile#L142-L160) | Makefile targets `make conf` and `make deploy-server` require `generate_apache_conf.py`, which is missing from the repository. |
| **Process Manager** | Systemd | **Inferred Only** | [`makefile:159`](../../makefile#L159) | Makefile issues `sudo systemctl restart apache2`. No systemd service unit files exist in the repository. |
| **Task Scheduler** | `django-crontab` | **Broken / Uninstalled** | [`makefile:130-138`](../../makefile#L130-L138) | Makefile targets `cron_add`, `cron_remove`, `cron_show` invoke `python manage.py crontab`, but `django-crontab` is neither installed nor configured in `INSTALLED_APPS`. |
| **CI/CD Pipeline** | GitHub Actions / GitLab CI | **Absent** | Repository root | No `.github/workflows/` or `.gitlab-ci.yml` directories exist. Deployment and testing are currently manual. |

