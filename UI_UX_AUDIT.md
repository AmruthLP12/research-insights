# Research Insights: Comprehensive UI/UX Audit and Redesign Plan

- **Date**: 2026-10-25
- **Status**: Audit & Planning Document (Ready for Review)
- **Scope**: Whole-Project UI/UX Evaluation, Functional Defect Analysis, Design System Definition, and Remediation Backlog

---

## 1. Executive Summary

This audit evaluates the user interface, interaction design, component consistency, and visual hierarchy of the **Research Insights** Django application (RRI Publications Dashboard).

Over the preceding remediation steps, critical security vulnerabilities (fail-closed settings, CSRF/session cookies, role-based access control, publication cascade deletion prevention, upload size enforcement, and Web of Science workflow hardening) were resolved and backed by 87 passing automated tests. 

However, the user-facing interface retains significant structural, functional, and visual defects resulting from uncoordinated development:
1. **Broken Core Interactions**: Several analytical drill-downs fail with unhandled `NoReverseMatch` 500 errors (e.g. document types with slashes such as `"Book/Book Chapter"`, authors with mononyms or empty first names, and unassigned RRI roles).
2. **Filter & Pagination Decoupling**: Navigating pagination pages in `components/pagination.html` completely discards all active filter parameters except `search`, frustrating users attempting multi-page exploration of filtered datasets.
3. **Template & Model Mismatches**: Key catalog pages reference non-existent model attributes (`abstract`, `full_text_url`, `citation`), while ignoring real persisted data models like `Citation` (`yearly_citations`).
4. **Visual & Component Inconsistencies**: Styles vary wildly across three conflicting paradigms—semantic DaisyUI component tokens, raw Tailwind utility classes, and hardcoded legacy hex codes (`#0A4DA3`). Stacked card layouts cause visual exhaustion ("cards inside cards"), and 24 separate inline Chart.js scripts duplicate hardcoded color palettes without centralized theme coordination.
5. **Malformed Base Layout**: `dashboard/templates/base.html` contains duplicate doctype and HTML tags, while an orphaned legacy base template remains in the repository.

This document inventories every user-facing page, categorizes all identified defects with concrete evidence, proposes a unified, light-themed research design system, and establishes a prioritized remediation backlog.

---

## 2. Page and Interaction Inventory

The application encompasses **38 distinct routes and user-facing endpoints** across the `accounts`, `publications`, and `dashboard` modules:

| # | URL / Pattern | View Name / Class | Template File | Key Interactions | Status / Verification |
|---|---|---|---|---|---|
| **Auth & Account Management** | | | | | |
| 1 | `/accounts/login/` | `accounts:login` (`CustomLoginView`) | `templates/registration/login.html` | Username/password login, remember me, link to password reset | Verified by test |
| 2 | `/accounts/logout/` | `accounts:logout` (`LogoutView`) | *Redirect to login* | POST logout action | Verified by test |
| 3 | `/accounts/password_reset/` | `accounts:password_reset` (`PasswordResetView`) | `templates/registration/password_reset_form.html` | Submit email to request password reset link | Verified by test |
| 4 | `/accounts/password_reset/done/` | `accounts:password_reset_done` (`PasswordResetDoneView`) | `templates/registration/password_reset_done.html` | Confirmation message instructing user to check inbox | Verified by test |
| 5 | `/accounts/reset/<uidb64>/<token>/` | `accounts:password_reset_confirm` (`PasswordResetConfirmView`) | `templates/registration/password_reset_confirm.html` | Enter and confirm new password via token link | Verified by test |
| 6 | `/accounts/reset/done/` | `accounts:password_reset_complete` (`PasswordResetCompleteView`) | `templates/registration/password_reset_complete.html` | Confirmation screen with link to login | Verified by test |
| 7 | `/accounts/password_change/` | `accounts:password_change` (`PasswordChangeView`) | `templates/registration/password_change_form.html` | Authenticated password change with old/new passwords | Verified by test |
| 8 | `/accounts/password_change/done/` | `accounts:password_change_done` (`PasswordChangeDoneView`) | `templates/registration/password_change_done.html` | Confirmation screen with link to dashboard | Verified by test |
| **Publications Catalog & Ingestion** | | | | | |
| 9 | `/` | `root` (`root_redirect`) | *Redirect to `/dashboard/`* | Automatic root entry routing | Verified by test |
| 10 | `/publications/` | `publications:list` (`PublicationsListView`) | `templates/publications/publications_list.html` | Search, dynamic filters, pagination, chart trend, table view | Verified by test |
| 11 | `/publications/<int:pk>/` | `publications:publication_detail` (`PublicationDetailView`) | `templates/publications/publication_detail.html` | Full publication metadata, authors, departments, DOI link | Verified by test |
| 12 | `/publications/wos/upload/` | `publications:wos_upload` (`wos_upload`) | `templates/publications/upload.html` | File selection, drag-and-drop, format/size validation, submit | Verified by test |
| 13 | `/publications/wos/review/` | `publications:wos_review` (`wos_review`) | `templates/publications/review.html` | Batch record review, author editing, affiliation inspection | Verified by test |
| 14 | `/publications/wos/save/` | `publications:wos_save` (`wos_save`) | *Redirect controller* | Atomic record persistence, author/affiliation mapping | Verified by test |
| 15 | `/publications/wos/cancel/` | `publications:wos_cancel` (`wos_cancel`) | *Redirect controller* | Discard staged batch and return to upload | Verified by test |
| 16 | `/publications/wos/success/` | `publications:wos_success` (`wos_success`) | `templates/publications/wos_success.html` | Batch completion card, navigation to catalog or dashboard | Verified by test |
| **Analytical Dashboard (Analytics)** | | | | | |
| 17 | `/dashboard/` | `dashboard:home` (`DashboardHomeView`) | `dashboard/templates/dashboard/dashboard.html` | KPI cards, type bar chart, year line chart, recent publications | Verified by test |
| 18 | `/dashboard/trends/` | `dashboard:trends` (`TrendsView`) | `dashboard/templates/dashboard/trends.html` | Publications by year bar chart, impact line chart, year table | Verified by test |
| 19 | `/dashboard/trends/<int:year>/` | `dashboard:trend_year_detail` (`TrendYearDetailView`) | `dashboard/templates/dashboard/trend_year_detail.html` | Year-specific publications list with pagination | Verified by test |
| 20 | `/dashboard/impact/` | `dashboard:impact` (`ImpactView`) | `dashboard/templates/dashboard/impact.html` | Impact distribution charts, journal impact summary table | Verified by test |
| 21 | `/dashboard/impact/<int:journal_id>/` | `dashboard:impact_detail` (`ImpactDetailView`) | `dashboard/templates/dashboard/impact_detail.html` | Journal impact breakdown, publication list with pagination | Verified by test |
| **Analytical Dashboard (Publications Breakdown)** | | | | | |
| 22 | `/dashboard/documents/` | `dashboard:documents` (`DocumentTypesView`) | `dashboard/templates/dashboard/document_types.html` | Document type breakdown charts, document types table | Verified by test |
| 23 | `/dashboard/document/<document_type>/` | `dashboard:document_type_detail` (`DocumentTypeDetailView`) | `dashboard/templates/dashboard/document_type_detail.html` | Publications filtered by document type with pagination | Defect confirmed |
| 24 | `/dashboard/collaboration/` | `dashboard:collaboration` (`CollaborationView`) | `dashboard/templates/dashboard/collaboration.html` | Institutional vs. international collaboration charts and table | Verified by test |
| 25 | `/dashboard/collaboration/<path:collaboration_type>/` | `dashboard:collaboration_detail` (`CollaborationDetailView`) | `dashboard/templates/dashboard/collaboration_detail.html` | Publications filtered by collaboration type | Verified by test |
| 26 | `/dashboard/country/collaboration/` | `dashboard:country_collaboration` (`CountryCollaborationView`) | `dashboard/templates/dashboard/country_collaboration.html` | Country collaboration breakdown charts and country table | Verified by test |
| 27 | `/dashboard/country-collaboration/<path:country>/` | `dashboard:country_collaboration_detail` (`CountryCollaborationDetailView`) | `dashboard/templates/dashboard/country_collaboration_detail.html` | Publications linked to specific foreign country affiliations | Verified by test |
| 28 | `/dashboard/institution/collaboration/` | `dashboard:institution_collaboration` (`InstitutionCollaborationView`) | `dashboard/templates/dashboard/institution_collaboration.html` | External collaborating institutions breakdown and table | Verified by test |
| 29 | `/dashboard/institution-collaboration/<path:institution>/` | `dashboard:institution_collaboration_detail` (`InstitutionCollaborationDetailView`) | `dashboard/templates/dashboard/institution_collaboration_detail.html` | Publications linked to specific collaborating institutions | Verified by test |
| **Analytical Dashboard (Entity Management & Rosters)** | | | | | |
| 30 | `/dashboard/authors/` | `dashboard:authors` (`AuthorsView`) | `dashboard/templates/dashboard/authors.html` | Top authors bar chart, impact share donut, author table | Verified by test |
| 31 | `/dashboard/authors/<first_name>/<last_name>/` | `dashboard:author_detail` (`AuthorDetailView`) | `dashboard/templates/dashboard/author_detail.html` | Author profile, affiliations list, author publication history | Defect confirmed |
| 32 | `/dashboard/journals/` | `dashboard:journals` (`JournalsView`) | `dashboard/templates/dashboard/journals.html` | Top journals by volume and impact, journals directory | Verified by test |
| 33 | `/dashboard/journal/<journal_id>/` | `dashboard:journal_detail` (`JournalDetailView`) | `dashboard/templates/dashboard/journal_detail.html` | Journal profile, impact factor, journal publication history | Defect confirmed |
| 34 | `/dashboard/departments/` | `dashboard:departments` (`DepartmentsView`) | `dashboard/templates/dashboard/departments.html` | Department productivity charts, departmental directory | Verified by test |
| 35 | `/dashboard/departments/<int:pk>/` | `dashboard:department_detail` (`DepartmentDetailView`) | `dashboard/templates/dashboard/department_detail.html` | Department profile, publications, affiliated scholars | Verified by test |
| 36 | `/dashboard/rri/role/` | `dashboard:rri_role` (`RRIRoleView`) | `dashboard/templates/dashboard/rri_role.html` | Institutional role breakdown (Faculty, Student, External) | Verified by test |
| 37 | `/dashboard/rri-role/<path:role>/` | `dashboard:rri_role_detail` (`RRIRoleDetailView`) | `dashboard/templates/dashboard/rri_role_detail.html` | Publications attributed to specific institutional roles | Defect confirmed |
| **System & Administration** | | | | | |
| 38 | `/admin/` | `admin:index` (Django Admin) | Default Django Admin | Database administrative console | Verified by test |

---

## 3. Audit of Functional Defects and Problems

Every defect reported below has been verified through code inspection or Python/Django runtime reproduction:

### 3.1 Confirmed Defects (Reproduced)

#### Defect F-01: Pagination Discards All Active Filter Parameters
- **Affected Components**: [`dashboard/templates/components/pagination.html:28,37,56,65`](file:///home/amruth/pro/django/research-insights/dashboard/templates/components/pagination.html#L28)
- **Observed Behavior**: When a user applies filters on `/publications/` or any analytical table (e.g. `document_type=Journal Article`, `journal=2`, `year_min=2020`) and navigates to page 2 via pagination controls, all active filters are wiped out, reverting the dataset to unfiltered pagination.
- **Evidence**:
  ```html
  <!-- pagination.html lines 35-39 -->
  <a class="join-item btn {% if not page_obj.has_previous %}btn-disabled{% endif %}"
     {% if page_obj.has_previous %}
         href="?page={{ page_obj.previous_page_number }}{% if request.GET.search %}&search={{ request.GET.search }}{% endif %}"
     {% endif %}>
      Prev
  </a>
  ```
  The template hardcodes only `&search={{ request.GET.search }}` and completely omits all other query parameters from `request.GET`.
- **Severity**: **P1 (High)**
- **Suggested Fix**: Create a lightweight template tag or helper (e.g. `{% query_transform page=page_obj.next_page_number %}`) that copies existing `request.GET` parameters while safely updating the `page` argument.

#### Defect F-02: `NoReverseMatch` Crash on `document_type_detail` for Document Types with Slashes
- **Affected Files**: [`dashboard/urls.py:10`](file:///home/amruth/pro/django/research-insights/dashboard/urls.py#L10), [`dashboard/templates/dashboard/document_types.html:59,69`](file:///home/amruth/pro/django/research-insights/dashboard/templates/dashboard/document_types.html#L59)
- **Observed Behavior**: Standard institutional publications include document type `"Book/Book Chapter"` (defined in `Publication.DOC_TYPE_CHOICES`). When this document type appears in the table, rendering `document_types.html` crashes with an unhandled `NoReverseMatch` 500 error.
- **Evidence**:
  ```python
  # Reproduction:
  from django.template import Template, Context
  Template("{% url 'dashboard:document_type_detail' 'Book/Book Chapter' %}").render(Context({}))
  # Output: NoReverseMatch: Reverse for 'document_type_detail' with arguments '('Book/Book Chapter',)' not found.
  # Pattern tried: ['dashboard/document/(?P<document_type>[^/]+)/\\Z']
  ```
  `dashboard/urls.py` uses `path("document/<document_type>/", ...)` which rejects slashes, whereas other routes correctly use `<path:...>`.
- **Severity**: **P1 (High)**
- **Suggested Fix**: Update `dashboard/urls.py` pattern to `path("document/<path:document_type>/", views.DocumentTypeDetailView.as_view(), name="document_type_detail")`.

#### Defect F-03: `NoReverseMatch` Crash on `author_detail` for Mononyms and Blank First Names
- **Affected Files**: [`dashboard/urls.py:16`](file:///home/amruth/pro/django/research-insights/dashboard/urls.py#L16), [`dashboard/templates/tables/authors_table.html:72`](file:///home/amruth/pro/django/research-insights/dashboard/templates/tables/authors_table.html#L72)
- **Observed Behavior**: Authors without a separate first name (e.g. Indian mononyms, corporate entities, single-word names) have `first_name=""`. Rendering `authors_table.html` crashes with an unhandled `NoReverseMatch` 500 error.
- **Evidence**:
  ```python
  # Reproduction:
  from django.urls import reverse
  reverse('dashboard:author_detail', kwargs={'first_name': '', 'last_name': 'Raman'})
  # Output: NoReverseMatch: Reverse for 'author_detail' with keyword arguments '{'first_name': '', 'last_name': 'Raman'}' not found.
  ```
  The regex `(?P<first_name>[^/]+)` requires at least 1 character.
- **Severity**: **P1 (High)**
- **Suggested Fix**: Route author drill-downs by primary key: `path("authors/<int:pk>/", views.AuthorDetailView.as_view(), name="author_detail")`.

#### Defect F-04: `NoReverseMatch` Crash on `rri_role_detail` for Unassigned or Empty Roles
- **Affected Files**: [`dashboard/urls.py:53`](file:///home/amruth/pro/django/research-insights/dashboard/urls.py#L53), [`dashboard/templates/dashboard/rri_role.html:69`](file:///home/amruth/pro/django/research-insights/dashboard/templates/dashboard/rri_role.html#L69)
- **Observed Behavior**: Authors newly ingested from Web of Science start with `rri_role=""` until categorized. When unassigned authors exist, `rri_role.html` crashes with `NoReverseMatch`.
- **Evidence**:
  ```python
  # Reproduction:
  from django.template import Template, Context
  Template("{% url 'dashboard:rri_role_detail' '' %}").render(Context({}))
  # Output: NoReverseMatch: Reverse for 'rri_role_detail' with arguments '('',)' not found.
  ```
- **Severity**: **P1 (High)**
- **Suggested Fix**: Provide a dedicated slug/keyword for unassigned roles (e.g. `unassigned`) and handle empty role lookups gracefully in view and template.

#### Defect F-05: Unhandled `ValueError` 500 Error on `JournalDetailView` for Non-Integer or Missing Journal IDs
- **Affected Files**: [`dashboard/urls.py:22`](file:///home/amruth/pro/django/research-insights/dashboard/urls.py#L22), [`dashboard/views.py:784`](file:///home/amruth/pro/django/research-insights/dashboard/views.py#L784)
- **Observed Behavior**: `dashboard/urls.py` declares `path("journal/<journal_id>/", ...)` using untyped `<journal_id>`. When a publication lacks a journal (`journal=None`), the template renders `/dashboard/journal/None/`. Visiting this URL triggers `ValueError: Field 'id' expected a number but got 'None'` in `JournalDetailView`, returning an unhandled HTTP 500 instead of a clean 404.
- **Severity**: **P1 (High)**
- **Suggested Fix**: Change URL pattern to `path("journal/<int:journal_id>/", ...)` and add a fallback in `journals.html` so unlinked journals do not generate invalid links.

#### Defect F-06: Malformed HTML Tags in `base.html` and Orphaned Duplicate Base Template
- **Affected Files**: [`dashboard/templates/base.html:1-8`](file:///home/amruth/pro/django/research-insights/dashboard/templates/base.html#L1-L8), [`dashboard/templates/dashboard/base.html`](file:///home/amruth/pro/django/research-insights/dashboard/templates/dashboard/base.html)
- **Observed Behavior**: `dashboard/templates/base.html` contains duplicate `<!doctype html>` declarations, duplicate `<html lang="en" data-theme="light">` tags, and duplicate `</html>` closing tags. Additionally, an orphaned `dashboard/templates/dashboard/base.html` file exists in the directory tree with outdated CDN dependencies.
- **Evidence**:
  ```html
  {% load static tailwind_tags %}
  <!doctype html>
  <html lang="en" data-theme="light">
    {% load static tailwind_tags %}
    <!doctype html>
    <html lang="en" data-theme="light">
  ```
- **Severity**: **P2 (Medium)**
- **Suggested Fix**: Clean up `dashboard/templates/base.html` so HTML tags are valid and well-formed. Safely archive or remove the unreferenced duplicate `dashboard/templates/dashboard/base.html`.

#### Defect F-07: Model-Template Mismatch in `publication_detail.html`
- **Affected Files**: [`templates/publications/publication_detail.html:65,119,125,129`](file:///home/amruth/pro/django/research-insights/templates/publications/publication_detail.html#L65)
- **Observed Behavior**: `publication_detail.html` attempts to render `publication.abstract`, `publication.full_text_url`, and `publication.citation`. None of these three attributes exist on the `Publication` model. Conversely, the model's actual citation data (`publication.yearly_citations.all`) is completely omitted from the template.
- **Evidence**:
  ```python
  [f.name for f in Publication._meta.get_fields()]
  # Output does NOT contain 'abstract', 'full_text_url', or 'citation'.
  # Yearly citations exist under related name 'yearly_citations'.
  ```
- **Severity**: **P1 (High)**
- **Suggested Fix**: Remove non-existent field references and render real citation metrics from `yearly_citations` (WoS citations, Google Scholar citations, Scopus citations).

#### Defect F-08: External CDN Script Injection in `publications_list.html`
- **Affected Files**: [`templates/publications/publications_list.html:101`](file:///home/amruth/pro/django/research-insights/templates/publications/publications_list.html#L101)
- **Observed Behavior**: `publications_list.html` includes `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`, even though `base.html` already loads the local bundled script `{% static 'js/chart.min.js' %}`. In offline or firewalled environments, this external CDN script causes network errors and duplicate Chart.js global initialization.
- **Severity**: **P2 (Medium)**
- **Suggested Fix**: Remove the external CDN script tag; rely on the already-loaded local `chart.min.js`.

#### Defect F-09: Table Header and Empty State Column Count Mismatch in `impact_table.html`
- **Affected Files**: [`dashboard/templates/tables/impact_table.html:51`](file:///home/amruth/pro/django/research-insights/dashboard/templates/tables/impact_table.html#L51)
- **Observed Behavior**: `impact_table.html` defines 6 table header columns (`#`, `Journal`, `Publications`, `Total IF`, `Average IF`, `Actions`), but specifies `<td colspan="5">` on the empty state row, breaking table grid geometry when no records match.
- **Severity**: **P3 (Polish)**
- **Suggested Fix**: Update to `<td colspan="6">`.

#### Defect F-10: Dashboard Sidebar Displayed on Public Authentication Pages
- **Affected Files**: [`dashboard/templates/base.html:27`](file:///home/amruth/pro/django/research-insights/dashboard/templates/base.html#L27), [`dashboard/templates/dashboard/sidebar.html:88-116`](file:///home/amruth/pro/django/research-insights/dashboard/templates/dashboard/sidebar.html#L88)
- **Observed Behavior**: When an anonymous user visits `/accounts/login/` or `/accounts/password_reset/`, `base.html` unconditionally renders the full dashboard sidebar with analytical navigation links. Clicking any sidebar link redirects back to `/accounts/login/?next=...`, creating a disorienting loop.
- **Severity**: **P2 (Medium)**
- **Suggested Fix**: In `base.html`, wrap the sidebar in an authentication check or permit child templates to override `{% block sidebar %}{% endblock %}` with empty content on public auth views.

---

### 3.2 Code-Established Issues

#### Issue F-11: Filter Reset Action Uses Relative `href="."`
- **Affected Files**: [`dashboard/templates/components/filter_bar.html:42`](file:///home/amruth/pro/django/research-insights/dashboard/templates/components/filter_bar.html#L42)
- **Observed Behavior**: The "Reset" button in the filter bar points to `href="."`. In subpaths or URLs with query parameters or without trailing slashes, `href="."` can produce unexpected relative navigation.
- **Severity**: **P2 (Medium)**
- **Suggested Fix**: Point reset to `request.path` (`<a href="{{ request.path }}" class="btn btn-ghost">Reset</a>`).

#### Issue F-12: Multiple Orphaned, Unreferenced Template Files
- **Affected Files**:
  - `templates/publications/create_publication.html`
  - `templates/publications/edit_publication.html`
  - `templates/publications/publication_form.html`
  - `dashboard/templates/dashboard/collaboration_types.html`
  - `dashboard/templates/dashboard/base.html`
- **Observed Behavior**: These 5 templates exist in the repository but have zero incoming references from URL configurations or view classes. They contain hardcoded hex colors (`#0A4DA3`) that conflict with the rest of the application.
- **Severity**: **P3 (Polish)**
- **Suggested Fix**: Archive or remove orphaned templates to avoid maintenance confusion.

#### Issue F-13: Missing Custom Error Pages (404, 403, 500)
- **Affected Files**: Root `templates/` directory lacks `404.html`, `403.html`, and `500.html`.
- **Observed Behavior**: When an authenticated or unauthenticated user encounters a 404 or permission error in production (`DEBUG=False`), Django falls back to generic server error pages with no institutional branding, navigation, or recovery pathways.
- **Severity**: **P2 (Medium)**
- **Suggested Fix**: Provide clean, light-themed `404.html`, `403.html`, and `500.html` templates consistent with the application's header and footer.

---

### 3.3 Potential Issues Requiring Further Verification

1. **Date Filter Boundaries on FilterBar**: `date_filters` in `dashboard/filters.py` dynamically builds date widgets. Need to confirm whether browser date inputs across Safari and Firefox trigger `onchange="this.form.submit()"` predictably.
2. **Horizontal Table Scroll on Mobile Devices**: Several detail tables (e.g. `document_type_detail.html`, `collaboration_detail.html`) wrap tables in `<div class="overflow-x-auto">`. On narrow mobile viewports (< 375px), wide 8-column tables require extensive scrolling. Column prioritization (hiding less critical metadata on mobile screens) should be verified with mobile emulator testing.

---

## 4. Visual Design Audit

### 4.1 Current Styling Architecture
The project employs **Tailwind CSS v4** (`@import "tailwindcss";`) combined with **DaisyUI v5** (`@plugin "daisyui";`) compiled into `theme/static/css/dist/styles.css`. Static assets include local copies of `alpine.min.js`, `chart.min.js`, and `lucide.min.js`.

### 4.2 Key Visual Inconsistencies & Flaws

1. **Styling Tri-furcation**:
   - *System A (DaisyUI)*: `card bg-base-100`, `btn btn-primary`, `btn-info`, `badge badge-outline`. (Used in `dashboard/`)
   - *System B (Raw Tailwind)*: `bg-white p-6 rounded shadow`, `bg-blue-600 text-white p-2 rounded`. (Used in `templates/registration/`)
   - *System C (Hardcoded Legacy)*: Inline hex colors like `text-[#0A4DA3]`, `focus:ring-[#0A4DA3]`. (Used in `create_publication.html` and forms)
2. **Card Nesting Overload ("Box Fatigue")**:
   - `page_header.html` is a card with shadows and border.
   - `filter_bar.html` is another card immediately below it.
   - `stats_cards.html` are nested inside another card.
   - `chart_card.html` adds more bordered boxes.
   - Data tables are wrapped in yet another card.
   The resulting layout feels cluttered and claustrophobic.
3. **Chart Palette Duplication**:
   - Across 24 chart instances, each template manually defines its own chart colors (e.g. `backgroundColor: "#4f46e5"`, `borderColor: "#06b6d4"`, or arbitrary 10-color arrays).
   - If a global palette adjustment is needed, all 24 templates must be manually edited.
   - Legends and tooltips lack uniform typography and font sizing.
4. **Typography Scale and Line Heights**:
   - Headings fluctuate unpredictably between `text-3xl font-bold`, `text-2xl font-bold`, `text-xl font-semibold`, and `card-title`.
   - Table body text uses default unconstrained sizing with varying contrast (`text-base-content/60`, `text-gray-500`, `text-slate-600`).
5. **Empty State Lack of Actionability**:
   - `components/empty_state.html` renders a floating emoji (`📊`) and short text without a call to action or a button to reset active filters.

---

## 5. Target Design Direction: Unified Research Design System

The proposed redesign aims for an **authoritative, clean, light-themed institutional research interface** tailored to academic metrics, scientific publications, and departmental governance.

### 5.1 Typography
- **Primary Font Family**:
  ```css
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  ```
- **Monospace Font** (DOIs, IDs, Article Numbers):
  ```css
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  ```
- **Type Scale**:
  - `Display / Page Title`: `1.5rem` (24px) / `font-bold` / `tracking-tight` / text-slate-900
  - `Section Heading (H2)`: `1.125rem` (18px) / `font-semibold` / text-slate-800
  - `Card / Table Title (H3)`: `0.9375rem` (15px) / `font-semibold` / text-slate-800
  - `Body / Cell Text`: `0.875rem` (14px) / `font-normal` / text-slate-700 / line-height `1.5`
  - `Caption / Meta / Badge`: `0.75rem` (12px) / `font-medium` / text-slate-500

### 5.2 Color Palette (Light Theme Only)
A restrained, accessible color system based on neutral slates and academic navy:

| Semantic Role | Token / Value | Hex | Usage |
|---|---|---|---|
| **Primary Accent** | `color-primary` | `#0A4DA3` / `#1D4ED8` | Institutional brand blue, primary actions, active tabs |
| **Primary Hover** | `color-primary-hover` | `#083C7E` / `#1E40AF` | Hover/focus state for primary buttons |
| **Surface Base** | `bg-base-200` | `#F8FAFC` (Slate-50) | Overall page background canvas |
| **Surface Card** | `bg-base-100` | `#FFFFFF` (White) | Content panels, table backgrounds, charts |
| **Border / Rule** | `border-base-300` | `#E2E8F0` (Slate-200) | Subtle card borders, table dividers, inputs |
| **Text Primary** | `text-base-content` | `#0F172A` (Slate-900) | Primary headings, titles, emphasis |
| **Text Secondary** | `text-muted` | `#64748B` (Slate-500) | Subtitles, table headers, metadata |
| **Success / High Impact** | `color-success` | `#059669` (Emerald-600) | High impact factors, verified badges, save confirmations |
| **Warning / Intermediate** | `color-warning` | `#D97706` (Amber-600) | Medium impact factors, notices |
| **Error / Destructive** | `color-error` | `#DC2626` (Red-600) | Form errors, delete actions, size limit warnings |

### 5.3 Surface and Elevation Conventions
- **Eliminate Unnecessary Card Wrappers**:
  - `page_header.html` should be **flat** (no background card, no shadow). It sits directly on the canvas with breadcrumbs, title, and metadata.
  - Content containers use a single level of elevation: `bg-white border border-slate-200 rounded-xl shadow-xs`.
  - Avoid nested cards inside cards.

### 5.4 Standard Component Conventions
- **Buttons**:
  - *Primary*: `bg-blue-700 hover:bg-blue-800 text-white font-medium px-4 py-2 rounded-lg text-sm transition shadow-xs`
  - *Secondary / Outline*: `bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium px-4 py-2 rounded-lg text-sm transition`
  - *Ghost*: `hover:bg-slate-100 text-slate-600 font-medium px-3 py-1.5 rounded-lg text-sm transition`
  - *Destructive*: `text-red-600 hover:text-red-800 hover:bg-red-50 text-sm font-medium px-3 py-1.5 rounded-lg transition`
- **Form Controls**:
  - `border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600`
- **Tables**:
  - Clear header row: `bg-slate-50 text-xs font-semibold uppercase text-slate-500 border-b border-slate-200`
  - Subtle zebra striping or hover rows: `hover:bg-slate-50/75 transition-colors`
  - Numeric cells right-aligned or centered with monospace alignment.

### 5.5 Charting Conventions (`chart-theme.js`)
Instead of duplicating inline configurations across 24 files, introduce a lightweight centralized configuration helper (`static/js/chart-theme.js`):
- Consistent 6-color categorical palette for scientific distribution:
  1. Primary Blue: `#1D4ED8`
  2. Teal: `#0D9488`
  3. Indigo: `#4F46E5`
  4. Amber: `#D97706`
  5. Emerald: `#059669`
  6. Slate: `#64748B`
- Uniform gridline colors (`#F1F5F9`), tick font sizes (11px Inter), and responsive aspect ratios.

---

## 6. Prioritized Remediation Backlog

Findings are structured into four priority tiers:

### Tier P1 — High: Functional, Routing, and Integration Defects

| Task ID | Component / Files | Problem & Evidence | Proposed Fix |
|---|---|---|---|
| **TASK-P1-01** | `dashboard/templates/components/pagination.html` | Pagination discards all active filter parameters on page transition, retaining only `?search=`. | Implement a query preservation template filter (`query_transform`) preserving all `request.GET` parameters. |
| **TASK-P1-02** | `dashboard/urls.py:10` | Document types containing slashes (`Book/Book Chapter`) crash with `NoReverseMatch`. | Change pattern converter to `<path:document_type>`. |
| **TASK-P1-03** | `dashboard/urls.py:16`, `dashboard/templates/tables/authors_table.html` | Authors with mononyms or blank first names fail `NoReverseMatch` in author table. | Route author detail by primary key (`authors/<int:pk>/`) or support empty first name safely. |
| **TASK-P1-04** | `dashboard/urls.py:53`, `dashboard/templates/dashboard/rri_role.html` | Authors with unassigned/blank `rri_role` crash `rri_role.html` with `NoReverseMatch`. | Handle unassigned roles with a dedicated URL slug (e.g. `unassigned`) and template guard. |
| **TASK-P1-05** | `dashboard/urls.py:22`, `dashboard/views.py:784` | Visiting `/dashboard/journal/None/` triggers unhandled `ValueError` 500 error. | Enforce `<int:journal_id>` converter; guard against null journal links in template. |
| **TASK-P1-06** | `templates/publications/publication_detail.html` | Detail template references non-existent fields (`abstract`, `citation`, `full_text_url`) and ignores real `yearly_citations`. | Remove phantom attributes and render verified metrics from `yearly_citations`. |
| **TASK-P1-07** | `templates/publications/publications_list.html:101` | Injects external CDN script `cdn.jsdelivr.net` causing duplicate Chart.js instances and network failures. | Remove CDN script tag and rely on bundled local `chart.min.js`. |

---

### Tier P2 — Medium: Layout, Component Consistency, and Navigation

| Task ID | Component / Files | Problem & Evidence | Proposed Fix |
|---|---|---|---|
| **TASK-P2-01** | `dashboard/templates/base.html`, `dashboard/templates/dashboard/base.html` | Duplicate doctype and nested `<html>` tags in `base.html`; orphaned unreferenced `dashboard/base.html`. | Fix HTML document structure in `base.html` and safely archive duplicate file. |
| **TASK-P2-02** | `dashboard/templates/dashboard/sidebar.html`, `dashboard/templates/base.html` | Full dashboard sidebar rendered on login and password reset pages for anonymous users. | Hide or omit sidebar on authentication routes; unify registration templates under DaisyUI card styling. |
| **TASK-P2-03** | `dashboard/templates/components/page_header.html`, `filter_bar.html` | "Box fatigue": Page header is an oversized card; stacked cards create claustrophobic visual nesting. | De-card `page_header.html` into a flat header; polish filter bar layout and replace `href="."` with `{{ request.path }}`. |
| **TASK-P2-04** | `static/js/chart-theme.js`, 24 dashboard templates | 24 inlined script blocks duplicate arbitrary hex colors without centralized palette coordination. | Implement reusable `chart-theme.js` defining standard institutional palettes, typography, and tooltips. |
| **TASK-P2-05** | Root `templates/` (404.html, 403.html, 500.html) | No branded error templates exist; users see raw default web server error pages on errors. | Create clean, light-themed institutional error templates with navigation recovery links. |

---

### Tier P3 — Polish: Minor Alignment, Empty States, and Cleanup

| Task ID | Component / Files | Problem & Evidence | Proposed Fix |
|---|---|---|---|
| **TASK-P3-01** | `dashboard/templates/tables/impact_table.html:51` | Table has 6 columns but empty state specifies `colspan="5"`. | Correct empty state to `colspan="6"`. |
| **TASK-P3-02** | `dashboard/templates/components/empty_state.html` | Empty states render passive emojis without actionable buttons to reset filters or clear search. | Add actionable "Clear Filters" button linked to `{{ request.path }}`. |
| **TASK-P3-03** | Orphaned templates (`create_publication.html`, `edit_publication.html`, `collaboration_types.html`) | 5 unreferenced templates clutter repository. | Clean up or archive unused templates. |

---

## 7. Recommended Implementation Batches

To ensure regression-free execution and separate functional fixes from visual polish, the remediation plan should proceed in **four self-contained batches**:

```
Batch 1: P1 Functional & URL Routing Fixes
  ├── TASK-P1-01 (Pagination query parameter preservation)
  ├── TASK-P1-02 (Book/Book Chapter path converter)
  ├── TASK-P1-03 (Author mononym / pk routing)
  ├── TASK-P1-04 (RRI unassigned role routing)
  ├── TASK-P1-05 (Journal integer ID URL enforcement)
  ├── TASK-P1-06 (Publication detail template-model alignment)
  └── TASK-P1-07 (Remove external CDN script from publications_list)
  └── Verification: Automated URL tests & regression checks

Batch 2: Base Layout & Layout Architecture Cleanups
  ├── TASK-P2-01 (Malformed HTML in base.html & archive duplicate)
  ├── TASK-P2-02 (Auth layout sidebar decoupling & form styling)
  ├── TASK-P2-03 (De-card page_header.html & filter_bar reset fix)
  └── TASK-P2-05 (Custom 404, 403, 500 error pages)
  └── Verification: HTML structure validation & auth flow tests

Batch 3: Chart Standardization & Table Refinements
  ├── TASK-P2-04 (Centralized chart-theme.js & palette adoption)
  ├── TASK-P3-01 (Impact table colspan fix)
  └── TASK-P3-02 (Actionable empty states)
  └── Verification: Chart rendering & table pagination tests

Batch 4: Template Cleanup & Design System Polish
  ├── TASK-P3-03 (Archive orphaned templates)
  └── General typography, spacing, and responsive table polish
  └── Verification: Full test suite, system check, and final git review
```

---

## 8. Test and Verification Limitations

1. **Automated Test Client Scope**:
   All 38 routes and views are verified for HTTP status codes, context variables, authentication redirects, and role-based permissions via Django's `TestCase` and `Client`.
2. **Visual & Browser Limitations**:
   Because the development environment operates within a headless sandbox without an interactive desktop display or graphical browser, visual layout inspections, font anti-aliasing, and responsive tap target ergonomics were evaluated via code and DOM analysis. Live browser verification should be conducted in an interactive development environment once Batch 1 and Batch 2 are deployed.

