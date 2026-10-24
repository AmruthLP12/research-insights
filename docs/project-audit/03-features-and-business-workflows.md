# Features and Business Workflows: RRI Publications Dashboard

## 1. Feature Implementation Status Matrix

| Feature Module | Primary Routes | Implementation Status | Verification Evidence | Key Limitations / Gaps |
| :--- | :--- | :--- | :--- | :--- |
| **Web of Science File Ingestion** | `/publications/wos/upload/`, `review/`, `save/` | **Implemented & Verified** | [`publications/views.py:200-367`](../../publications/views.py#L200-L367), [`wos_parser.py`](../../publications/utils/wos_parser.py) | No file size validation; large payloads staged in session; naive `Author` duplication on save |
| **Publications Catalog & Filtering** | `/publications/` (`publications:list`) | **Implemented & Verified** | [`publications/views.py:48-171`](../../publications/views.py#L48-L171), [`publications_list.html`](../../templates/publications/publications_list.html) | Pagination drops active filters except `search`; public without auth |
| **Publication Detail View** | `/publications/<int:pk>/` | **Implemented & Verified** | [`publications/views.py:173-195`](../../publications/views.py#L173-L195), [`publication_detail.html`](../../templates/publications/publication_detail.html) | Public without auth; displays metadata, affiliations, citations |
| **Executive Analytics Dashboard** | `/dashboard/` (`dashboard:home`) | **Implemented & Verified** | [`dashboard/views.py:17-108`](../../dashboard/views.py#L17-L108), [`dashboard.html`](../../dashboard/templates/dashboard/dashboard.html) | Public without auth; dynamic filters, Chart.js trends, recent pubs |
| **Document Types Analytics** | `/dashboard/documents/`, `document/<type>/` | **Implemented & Verified** | [`dashboard/views.py:110-270`](../../dashboard/views.py#L110-L270), [`document_types.html`](../../dashboard/templates/dashboard/document_types.html) | Filter by Journal Article, Conference Paper, Book Chapter, etc. |
| **Authors Intelligence & Leaderboard**| `/dashboard/authors/`, `authors/<first>/<last>/`| **Implemented & Verified** | [`dashboard/views.py:272-632`](../../dashboard/views.py#L272-L632), [`authors.html`](../../dashboard/templates/dashboard/authors.html) | In-memory author merging; lookup by first/last string instead of ID |
| **Journals & Impact Metrics** | `/dashboard/journals/`, `journal/<id>/` | **Implemented & Verified** | [`dashboard/views.py:635-842`](../../dashboard/views.py#L635-L842), [`journals.html`](../../dashboard/templates/dashboard/journals.html) | Aggregates publisher counts and journal impact factor averages |
| **Departmental Productivity** | `/dashboard/departments/`, `departments/<pk>/` | **Implemented & Verified** | [`dashboard/views.py:844-1053`](../../dashboard/views.py#L844-L1053), [`departments.html`](../../dashboard/templates/dashboard/departments.html) | Tracks departmental output and department-level impact factor |
| **Collaboration Scope Analytics** | `/dashboard/collaboration/`, `collaboration/<type>/`| **Implemented & Verified** | [`dashboard/views.py:1055-1220`](../../dashboard/views.py#L1055-L1220), [`collaboration.html`](../../dashboard/templates/dashboard/collaboration.html) | National, International, Departmental, National/International |
| **Geographic Collaboration** | `/dashboard/country/collaboration/` | **Implemented & Verified** | [`dashboard/views.py:1222-1415`](../../dashboard/views.py#L1222-L1415), [`country_collaboration.html`](../../dashboard/templates/dashboard/country_collaboration.html)| Semicolon sanitization in Python memory; country co-authorship |
| **Institutional Collaboration** | `/dashboard/institution/collaboration/` | **Implemented & Verified** | [`dashboard/views.py:1417-1607`](../../dashboard/views.py#L1417-L1607), [`institution_collaboration.html`](../../dashboard/templates/dashboard/institution_collaboration.html)| Partner university tracking; in-memory deduplication |
| **Historical & Year Trends** | `/dashboard/trends/`, `trends/<year>/` | **Implemented & Verified** | [`dashboard/views.py:1609-1764`](../../dashboard/views.py#L1609-L1764), [`trends.html`](../../dashboard/templates/dashboard/trends.html) | Multi-year publication trajectories and citation growth metrics |
| **Journal Impact Analysis** | `/dashboard/impact/`, `impact/<journal_id>/` | **Implemented & Verified** | [`dashboard/views.py:1766-1904`](../../dashboard/views.py#L1766-L1904), [`impact.html`](../../dashboard/templates/dashboard/impact.html) | High-impact publication tracking and journal impact factor distribution |
| **RRI Institutional Roles** | `/dashboard/rri/role/`, `rri-role/<role>/` | **Implemented & Verified** | [`dashboard/views.py:1906-2112`](../../dashboard/views.py#L1906-L2112), [`rri_role.html`](../../dashboard/templates/dashboard/rri_role.html) | Faculty, Scholar, Postdoc, Staff, External breakdowns |
| **User Authentication & Session** | `/accounts/login/`, `/logout/` | **Implemented & Verified** | [`accounts/views.py:6-18`](../../accounts/views.py#L6-L18), [`login.html`](../../templates/registration/login.html) | Custom login with "Remember Me" session duration logic |
| **Password Reset / Change** | `/accounts/password_reset/*`, `change/*` | **Partially Implemented** | [`accounts/urls.py:14-23`](../../accounts/urls.py#L14-L23), templates present | **Non-Functional in Practice**: Unconfigured SMTP backend raises 500 error |
| **Manual Publication Entry / Edit**| None (orphan templates) | **Present in UI / Not Functional** | [`templates/publications/create_publication.html`](../../templates/publications/create_publication.html) | Templates exist with client JS, but no URL routes or views exist |
| **Legacy Dashboard FBV Prototype** | None (unrouted code) | **Dead Code** | [`publications/views_dashboard.py:1-109`](../../publications/views_dashboard.py#L1-L109) | Superseded by `dashboard` app; renders non-existent template |

---

## 2. Core Business Workflows

### 2.1 Workflow 1: Web of Science (WoS) Batch Ingestion and Review

```mermaid
sequenceDiagram
    autonumber
    actor Officer as Library / Admin Officer
    participant Browser as Client Browser
    participant UploadView as wos_upload View
    participant Parser as wos_parser.py
    participant Session as Django SessionStore
    participant ReviewView as wos_review View
    participant SaveView as wos_save View
    participant DB as SQLite Database

    Officer->>Browser: Selects .txt WoS export file & clicks "Upload & Review"
    Browser->>UploadView: POST /publications/wos/upload/ (multipart/form-data)
    Note over UploadView: Verifies @login_required & request.FILES
    UploadView->>Parser: parse_wos_file(file_obj)
    Note over Parser: Parses TSV rows, resolves page/artn, splits names,<br>extracts C1 address blocks & country
    Parser-->>UploadView: List of publication & author dictionaries
    UploadView->>Session: Store records in request.session["wos_records"], index=0
    UploadView-->>Browser: Redirect to /publications/wos/review/
    
    loop For each publication record (wos_index < total)
        Browser->>ReviewView: GET /publications/wos/review/
        ReviewView->>Session: Fetch record at wos_index
        Note over ReviewView: Run is_rri_affiliation heuristic<br>Construct PublicationForm & AuthorFormSet
        ReviewView-->>Browser: Render review.html (Record i of N)
        Officer->>Browser: Inspects / adjusts metadata, roles, affiliations
        Officer->>Browser: Clicks "Save & Next"
        Browser->>SaveView: POST /publications/wos/save/
        Note over SaveView: Atomic Transaction Started
        SaveView->>DB: Save Publication (created_by=request.user)
        SaveView->>DB: Save Authors (form.save())
        SaveView->>DB: Get or Create Affiliations & AuthorAffiliation rows
        Note over SaveView: Atomic Transaction Committed
        SaveView->>Session: Increment wos_index by 1
        SaveView-->>Browser: Redirect to /publications/wos/review/ (next)
    end
    
    SaveView->>Session: Pop "wos_records" and "wos_index"
    SaveView-->>Browser: Redirect to /publications/wos/success/
    Browser-->>Officer: Displays Success Confirmation Screen
```

#### Detailed Execution Steps and Business Logic:

1. **File Ingestion (`wos_upload`)**:
   - Accepts `.txt` file exported from Clarivate Web of Science (format: *Tab-delimited Win, Full Record*).
   - In [`publications/utils/wos_parser.py:64-110`](../../publications/utils/wos_parser.py#L64-L110), reads and decodes the stream as UTF-8 (ignoring malformed bytes).
   - Maps standard Web of Science field tags:
     - `TI`: Title
     - `SO`: Journal Name (Source Publication)
     - `DT`: Document Type
     - `PY`: Publication Year (converted to `YYYY-01-01`)
     - `VL`: Volume, `IS`: Issue
     - `BP` / `EP` / `AR` / `ARTN`: Page range or article number
     - `DI`: Digital Object Identifier (DOI)
     - `AF`: Author Full Names (semicolon-separated)
     - `C1`: Author Affiliations and institutional address blocks
2. **Affiliation and Author Parsing**:
   - `parse_affiliation_blocks()` parses bracketed syntax: `[Author A; Author B] Raman Res Inst, Bangalore, India`.
   - `split_name()` splits `Last, First` into `first_name` and `last_name`.
   - `extract_country()` extracts the final comma-delimited segment of an address string.
3. **Institutional Heuristic Detection**:
   - In [`publications/views.py:32-42`](../../publications/views.py#L32-L42), `is_rri_affiliation(name)` checks for substrings: `["raman", "raman res inst", "raman research institute", "rri"]`.
   - If detected, `rri_role` in `review.html` is left blank for manual assignment; if not detected, `rri_role` defaults to `"External"`.
4. **Interactive Staging & Review (`wos_review`)**:
   - Pre-populates a `PublicationForm` and an `AuthorFormSet` with extra forms equal to author count.
   - Form fields include hidden `affiliations_json` containing serialized affiliation dictionaries.
5. **Persistence & Side Effects (`wos_save`)**:
   - Executed under `transaction.atomic`.
   - Creates a `Publication` record linked to `request.user`.
   - Iterates through the `AuthorFormSet`: creates `Author` instances, resolves or creates `Affiliation` records with `Affiliation.objects.get_or_create()`, and creates linking `AuthorAffiliation` records.
   - Updates session pointer. When all records are processed, cleans up session keys and redirects to `wos_success`.

---

### 2.2 Workflow 2: Catalog Browsing, Search, and Faceted Filtering

```mermaid
sequenceDiagram
    autonumber
    actor User as Researcher / Visitor
    participant Browser as Browser Client
    participant View as PublicationsListView
    participant Filter as DynamicFilter
    participant DB as Database
    participant Tpl as publications_list.html

    User->>Browser: Enters search keyword or selects document type
    Browser->>View: GET /publications/?search=Optics&document_type=Journal+Article
    Note over View: Constructs base queryset:<br>select_related('journal'), prefetch_related('authors', 'departments')
    View->>Filter: DynamicFilter(request.GET, queryset)
    Filter->>DB: Generates OR-chained icontains query on title, journal, doi, authors
    DB-->>Filter: Filtered queryset
    View->>DB: publications.aggregate(Count, Sum(IF), Avg(IF), Max(IF))
    View->>DB: publications.values('date_published__year').annotate(total=Count)
    View->>View: Paginator(publications, 10).get_page(page)
    View->>Tpl: Render publications_list.html
    Tpl-->>Browser: Return HTML with KPI stats, trend chart JSON, table
```

#### Business Rules and Computations:
- **Search Scope**: Evaluates matches across `title`, `journal__name`, `doi`, `authors__first_name`, `authors__last_name`, and `departments__name`.
- **KPI Aggregations**:
  - `publication_count`: Total publication records matching current filters.
  - `publication_total_impact`: Sum of all associated `journal__impact_factor` values.
  - `publication_average_impact`: Mean impact factor per publication.
  - `publication_highest_impact`: Maximum recorded journal impact factor in the filtered set.
- **Trend Data Generation**: Grouped by `date_published__year`, computing total count, total impact factor, and average impact factor for client-side Chart.js rendering.

---

### 2.3 Workflow 3: Author Analytics, Leaderboard, and Profile Drilldown

```mermaid
sequenceDiagram
    autonumber
    actor User as Academic Dean / Evaluator
    participant Browser as Browser Client
    participant View as AuthorsView
    participant DB as Database
    participant Detail as AuthorDetailView

    User->>Browser: Navigates to /dashboard/authors/
    Browser->>View: GET /dashboard/authors/?total_publications_gt=5
    View->>DB: Query Author.objects.annotate(Count, Sum, Avg).prefetch_related(...)
    DB-->>View: Raw author rows (contains duplicates from multiple imports)
    Note over View: In-Memory Deduplication Pipeline:<br>Keys by (first_name.strip().lower(), last_name.strip().lower())<br>Sums merged_publications & merged_impact<br>Accumulates merged_affiliations set
    Note over View: Post-Merge Filtering & Sorting:<br>Applies total_publications_gt / ordering in Python<br>Paginates resulting list (10 per page)
    View-->>Browser: Render authors.html (Leaderboard + Filter Bar)
    
    User->>Browser: Clicks specific author name link
    Browser->>Detail: GET /dashboard/authors/John/Doe/
    Detail->>DB: Author.objects.filter(first_name__iexact='John', last_name__iexact='Doe')
    Detail->>DB: Publication.objects.filter(authors__in=authors).distinct()
    Detail->>DB: AuthorAffiliation.objects.filter(author__in=authors)
    Detail-->>Browser: Render author_detail.html (Publication list, affiliations, total IF)
```

#### Business Rules and Computations:
- **In-Memory Merging Algorithm**:
  - Because `wos_save` creates distinct `Author` rows on each paper, `AuthorsView` merges authors by lowercase tuple `(first_name, last_name)`.
  - Recomputes `average_impact_factor = merged_impact / merged_publications`.
- **Author Detail URL Scheme**:
  - Uses `dashboard/authors/<first_name>/<last_name>/` rather than integer primary keys (`/authors/<pk>/`).
  - Queries all matching duplicate rows via `Author.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name)` to aggregate publications across all duplicate author entries.

---

### 2.4 Workflow 4: User Authentication and Session Management

```mermaid
sequenceDiagram
    autonumber
    actor User as Institutional User
    participant Browser as Browser Client
    participant LoginView as CustomLoginView
    participant Form as CustomAuthenticationForm
    participant Session as Django Session

    User->>Browser: Enters credentials & checks "Remember me"
    Browser->>LoginView: POST /accounts/login/
    LoginView->>Form: is_valid() authentication check
    alt Valid Credentials
        Note over LoginView: form_valid() executed
        alt remember_me is False
            LoginView->>Session: request.session.set_expiry(0) (Browser Close Expiry)
        else remember_me is True
            Note over LoginView: Retains default SESSION_COOKIE_AGE (2 weeks)
        end
        LoginView-->>Browser: Redirect to dashboard:home (/dashboard/)
    else Invalid Credentials
        LoginView-->>Browser: Render login.html with non_field_errors
    end
```

---

## 3. Unimplemented and Orphaned Business Logic

1. **Manual Publication Creation & Editing**:
   - `templates/publications/create_publication.html` and `edit_publication.html` implement a dynamic vanilla JavaScript author/affiliation block cloner.
   - However, no matching URLs exist in `publications/urls.py` and no view classes exist in `publications/views.py`. Publications cannot be manually authored through the frontend; they must be ingested via WoS files or Django Admin.
2. **Password Reset Workflow**:
   - While `accounts/urls.py` declares the full suite of Django auth password reset views (`password_reset`, `password_reset_done`, `password_reset_confirm`, `password_reset_complete`), the project lacks any configured SMTP backend in `settings.py`. Attempting to reset a password results in a 500 error (`ConnectionRefusedError: [Errno 111] Connection refused`).
3. **Legacy Dashboard Module**:
   - [`publications/views_dashboard.py`](../../publications/views_dashboard.py) contains an early prototype of the dashboard logic. It queries RRI publications and renders `"publications/dashboard/dashboard.html"`, but is unreferenced in any URLconf and the referenced template does not exist.

