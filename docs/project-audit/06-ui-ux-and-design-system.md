# UI/UX and Design System: RRI Publications Dashboard

## 1. Visual Identity and Branding

| Branding Element | Implementation Details | Evidence / Repository Reference |
| :--- | :--- | :--- |
| **Institutional Brand** | Raman Research Institute (RRI), Bangalore | [`dashboard/templates/dashboard/sidebar.html:32`](../../dashboard/templates/dashboard/sidebar.html#L32) |
| **Application Name** | Research Dashboard / Research Insights | [`dashboard/templates/dashboard/sidebar.html:31`](../../dashboard/templates/dashboard/sidebar.html#L31), [`README.md:1`](../../README.md#L1) |
| **Logo / Icon Mark** | Monogram badge: Dark rounded box (`bg-neutral text-neutral-content`) containing a bold capital letter **"R"** | [`dashboard/templates/dashboard/sidebar.html:27-29`](../../dashboard/templates/dashboard/sidebar.html#L27-L29) |
| **Browser Title** | `{% block title %}RRI Publications Dashboard{% endblock %}` | [`dashboard/templates/base.html:13`](../../dashboard/templates/base.html#L13) |
| **Favicon** | *Not configured* (No `<link rel="icon">` in HTML head) | [`dashboard/templates/base.html:1-25`](../../dashboard/templates/base.html#L1-L25) |
| **Active Theme** | DaisyUI `light` theme (`data-theme="light"`) | [`dashboard/templates/base.html:4`](../../dashboard/templates/base.html#L4) |

> [!NOTE]
> *Inspection Limitation Disclaimer*: This design audit is derived strictly from static code analysis of Django templates, compiled PostCSS stylesheets, and vendor JavaScript assets. Browser rendering and visual screenshot inspection were not performed.

---

## 2. Color System and Palette

The user interface uses a combination of **DaisyUI semantic theme tokens** for dashboard pages and **custom hardcoded institutional HEX colors** in publication forms.

### 2.1 Verified Color Palette

| Token / HEX | Visual Sample | Semantic Role | Source Code References | Usage in UI |
| :--- | :--- | :--- | :--- | :--- |
| **`#0A4DA3`** | `■` Deep RRI Navy | Institutional Primary | [`publications/forms.py:7, 11`](../../publications/forms.py#L7), [`create_publication.html:6, 10, 24`](../../templates/publications/create_publication.html#L6) | Form focus rings (`focus:ring-[#0A4DA3]`), form headers, buttons in manual form drafts |
| **`#4f46e5`** | `■` Indigo 600 | Primary Chart Bar | [`dashboard.html:117`](../../dashboard/templates/dashboard/dashboard.html#L117), [`trends.html:245`](../../dashboard/templates/dashboard/trends.html#L245) | Default bar chart fills for document types and publication counts |
| **`#06b6d4`** | `■` Cyan 500 | Trend Line & Accent | [`dashboard.html:145`](../../dashboard/templates/dashboard/dashboard.html#L145), [`publications_list.html:180`](../../templates/publications/publications_list.html#L180) | Line chart strokes, area fill gradients (`rgba(6,182,212,.2)`) |
| **`#8b5cf6`** | `■` Purple 500 | Secondary Chart Line | [`trends.html:265`](../../dashboard/templates/dashboard/trends.html#L265) | Secondary comparison series in multi-dataset trends |
| **`#22c55e`** | `■` Green 500 | Success / Impact | [`impact.html:85`](../../dashboard/templates/dashboard/impact.html#L85), [`journals.html:210`](../../dashboard/templates/dashboard/journals.html#L210) | High impact factor indicators, success badges |
| **`#f59e0b`** | `■` Amber 500 | Warning / Mid-Impact | [`journals.html:215`](../../dashboard/templates/dashboard/journals.html#L215) | Medium impact factor badges, warnings |
| **`#ef4444`** | `■` Red 500 | Error / Destructive | [`sidebar.html:105`](../../dashboard/templates/dashboard/sidebar.html#L105), [`login.html:8`](../../templates/registration/login.html#L8) | Logout button (`btn-error`), validation error text |
| **`#14b8a6`** | `■` Teal 500 | Collaboration Accent | [`collaboration.html:130`](../../dashboard/templates/dashboard/collaboration.html#L130) | Collaboration distribution bar charts |
| **`#ec4899`** | `■` Pink 500 | Categorical Chart | [`document_types.html:185`](../../dashboard/templates/dashboard/document_types.html#L185) | Multi-color bar charts for document types |

### 2.2 DaisyUI Semantic Tokens (Default Light Theme)

| Semantic Class | Computed Light Value | Primary Application |
| :--- | :--- | :--- |
| **`bg-base-100`** | `#ffffff` (Pure White) | Card surfaces, modal backgrounds, input fields, header navbar |
| **`bg-base-200`** | `#f2f2f2` (Light Neutral Gray) | Main viewport body background (`<body class="bg-base-200">`) |
| **`bg-base-300`** | `#e5e6e6` (Border / Hover Gray) | Card borders, dividers, active navigation background |
| **`text-base-content`** | `#1f2937` (Dark Charcoal) | Primary headings, body copy, table text |
| **`text-base-content/60`** | `rgba(31,41,55,0.6)` (Muted Gray) | Subtitles, breadcrumb non-active links, table footer labels |
| **`bg-neutral`** | `#2b3440` (Dark Slate) | Brand mark logo badge, sidebar active pill, primary action buttons |

---

## 3. Typography and Iconography

### 3.1 Font Family Hierarchy
- **Primary Font Stack**: The project relies on Tailwind's default system font stack declared via PostCSS:
  ```css
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  ```
- **Monospace Stack**: Used for code blocks, DOIs, and file tags:
  ```css
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  ```
- **Font Sourcing**: Zero external web fonts (e.g., Google Fonts or Adobe Fonts) are loaded over the network. All rendering uses local client system fonts.

### 3.2 Typographic Scale and Hierarchy

| Level | Tailwind Classes | Usage Across Templates |
| :--- | :--- | :--- |
| **Display / Page Header** | `text-3xl font-bold tracking-tight` | [`components/page_header.html:43`](../../dashboard/templates/components/page_header.html#L43) |
| **Card / Section Titles** | `card-title text-base sm:text-lg font-bold` | [`components/chart_card.html:6`](../../dashboard/templates/components/chart_card.html#L6), [`dashboard.html:31`](../../dashboard/templates/dashboard/dashboard.html#L31) |
| **KPI Stat Numbers** | `stat-value text-3xl sm:text-4xl font-extrabold` | [`components/stats_cards.html:7`](../../dashboard/templates/components/stats_cards.html#L7) |
| **Body Text** | `text-sm text-base-content` | Table cells, form labels, paragraph descriptions |
| **Subtitles / Footnotes** | `text-xs sm:text-sm text-base-content/60` | Header subtitles, timestamp annotations, pagination counts |

### 3.3 Iconography (Lucide Icons)
- **Engine**: Bundled client library [`static/js/lucide.min.js`](../../static/js/lucide.min.js).
- **Execution**: Initialized on DOM ready and re-evaluated upon Alpine sidebar state transitions:
  ```javascript
  this.$nextTick(() => lucide.createIcons());
  ```
- **Icon Inventory**:
  - Analytics: `layout-dashboard`, `trending-up`, `activity`, `chart-bar`
  - Publications: `book-open`, `file-text`, `handshake`, `globe`, `building`, `library`
  - Management & User: `users`, `book`, `badge-check`, `log-in`, `log-out`, `chevron-left`, `x`

---

## 4. Layout Architecture and Responsive Behavior

The global application layout is governed by [`dashboard/templates/base.html`](../../dashboard/templates/base.html) and [`dashboard/templates/dashboard/sidebar.html`](../../dashboard/templates/dashboard/sidebar.html).

```
+---------------------------------------------------------------------------------------+
|                                    FIXED HEADER NAVBAR                                |
|  [Hamburger (Mobile)]  Page Title (e.g. "Research Dashboard")                         |
+---------------------------------------------------------------------------------------+
|  FIXED ASIDE SIDEBAR  |                          MAIN CONTENT                         |
|  - Brand Logo & Name  |  [Breadcrumbs]                                                |
|  - Section: Analytics |  [Page Header Card with Title & Subtitle]                     |
|  - Section: Pubs      |  [Dynamic Filter Bar Card]                                    |
|  - Section: Manage    |  [KPI Stats Cards Row]                                        |
|  - Collapsible Toggle |  [Chart Cards Grid (1-col or 2-col)]                          |
|  - User Profile/Logout|  [Data Table Card with Striped Rows & Pagination]             |
+-----------------------+---------------------------------------------------------------+
```

### 4.1 Collapsible Sidebar (Alpine.js State Machine)
- **Desktop Behavior (`>= 1024px`)**:
  - Expanded width: `w-72` (288px). Main content applies margin `lg:ml-72`.
  - Collapsed width: `w-19` (76px). Main content applies margin `lg:ml-[76px]`.
  - Toggled by floating circular button on the right border: `<i data-lucide="chevron-left" :class="isCollapsed && 'rotate-180'">`.
  - State persisted across page navigations in browser `localStorage.getItem("sidebarCollapsed")`.
- **Mobile Behavior (`< 1024px`)**:
  - Sidebar is hidden offscreen with `-translate-x-full`.
  - Clicking the hamburger button slides the sidebar into view (`translate-x-0`) with a dark backdrop overlay (`bg-black/50 fixed inset-0 z-40`).

---

## 5. Reusable Component Inventory

| Component Path | Component Role | Key Features & CSS Classes |
| :--- | :--- | :--- |
| [`components/page_header.html`](../../dashboard/templates/components/page_header.html) | View Header | Card container, optional breadcrumbs list, icon badge (`bg-info/10 text-2xl`), title, subtitle, action buttons slot |
| [`components/stats_cards.html`](../../dashboard/templates/components/stats_cards.html) | KPI Metric Block | DaisyUI `stat`, `stat-title`, `stat-value {{ color }}`, optional `stat-desc` |
| [`components/filter_bar.html`](../../dashboard/templates/components/filter_bar.html) | Faceted Filter Bar | 5-column responsive grid (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-5`), badge active indicator, Apply & Reset buttons |
| [`components/chart_card.html`](../../dashboard/templates/components/chart_card.html) | Chart Container | Card wrapper with header and fixed height canvas container (`h-80`) |
| [`components/data_table.html`](../../dashboard/templates/components/data_table.html) | Master Table Wrapper| Includes result counter header, responsive `overflow-x-auto` wrapper, and pagination footer |
| [`components/pagination.html`](../../dashboard/templates/components/pagination.html) | Pagination Bar | DaisyUI `join` container with first, previous, current/total, next, and last page buttons |
| [`components/empty_state.html`](../../dashboard/templates/components/empty_state.html) | Zero State Placeholder| Centered emoji (`📊`), title, and descriptive advice ("Try changing your filters") |

---

## 6. Page-by-Page Audit and UX Inconsistencies

### 6.1 Critical Layout Bugs
1. **HTML Doctype Duplication in `dashboard/templates/base.html`**:
   - Lines 1-6 duplicate the doctype and HTML tags:
     ```html
     {% load static tailwind_tags %}
     <!doctype html>
     <html lang="en" data-theme="light">
       {% load static tailwind_tags %}
       <!doctype html>
       <html lang="en" data-theme="light">
     ```
   - Lines 79-80 close with two `</html>` tags: `</body> </html> </html>`.
   - While modern browsers auto-correct this invalid markup, it causes validation failures and potential quirks-mode rendering in strict browsers.

### 6.2 UX and Design Deficiencies
1. **Hardcoded Color Token Inconsistency**:
   - Publications templates ([`upload.html`](../../templates/publications/upload.html), [`review.html`](../../templates/publications/review.html)) and [`forms.py`](../../publications/forms.py) use hardcoded `#0A4DA3` and standard Tailwind classes (`bg-blue-700`, `text-gray-800`), whereas `dashboard` templates exclusively use DaisyUI tokens (`btn-info`, `btn-primary`, `bg-base-100`, `text-base-content`).
   - This causes visual divergence between the catalog/upload workflow and the analytics dashboards.
2. **Filter Loss on Pagination**:
   - In [`components/pagination.html:43`](../../dashboard/templates/components/pagination.html#L43), the pagination links only preserve `request.GET.search`:
     ```html
     href="?page={{ page_obj.next_page_number }}{% if request.GET.search %}&search={{ request.GET.search }}{% endif %}"
     ```
   - Clicking page 2 permanently wipes out all date range filters, document type selections, and collaboration filters.
3. **Missing Feedback on Empty Table Results**:
   - In several table views, if a filter yields 0 records, the table headers render over an empty whitespace rather than displaying [`components/empty_state.html`](../../dashboard/templates/components/empty_state.html).
4. **Unformatted Big Numbers**:
   - Metric cards displaying publication counts or citations output raw integer strings (e.g. `12450`) rather than localized formatted numbers (`12,450`).

