# Routes, Views, and API Reference: RRI Publications Dashboard

## 1. Overview and Route Architecture

The **RRI Publications Dashboard** relies on traditional server-rendered Django class-based and function-based views. There are **no REST API frameworks (such as Django REST Framework), GraphQL endpoints, or external webhook receivers** implemented in the project. JSON responses are not generated via API endpoints; instead, datasets intended for Chart.js are serialized server-side into templates using Django's `json_script` template tag.

All application routes are organized under three URL namespaces:
- **`accounts:`**: User authentication, session control, password modification ([`accounts/urls.py`](../../accounts/urls.py))
- **`publications:`**: Publication catalog, individual record views, and Web of Science ingestion flow ([`publications/urls.py`](../../publications/urls.py))
- **`dashboard:`**: Visualizations, metrics, institutional rankings, and drill-down pages ([`dashboard/urls.py`](../../dashboard/urls.py))

---

## 2. Master Route and Endpoint Inventory

### 2.1 Root and Administrative Routes

| Method | URL Pattern | Name & Namespace | View Function / Class | Purpose | Auth Required | CSRF | Accepted Inputs | Response Type |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/` | `root` (global) | [`root_redirect`](../../rri_publications_dashboard/urls.py#L7) | Redirects incoming root traffic to the main dashboard | None | No | None | HTTP 302 Redirect to `/dashboard/` |
| **GET / POST** | `/admin/` | `admin:index` | `admin.site.urls` | Django Administration portal | Staff (`is_staff=True`) | Yes (POST) | Django admin form inputs | `text/html` |
| **GET** | `/__reload__/events/` | `django_browser_reload:events` | `events` (DEBUG only) | Server-Sent Events (SSE) for hot reload | None | No | None | `text/event-stream` |

---

### 2.2 Publications Application Routes (`publications:`)

| Method | URL Pattern | Name | View Function / Class | Purpose | Auth & Permissions | Forms / Models | Accepted Inputs | Response Type |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/publications/` | `publications:list` | [`PublicationsListView`](../../publications/views.py#L48) | Searchable catalog of all publications with KPI stats and trend chart | **Public** (No auth) | `DynamicFilter`<br>`Publication`, `Journal`, `Author` | `search`, `document_type`, `collaboration_type`, `date_published_from`, `date_published_to`, `ordering`, `page` | `text/html` |
| **GET** | `/publications/<int:pk>/` | `publications:publication_detail` | [`PublicationDetailView`](../../publications/views.py#L173) | Full metadata, author list, institutional affiliations, and citation metrics for a single publication | **Public** (No auth) | `Publication`, `Author`, `Affiliation`, `Citation` | `pk` (URL parameter) | `text/html` |
| **GET / POST** | `/publications/wos/upload/` | `publications:wos_upload` | [`wos_upload`](../../publications/views.py#L201) | Upload form for Web of Science `.txt` full-record TSV files | `@login_required`<br>(Any user role) | Custom TSV parser (`wos_parser.py`) | POST: `wos_file` (multipart file upload) | `text/html` (GET) / HTTP 302 to `review` |
| **GET** | `/publications/wos/review/` | `publications:wos_review` | [`wos_review`](../../publications/views.py#L225) | Interactive review screen for staged publication at current session index | `@login_required`<br>(Any user role) | `PublicationForm`, `AuthorFormSet`<br>`Publication`, `Author` | Reads `request.session["wos_records"]` and `["wos_index"]` | `text/html` |
| **POST** | `/publications/wos/save/` | `publications:wos_save` | [`wos_save`](../../publications/views.py#L302) | Atomically commits the reviewed publication and its authors to the database; advances session pointer | `@login_required`<br>(Any user role) | `PublicationForm`, `AuthorFormSet`<br>`Publication`, `Author`, `Affiliation` | POST body: Form fields, management form data, hidden `affiliations_json` | HTTP 302 to `review` or `success` |
| **GET** | `/publications/wos/success/` | `publications:wos_success` | [`wos_success`](../../publications/views.py#L365) | Confirmation screen displayed when all staged WoS records are imported | **Public** (No `@login_required`!) | None | None | `text/html` |

---

### 2.3 Accounts and Authentication Routes (`accounts:`)

| Method | URL Pattern | Name | View Function / Class | Purpose | Auth & Permissions | Forms Involved | Accepted Inputs | Response Type |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET / POST** | `/accounts/login/` | `accounts:login` | [`CustomLoginView`](../../accounts/views.py#L6) | User login form; configures session expiry based on "Remember Me" | Anonymous only (`redirect_authenticated_user=True`) | [`CustomAuthenticationForm`](../../accounts/forms.py#L11) | `username`, `password`, `remember_me` | `text/html` (GET) / HTTP 302 to `dashboard:home` |
| **POST** | `/accounts/logout/` | `accounts:logout` | `auth_views.LogoutView` | Clears user session and logs user out | Authenticated | None | CSRF token | HTTP 302 to `accounts:login` |
| **GET / POST** | `/accounts/password_reset/` | `accounts:password_reset` | `auth_views.PasswordResetView` | Initiates password reset by email | Public | `PasswordResetForm` | `email` | `text/html` (Fails with 500 in practice due to missing SMTP) |
| **GET** | `/accounts/password_reset/done/` | `accounts:password_reset_done` | `auth_views.PasswordResetDoneView` | Password reset email sent confirmation | Public | None | None | `text/html` |
| **GET / POST** | `/accounts/reset/<uidb64>/<token>/` | `accounts:password_reset_confirm` | `auth_views.PasswordResetConfirmView` | Token verification and new password entry | Public | `SetPasswordForm` | `new_password1`, `new_password2` | `text/html` |
| **GET** | `/accounts/reset/done/` | `accounts:password_reset_complete` | `auth_views.PasswordResetCompleteView` | Password successfully reset confirmation | Public | None | None | `text/html` |
| **GET / POST** | `/accounts/password_change/` | `accounts:password_change` | `auth_views.PasswordChangeView` | Password change form for logged-in users | Authenticated | `PasswordChangeForm` | `old_password`, `new_password1`, `new_password2` | `text/html` |
| **GET** | `/accounts/password_change/done/` | `accounts:password_change_done` | `auth_views.PasswordChangeDoneView` | Password successfully changed confirmation | Authenticated | None | None | `text/html` |

---

### 2.4 Dashboard Analytics and Drilldown Routes (`dashboard:`)

*All 21 views below inherit from `TemplateView`. All are completely open to anonymous users (no authentication or role checks).*

| Method | URL Pattern | Name | View Class | Analytical Focus | Accepted Query Parameters | Response |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/dashboard/` | `dashboard:home` | [`DashboardHomeView`](../../dashboard/views.py#L17) | Executive overview: KPI cards, publications by type bar chart, YoY line chart, recent publications | `search`, `document_type`, `collaboration_type`, `date_published_from`, `date_published_to` | `text/html` |
| **GET** | `/dashboard/documents/` | `dashboard:documents` | [`DocumentTypesView`](../../dashboard/views.py#L110) | Catalog split by document type (Articles, Letters, Reviews, Patents, etc.) | `search`, `collaboration_type`, `date_published_from`, `date_published_to`, `ordering`, `page` | `text/html` |
| **GET** | `/dashboard/document/<document_type>/` | `dashboard:document_type_detail` | [`DocumentTypeDetailView`](../../dashboard/views.py#L199) | Deep dive into specific document type output and associated publications | `document_type` (URL path) | `text/html` |
| **GET** | `/dashboard/authors/` | `dashboard:authors` | [`AuthorsView`](../../dashboard/views.py#L272) | Author leaderboard, in-memory deduplication, publication counts, average and total impact factors | `search`, `total_publications_gt`, `total_publications_lt`, `total_impact_factor_gt`, `ordering`, `page` | `text/html` |
| **GET** | `/dashboard/authors/<first_name>/<last_name>/` | `dashboard:author_detail` | [`AuthorDetailView`](../../dashboard/views.py#L560) | Comprehensive author dossier: affiliations, publications, cumulative impact factor | `first_name`, `last_name` (URL path) | `text/html` |
| **GET** | `/dashboard/journals/` | `dashboard:journals` | [`JournalsView`](../../dashboard/views.py#L635) | Journal rankings, publisher distributions, impact factor distribution | `search`, `publisher`, `date_published_from`, `date_published_to`, `ordering`, `page` | `text/html` |
| **GET** | `/dashboard/journal/<journal_id>/` | `dashboard:journal_detail` | [`JournalDetailView`](../../dashboard/views.py#L776) | Specific journal publication history, impact factor, volume/issue records | `journal_id` (URL path) | `text/html` |
| **GET** | `/dashboard/departments/` | `dashboard:departments` | [`DepartmentsView`](../../dashboard/views.py#L844) | RRI departmental productivity rankings and comparative charts | `search`, `date_published_from`, `date_published_to`, `ordering`, `page` | `text/html` |
| **GET** | `/dashboard/departments/<int:pk>/` | `dashboard:department_detail` | [`DepartmentDetailView`](../../dashboard/views.py#L989) | Department profile with member publications and affiliated authors | `pk` (URL parameter) | `text/html` |
| **GET** | `/dashboard/collaboration/` | `dashboard:collaboration` | [`CollaborationView`](../../dashboard/views.py#L1055) | Collaboration distributions (National, International, Departmental) | `search`, `date_published_from`, `date_published_to`, `ordering`, `page` | `text/html` |
| **GET** | `/dashboard/collaboration/<path:collaboration_type>/` | `dashboard:collaboration_detail` | [`CollaborationDetailView`](../../dashboard/views.py#L1158) | Filtered publication list for a specific collaboration mode | `collaboration_type` (URL path; supports slashes) | `text/html` |
| **GET** | `/dashboard/country/collaboration/` | `dashboard:country_collaboration` | [`CountryCollaborationView`](../../dashboard/views.py#L1222) | International co-authorship distributions mapped across partner countries | `search`, `document_type`, `collaboration_type`, `date_published_from`, `date_published_to`, `page` | `text/html` |
| **GET** | `/dashboard/country-collaboration/<path:country>/` | `dashboard:country_collaboration_detail` | [`CountryCollaborationDetailView`](../../dashboard/views.py#L1355) | Deep-dive publication records co-authored with researchers from a specific nation | `country` (URL path; supports whitespace/punctuation) | `text/html` |
| **GET** | `/dashboard/institution/collaboration/` | `dashboard:institution_collaboration` | [`InstitutionCollaborationView`](../../dashboard/views.py#L1417) | Academic co-authorship mapped across partner universities and research centers | `search`, `document_type`, `collaboration_type`, `date_published_from`, `date_published_to`, `page` | `text/html` |
| **GET** | `/dashboard/institution-collaboration/<path:institution>/` | `dashboard:institution_collaboration_detail` | [`InstitutionCollaborationDetailView`](../../dashboard/views.py#L1547) | Specific institution collaboration history and publications | `institution` (URL path; supports complex names) | `text/html` |
| **GET** | `/dashboard/trends/` | `dashboard:trends` | [`TrendsView`](../../dashboard/views.py#L1609) | Multi-year publication trends, growth rates, and annual impact factor metrics | `search`, `document_type`, `collaboration_type`, `date_published_from`, `date_published_to`, `page` | `text/html` |
| **GET** | `/dashboard/trends/<int:year>/` | `dashboard:trend_year_detail` | [`TrendYearDetailView`](../../dashboard/views.py#L1702) | Deep dive into a specific calendar year's publication output | `year` (URL integer parameter) | `text/html` |
| **GET** | `/dashboard/impact/` | `dashboard:impact` | [`ImpactView`](../../dashboard/views.py#L1766) | Journal impact factor tiers, quartile analysis, high-impact publication leaderboard | `search`, `date_published_from`, `date_published_to`, `page` | `text/html` |
| **GET** | `/dashboard/impact/<int:journal_id>/` | `dashboard:impact_detail` | [`ImpactDetailView`](../../dashboard/views.py#L1837) | Detailed impact factor metrics for a specific journal | `journal_id` (URL integer parameter) | `text/html` |
| **GET** | `/dashboard/rri/role/` | `dashboard:rri_role` | [`RRIRoleView`](../../dashboard/views.py#L1906) | Output distribution categorized by institutional role (Faculty, Scholar, Postdoc, etc.) | `search`, `date_published_from`, `date_published_to`, `page` | `text/html` |
| **GET** | `/dashboard/rri-role/<path:role>/` | `dashboard:rri_role_detail` | [`RRIRoleDetailView`](../../dashboard/views.py#L2052) | Publications authored by members holding a specific institutional role | `role` (URL path; supports slashes and parentheses) | `text/html` |

---

## 3. Routing and Architectural Inconsistencies

1. **Inconsistent Path Delimiters Across Master-Detail Pairs**:
   - `dashboard/rri/role/` (slashes) vs `dashboard/rri-role/<path:role>/` (hyphens)
   - `dashboard/country/collaboration/` (slashes) vs `dashboard/country-collaboration/<path:country>/` (hyphens)
   - `dashboard/institution/collaboration/` (slashes) vs `dashboard/institution-collaboration/<path:institution>/` (hyphens)
2. **Plural vs Singular URL Pattern Inconsistencies**:
   - `dashboard/documents/` (plural) vs `dashboard/document/<document_type>/` (singular)
   - `dashboard/journals/` (plural) vs `dashboard/journal/<journal_id>/` (singular)
   - `dashboard/authors/` (plural) vs `dashboard/authors/<first_name>/<last_name>/` (retains plural!)
   - `dashboard/departments/` (plural) vs `dashboard/departments/<int:pk>/` (retains plural!)
3. **Ambiguous String-Based Entity Lookups**:
   - Author detail relies on `authors/<first_name>/<last_name>/`. If two distinct authors share identical first and last names (e.g., common surnames like "Kumar" or "Sharma"), the route maps both authors into a single aggregated view.
   - Journal detail uses untyped string `<journal_id>` in `dashboard/urls.py:27` but converts it in `views.py:782`.
4. **Missing Authentication on Success Page**:
   - While `wos_upload`, `wos_review`, and `wos_save` are protected by `@login_required`, the completion screen `wos_success` ([`publications/urls.py:16`](../../publications/urls.py#L16)) lacks `@login_required`.
5. **No REST / JSON Endpoints**:
   - Any external integration or client-side dynamic fetching must parse full HTML documents because no headless JSON API routes exist.

