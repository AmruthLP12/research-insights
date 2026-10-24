# Testing, Quality, and Maintainability: RRI Publications Dashboard

## 1. Automated Test Coverage and Execution Results

### 1.1 Verified Test Execution

The Django test runner was executed inside the project's virtual environment:

```bash
$ python manage.py test
Found 0 test(s).
System check identified no issues (0 silenced).

----------------------------------------------------------------------
Ran 0 tests in 0.000s

NO TESTS RAN
```

- **Current Test Coverage**: **0.00%** across all applications.
- **Test File Inventory**:
  - [`accounts/tests.py`](../../accounts/tests.py): 3 lines containing `# Create your tests here.`
  - [`dashboard/tests.py`](../../dashboard/tests.py): 3 lines containing `# Create your tests here.`
  - [`publications/tests.py`](../../publications/tests.py): 3 lines containing `# Create your tests here.`

---

## 2. Critical Test Coverage Gaps

Because there are zero automated tests, regressions in core business logic and parsing routines cannot currently be detected prior to deployment. The following areas represent high-priority test gaps:

| Critical Area | Risk Description | Key Test Cases Needed |
| :--- | :--- | :--- |
| **Web of Science TSV Parser** | Edge-case syntax variations in Clarivate export files | - Files with missing `C1` affiliation blocks<br>- Files with multiple authors per bracket `[Author A; Author B]`<br>- Incomplete records missing publication years (`PY`) or titles (`TI`)<br>- Non-standard character encodings or BOM headers |
| **RRI Affiliation Detection** | False positives/negatives in institutional tagging | - Verifying strings: `"Raman Res Inst"`, `"RRI, Bangalore"`, `"C.V. Raman"`<br>- Rejecting non-RRI institutions with similar names |
| **Metrics & Aggregations** | Mathematical exceptions during metric calculation | - Zero publications handling (avoiding `ZeroDivisionError` in average impact factor)<br>- Publications linked to journals with `null` impact factors |
| **DynamicFilter Engine** | Malformed query parameter injection | - Passing non-numeric strings to `total_publications_gt`<br>- Passing invalid dates (`date_published_from=invalid-date`)<br>- Multi-term search queries across foreign key relationships |
| **Database Transaction Rollback** | Partial database writes during failed ingestion | - Raising validation errors mid-way through `wos_save` to verify `transaction.atomic` rolls back publication and author creations |
| **Authentication & Permissions** | Unintended public exposure of sensitive views | - Verifying anonymous redirects on `/publications/wos/upload/`<br>- Verifying future role checks for `"viewer"` vs `"admin"` |

---

## 3. Code Quality, Linting, and Typing

### 3.1 Static Analysis Configuration

| Tool | Status | Configuration Location | Configured Settings |
| :--- | :--- | :--- | :--- |
| **djLint** | **Installed** (`1.40.8`) | [`.djlintrc:1-4`](../../.djlintrc#L1-L4), [`pyproject.toml:1-3`](../../pyproject.toml#L1-L3) | Profile set to `"django"`. Rules ignored: `H030,T003,H031,H021,H006,H013,H014,T001,H029,H025`. |
| **Ruff** | **Uninstalled** | [`pyproject.toml:4-5`](../../pyproject.toml#L4-L5) | Configured with lint ignore list (`RUF012`, `RUF010`, `BLE001`, `TRY004`, `TRY401`, `FURB157`, etc.), but `ruff` package is not declared in `requirements.txt`. |
| **Type Checking (Mypy)** | **Absent** | None | Zero type annotations (`from typing import ...`) exist in Python files. No `mypy.ini` or `pyrightconfig.json` exists. |

---

## 4. Code Architecture and Maintainability Analysis

### 4.1 Monolithic Bloat in `dashboard/views.py`
- **File Length**: 2,112 lines of code in a single file.
- **Architectural Duplication**: `dashboard/views.py` contains 21 distinct `TemplateView` subclasses. The majority of these views repeat the identical multi-step pattern:
  1. Base queryset construction with `select_related()` and `prefetch_related()`.
  2. Dynamic filter instantiation.
  3. Metric dictionary aggregation (`total_publications`, `total_impact_factor`, `average_impact_factor`).
  4. In-memory data merging.
  5. Paginator instantiation and context assembly.
- **Refactoring Recommendation**: Decompose `dashboard/views.py` into a package (`dashboard/views/`) organized by domain: `authors.py`, `journals.py`, `collaborations.py`, `trends.py`, and create a shared `BaseDashboardView` mixin.

### 4.2 Dead and Orphaned Code Inventory

| Artifact | Nature | File Path | Impact & Recommendation |
| :--- | :--- | :--- | :--- |
| **`views_dashboard.py`** | Dead Code | [`publications/views_dashboard.py`](../../publications/views_dashboard.py) | A 109-line legacy dashboard view prototype referencing a non-existent template (`publications/dashboard/dashboard.html`). Safe to delete. |
| **`tables.py`** | Phantom Code | [`dashboard/tables.py`](../../dashboard/tables.py) | Imports uninstalled library `django-tables2`. Unused by any view. Safe to delete. |
| **`create_publication.html`** | Orphan Template | [`templates/publications/create_publication.html`](../../templates/publications/create_publication.html) | Complete manual publication creation form with complex client JS, but no URL pattern or view exists. Either wire up or archive. |
| **`edit_publication.html`** | Orphan Template | [`templates/publications/edit_publication.html`](../../templates/publications/edit_publication.html) | Manual publication edit form with no URL pattern or view. |
| **`publication_form.html`** | Orphan Template | [`templates/publications/publication_form.html`](../../templates/publications/publication_form.html) | Bare-bones form prototype with no URL pattern or view. |

### 4.3 Error Handling and Exception Strategy
- **Generic Try-Except Blocks**:
  - In [`publications/templatetags/json_extras.py:10-12`](../../publications/templatetags/json_extras.py#L10-L12):
    ```python
    @register.filter
    def json_loads(value):
        try:
            return json.loads(value)
        except:
            return []
    ```
    Uses bare `except:`, which catches `KeyboardInterrupt` and `SystemExit`. Should be refined to `except (json.JSONDecodeError, TypeError):`.
- **Parser Exception Handling**:
  - [`publications/utils/wos_parser.py:64`](../../publications/utils/wos_parser.py#L64) decodes files with `errors="ignore"`. While this prevents crashes on invalid characters, it may silently drop non-ASCII author names or institutional accents.

