# Glossary and Developer Guide: RRI Publications Dashboard

## 1. Domain and Technical Glossary

| Term | Domain Context | Meaning / Application Role |
| :--- | :--- | :--- |
| **Bibliometrics** | Academic Science | The quantitative analysis of scientific publications, citation counts, journal prestige, and co-authorship networks. |
| **Web of Science (WoS)** | Academic Indexing | A global scientific citation indexing database published by Clarivate Analytics. The primary data source ingested by this system. |
| **Full Record TSV** | Data Format | A tab-separated text export (`.txt`) from Web of Science containing tagged bibliographic fields (`TI`, `SO`, `PY`, `AF`, `C1`, `DI`). |
| **C1 Address Block** | WoS Syntax | A specialized address format pairing authors with institutions, e.g. `[Author A; Author B] Raman Res Inst, Bangalore, India`. |
| **Impact Factor (IF)** | Scientometrics | The Journal Citation Reports (JCR) measure reflecting the yearly average number of citations to recent articles published in that journal. |
| **DOI** | Publishing Standards | Digital Object Identifier (e.g. `10.1103/PhysRevLett.120.010401`), providing a persistent URI link to the published article. |
| **Collaboration Scope** | Institutional Analytics | Classification of research co-authorship: `National` (within India), `International` (global co-authors), `Departmental` (internal only). |
| **RRI Role** | Institutional HR | Categorization of authors: `Faculty`, `Retired Faculty`, `Adjunct Faculty`, `Research Scholar`, `PDF`, `RA`, `Staff`, or `External`. |
| **DynamicFilter** | Application Architecture | Custom filter class ([`dashboard/filters.py`](../../dashboard/filters.py)) extending `django-filter` to generate runtime querysets from CBV attributes. |
| **AuthorAffiliation** | Data Modeling | Explicit junction model linking an `Author` and an `Affiliation` to a specific `Publication` with an `is_primary` flag. |
| **In-Memory Merging** | Code Architecture | Python-level grouping and deduplication in `dashboard/views.py` used to aggregate multiple duplicate `Author` records. |

---

## 2. Verified Local Development Setup Guide

### 2.1 Prerequisites
- **Python**: Version `3.10`, `3.11`, or `3.12` installed.
- **Node.js & npm**: Node.js LTS (v18+) and npm installed.
- **Git** and **GNU Make** (on Linux/macOS).

### 2.2 Step-by-Step Setup Instructions

```bash
# 1. Clone the repository and navigate into the workspace root
cd research-insights

# 2. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Node.js dependencies for Tailwind CSS v4 and DaisyUI 5
cd theme/static_src
npm install
cd ../..

# 5. Create local environment configuration file
cp .env.example .env

# 6. Apply database migrations to local SQLite datastore
python manage.py migrate

# 7. Create an administrative superuser account
python manage.py createsuperuser

# 8. Compile Tailwind CSS (one-time build or watcher)
# To build once:
python manage.py tailwind build

# 9. Start the development server
python manage.py runserver 0.0.0.0:9000
```

> [!TIP]
> On Linux and macOS systems with GNU Make installed, steps 2 through 4 can be executed via `make create_venv`, `make install_packages`, and `make tailwind-install`.

---

## 3. Standard Operational Commands

| Task | GNU Make Command (Linux/macOS) | Direct Django / CLI Command | Verification Status |
| :--- | :--- | :--- | :--- |
| **Run Development Server** | `make run` | `python manage.py runserver 0.0.0.0:9000` | **Verified working** |
| **Tailwind Watcher** | `make tailwind` | `python manage.py tailwind start` | **Verified working** |
| **Compile Tailwind CSS** | `make tailwind-build` | `python manage.py tailwind build` | **Verified working** |
| **Run Both (Dev-All)** | `make dev-all` | Run Tailwind watcher in terminal 1, runserver in terminal 2 | **Verified working** |
| **Apply Migrations** | `make migrate` | `python manage.py migrate` | **Verified working** |
| **Show Migrations** | `make showmigrations` | `python manage.py showmigrations` | **Verified working** |
| **Execute Tests** | `make test` | `python manage.py test` | **Verified working (0 tests found)** |
| **Django Shell** | `make shell` | `python manage.py shell` | **Verified working** |
| **Collect Static Files** | `make collectstatic` | `python manage.py collectstatic --noinput` | **Fails** (Requires `STATIC_ROOT` in `settings.py`) |
| **Apache Config Generator**| `make conf` | `python generate_apache_conf.py` | **Fails** (Script missing from repo) |
| **Cron Job Management** | `make cron_add` | `python manage.py crontab add` | **Fails** (`django-crontab` uninstalled) |

---

## 4. Developer How-To Guide: Common Code Changes

### 4.1 How to Add a New Filter to a Dashboard View
1. Open the target view class in [`dashboard/views.py`](../../dashboard/views.py).
2. To filter by exact match choices (e.g. `collaboration_type`), append the model field name to `exact_filters`:
   ```python
   exact_filters = ["document_type", "collaboration_type"]
   ```
3. To add a text search field across a related entity, append the ORM lookup path to `search_fields`:
   ```python
   search_fields = ["title", "journal__name", "doi", "authors__last_name"]
   ```
4. To add date range bounds (`_from` and `_to`), add the date field to `date_filters`:
   ```python
   date_filters = ["date_published"]
   ```
5. `DynamicFilter` automatically constructs form controls with `onchange="this.form.submit()"` and applies lookups to `self.qs`.

### 4.2 How to Add a New Dashboard View
1. Create a new `TemplateView` subclass in [`dashboard/views.py`](../../dashboard/views.py):
   ```python
   class ResearchGrantsView(TemplateView):
       template_name = "dashboard/grants.html"
       paginate_by = 10
       # Declare filter attributes
       search_fields = ["title"]
       
       def get_context_data(self, **kwargs):
           context = super().get_context_data(**kwargs)
           # Construct queryset, apply DynamicFilter, paginate, return context
           return context
   ```
2. Register the URL pattern in [`dashboard/urls.py`](../../dashboard/urls.py):
   ```python
   path("grants/", views.ResearchGrantsView.as_view(), name="grants"),
   ```
3. Add the navigation item into [`dashboard/context_processors.py`](../../dashboard/context_processors.py) under the desired menu section:
   ```python
   {
       "title": "Research Grants",
       "url": reverse("dashboard:grants"),
       "url_name": "grants",
       "icon": "award",
   }
   ```
4. Create the template in `dashboard/templates/dashboard/grants.html` extending `"base.html"` and including `components/page_header.html`, `components/filter_bar.html`, and `components/stats_cards.html`.

### 4.3 How to Modify Frontend Styles or DaisyUI Themes
1. Source CSS styles are defined in [`theme/static_src/src/styles.css`](../../theme/static_src/src/styles.css).
2. To change the DaisyUI theme from `light` to another theme (e.g. `corporate` or `dark`), update `data-theme="light"` in [`dashboard/templates/base.html:4`](../../dashboard/templates/base.html#L4).
3. Recompile the production stylesheet:
   ```bash
   python manage.py tailwind build
   ```

---

## 5. Critical Pitfalls and Development Traps

1. **Schema Drift on `article_number`**:
   - Do NOT run `python manage.py makemigrations` without first adding `article_number = models.CharField(max_length=50, blank=True, null=True)` back to `Publication` in [`publications/models.py`](../../publications/models.py). Failure to do so will create a migration that drops the column from the database.
2. **Settings Are Not Connected to `.env`**:
   - Modifying `DEBUG=False` or `DJANGO_SECRET_KEY` in `.env` will **not** alter application runtime behavior until `django-environ` is wired into `settings.py`.
3. **Author Deduplication Trap**:
   - If querying authors directly via `Author.objects.all()`, be aware that the table contains duplicate rows for the same individual. Either query through `Publication.authors` with distinct counts or inspect the grouping logic in `dashboard/views.py:358-387`.
4. **Missing `STATIC_ROOT`**:
   - Never run `collectstatic` on production servers without first declaring `STATIC_ROOT = BASE_DIR / "staticfiles"` in `settings.py`.

