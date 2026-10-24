# Performance and Scalability: RRI Publications Dashboard

## 1. Database Query Patterns and N+1 Risk Analysis

The codebase demonstrates awareness of Django's query optimization tools, employing `select_related()` and `prefetch_related()` in multiple views. However, architectural workarounds in authorship identity handling introduce severe scalability bottlenecks.

### 1.1 Positive Query Optimization Practices
- **ForeignKey Optimization**: Catalog and dashboard views consistently apply `select_related("journal")` ([`dashboard/views.py:44`](../../dashboard/views.py#L44), [`publications/views.py:65`](../../publications/views.py#L65)), eliminating N+1 queries when accessing journal names or impact factors.
- **ManyToMany Prefetching**: Views prefetch authors and departments via `prefetch_related("authors", "departments")`.
- **Targeted Prefetches**: [`dashboard/views.py:346-350`](../../dashboard/views.py#L346-L350) utilizes a custom `Prefetch` object with `select_related("affiliation")` on `author_affiliations`:
  ```python
  Prefetch(
      "author_affiliations",
      queryset=AuthorAffiliation.objects.select_related("affiliation"),
  )
  ```

### 1.2 Identified Query Deficiencies and Inefficiencies
1. **Python-Level Aggregations Over Database Calculations**:
   - In [`dashboard/views.py:599-601`](../../dashboard/views.py#L599-L601) (`AuthorDetailView`):
     ```python
     total_if = sum(p.journal.impact_factor or 0 for p in publications if p.journal)
     avg_if = total_if / total_publications if total_publications else 0
     ```
   - **Impact**: Evaluates the full `publications` queryset into Python memory to sum impact factors in a Python loop rather than delegating the calculation to the database engine via `publications.aggregate(Sum("journal__impact_factor"))`.
2. **Subquery Redundancy in KPI Calculations**:
   - In [`dashboard/views.py:69-73`](../../dashboard/views.py#L69-L73) (`DashboardHomeView`):
     ```python
     "active_authors": (
         Author.objects.filter(publications__in=publications)
         .distinct()
         .count()
     )
     ```
   - When filters are active, `publications__in=publications` generates an expensive SQL `IN (SELECT ...)` subquery that executes synchronously during dashboard rendering.
3. **Cartesian Product Risk in Multi-Join Text Search**:
   - In [`dashboard/filters.py:159-164`](../../dashboard/filters.py#L159-L164), `DynamicFilter.search_filter()` joins across `authors` and `departments` simultaneously:
     ```python
     q |= Q(**{f"{field}__icontains": value})
     return qs.filter(q).distinct()
     ```
   - Joining two distinct Many-to-Many relationships (`authors` and `departments`) causes SQLite to construct a Cartesian product of join rows before executing `DISTINCT`, causing noticeable query latency on large catalogs.

---

## 2. In-Memory Processing and Memory Scalability Bottlenecks

The most critical architectural performance risk lies in **in-memory data restructuring pipelines** implemented within analytical views.

```
+---------------------------------------------------------------------------------------+
|  1. SQL Database Layer:                                                               |
|     Author.objects.filter(...).annotate(total=Count('publications')).distinct()       |
|     (Returns EVERY duplicate Author row created across all historic imports)          |
+---------------------------------------------------------------------------------------+
                                           |
                                (10,000+ records)
                                           v
+---------------------------------------------------------------------------------------+
|  2. Server RAM (Python Memory):                                                       |
|     merged_authors = {}                                                               |
|     for author in authors:                                                            |
|         key = (author.first_name.strip().lower(), author.last_name.strip().lower())   |
|         # In-memory dictionary grouping, string stripping, sets aggregation           |
+---------------------------------------------------------------------------------------+
                                           |
                                (5,000 unique records)
                                           v
+---------------------------------------------------------------------------------------+
|  3. Python Sorting & Range Filtering:                                                 |
|     - authors = [a for a in authors if a.total_publications > gt_value]              |
|     - authors.sort(key=lambda x: x.total_impact_factor, reverse=True)                 |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|  4. In-Memory Pagination:                                                             |
|     paginator = Paginator(authors, 10)  # Slices in-memory list                       |
+---------------------------------------------------------------------------------------+
```

### 2.1 Affected Views
- **`AuthorsView`** ([`dashboard/views.py:358-450`](../../dashboard/views.py#L358-L450)): Pulls all author records, loops in Python, builds sets of affiliations, merges publications and impact factors into dictionaries, filters ranges in Python, sorts in Python, and paginates in Python.
- **`CountryCollaborationView`** ([`dashboard/views.py:1276-1335`](../../dashboard/views.py#L1276-L1335)): Pulls country rows, strips trailing semicolons in a Python loop, merges into dicts, sorts in Python, and paginates.
- **`InstitutionCollaborationView`** ([`dashboard/views.py:1471-1525`](../../dashboard/views.py#L1471-L1525)): Pulls institution rows, strips whitespace in Python, merges, sorts, and paginates.

### 2.2 Scalability Impact
- **Memory Consumption**: For 5,000 publications and 25,000 author entries, instantiating full model instances and allocating sets for every row will consume 150MB+ of RAM per request.
- **CPU Saturation**: Under concurrent user requests, Python GIL lock contention and CPU saturation during string manipulation and list sorting will cause request queuing and slow response times.
- **Remediation**: Author canonicalization must be solved at the database schema level so standard SQL `GROUP BY`, `ORDER BY`, and SQL `LIMIT/OFFSET` pagination can execute entirely inside the database engine.

---

## 3. Database Concurrency and Storage Constraints

1. **SQLite Concurrency Bottleneck**:
   - The project uses SQLite 3 (`db.sqlite3`).
   - SQLite uses file-level locking: when a library officer uploads a Web of Science file and executes `wos_save` (an atomic transaction writing hundreds of rows), SQLite places an exclusive lock on the entire database file.
   - Any concurrent visitor attempting to browse `/dashboard/` or `/publications/` during this write transaction will encounter locking delays or `sqlite3.OperationalError: database is locked`.
   - **Production Requirement**: Migrate to PostgreSQL or MySQL before opening the platform to concurrent institutional traffic.
2. **Missing Database Indexes**:
   - Critical lookup columns lack explicit indexes:
     - `Publication.date_published`
     - `Publication.document_type`
     - `Publication.collaboration_type`
     - `Publication.doi`
   - Adding `indexes = [models.Index(fields=['date_published']), ...]` in `Publication.Meta` will allow the database to bypass full table scans during filtering.

---

## 4. Synchronous Processing and Caching Opportunities

1. **Synchronous File Processing**:
   - In [`publications/views.py:201-218`](../../publications/views.py#L201-L218), Web of Science parsing executes synchronously inside the HTTP POST thread.
   - A large multi-year WoS export file (e.g. 5,000 records) will take 10-30 seconds to parse and serialize, exceeding standard WSGI/Nginx gateway timeouts (e.g., 30s or 60s).
   - **Remediation**: Move file parsing to an asynchronous task queue (e.g. Celery, Django-Q, or Huey).
2. **Caching Absence**:
   - The application has zero caching configured.
   - **High-ROI Opportunities**:
     - **Dashboard Aggregate Metrics**: Aggregations for `/dashboard/` and `/dashboard/trends/` change only when new publications are uploaded. Caching aggregated metric dictionaries in Redis or LocMem with a 24-hour TTL (invalidated on `Publication.save()`) will reduce database queries to near-zero for regular browsing.
     - **Sidebar Navigation**: Cache `dashboard_sidebar` context processor output per session or globally.

