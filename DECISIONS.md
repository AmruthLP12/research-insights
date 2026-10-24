# Architecture and Engineering Decision Log (DECISIONS.md)

This document records the architectural, security, and engineering decisions made during the maintenance, remediation, and modernization of the RRI Publications Dashboard (*Research Insights*).

---

## Decision Record Index

| ID | Title | Date | Status |
| :--- | :--- | :--- | :--- |
| **[D-001](#d-001-incremental-remediation-workflow)** | Incremental Remediation Workflow and Evidence-Based Verification | 2026-10-24 | **Accepted** |
| **[D-002](#d-002-environment-driven-security-settings-and-fail-closed-configuration)** | Environment-Driven Security Settings and Fail-Closed Configuration | 2026-10-24 | **Accepted** |
| **[D-003](#d-003-settings-module-refactoring-and-strict-environment-validation)** | Settings Module Refactoring and Strict Environment Validation | 2026-10-24 | **Accepted** |
| **[D-004](#d-004-separation-of-environment-helpers-into-envpy)** | Separation of Environment Helpers into Dedicated env.py Module | 2026-10-24 | **Accepted** |

---

## D-001: Incremental Remediation Workflow and Evidence-Based Verification

### Context
A comprehensive technical audit of the RRI Publications Dashboard identified critical configuration vulnerabilities, database schema drift, zero automated test coverage, and several performance bottlenecks (see [`docs/project-audit/`](docs/project-audit/)).

Because there is currently **0% automated test coverage**, attempting broad or coupled refactorings introduces severe risks of regression, schema corruption, and broken ingestion workflows. Furthermore, prior audit documents may describe states that could change or contain nuances requiring code-level verification.

### Decision

1. **One Focused Change at a Time**:
   - All subsequent remediation tasks must address a single, tightly scoped problem (e.g., resolving `article_number` schema drift, unblocking `collectstatic`, wiring environment variables).
   - Tasks must never combine unrelated changes (such as refactoring views while editing database models).

2. **Source Code as Primary Truth**:
   - Before implementing any change, the engineer or agent must inspect the actual current files on disk to verify the existing behavior, rather than blindly trusting audit notes or documentation.

3. **Mandatory Dual-Tracking Documentation**:
   - Every completed remediation step must update both:
     - `CHANGELOG.md`: Records what was changed, files affected, tests/checks run, results, and limitations.
     - `DECISIONS.md`: Records significant architectural or procedural decisions, their rationale, alternatives considered, and consequences.
   - Documentation must be updated in the **same task** as the code change. Documentation must never be deferred to a later step.
   - If a task modifies no application code, this must be stated explicitly.

4. **Honest Reporting of Failures and Risks**:
   - A failed test, unresolved risk, or unverified claim must be recorded honestly.
   - Planned, partial, or unverified work must never be represented as successfully completed.

5. **Safety Checks for State-Altering Operations**:
   - **Database Changes**: Must verify schema drift via `makemigrations --dry-run` and inspect generated SQL before applying migrations. Avoid destructive drops or unverified table resets.
   - **Data Cleanup**: Must verify relationship constraints (`on_delete`) to avoid accidental cascade deletions.
   - **Security Configurations**: Must retain working development defaults while hardening production paths.
   - **Deployment Configurations**: Must ensure files and dependencies referenced in build scripts actually exist.

### Conventions for Subsequent Tasks

- **Decision Identifiers**: Use stable, sequential IDs (`D-001`, `D-002`, `D-003`, etc.).
- **Decision Template**:
  ```markdown
  ## D-XXX: Title
  - **Date**: YYYY-MM-DD
  - **Status**: Proposed | Accepted | Deprecated | Superseded by D-YYY
  - **Context**: Problem statement, background, constraints.
  - **Decision**: Specific choice made.
  - **Alternatives Considered**: Other approaches evaluated and reasons for rejection.
  - **Consequences**: Positive benefits, trade-offs, and downstream impacts.
  ```

---

## D-002: Environment-Driven Security Settings and Fail-Closed Configuration

- **Date**: 2026-10-24
- **Status**: Accepted
- **Context**:
  The initial security audit ([`07-authentication-authorization-and-security.md`](docs/project-audit/07-authentication-authorization-and-security.md)) identified that `rri_publications_dashboard/settings.py` had hardcoded `DEBUG = True`, a hardcoded `SECRET_KEY` starting with `django-insecure-`, and `ALLOWED_HOSTS = ['*']`. This opened the application to critical security vulnerabilities (session hijacking, cryptographic tampering, and Host-header injection) if deployed without modification.

  Because the project had 0% automated test coverage, the solution needed to harden the application strictly against production misconfigurations while avoiding adding heavy dependencies (such as `django-environ` or `dynaconf`) that could disrupt existing local development workflows.

- **Decision**:
  1. **Zero External Dependencies for Configuration**:
     - Implement environment loading using only Python's standard library (`os`, `pathlib.Path`, `secrets`).
     - Parse `.env` files manually if present in the repository root without overwriting existing environment variables (allowing container or shell variables to take precedence).
  2. **Fail-Closed Production Posture**:
     - In production (`DEBUG=False`):
       - `DJANGO_SECRET_KEY` is mandatory. The application refuses to start (`ImproperlyConfigured`) if it is missing, shorter than 50 characters, or starts with the default Django insecure prefix (`django-insecure-`).
       - `ALLOWED_HOSTS` is mandatory. The application refuses to start if empty or if it contains a wildcard (`*`).
  3. **Frictionless Local Development**:
     - In development (`DEBUG=True`):
       - If `DJANGO_SECRET_KEY` is not provided, Django generates a process-ephemeral random secret key (`django-insecure-dev-...`), allowing local developers and CI runners to start immediately without setup roadblocks.
       - If `ALLOWED_HOSTS` is not provided, it defaults to safe local loopback interfaces (`localhost`, `127.0.0.1`, `[::1]`).
  4. **Explicit Boolean Parsing**:
     - `DEBUG` is parsed strictly against recognized string representations: `('true', '1', 'yes', 't', 'on')` evaluates to `True`; anything else evaluates to `False`. Defaults to `False` if unset.

- **Alternatives Considered**:
  - **Add `django-environ` or `python-dotenv`**: Rejected to avoid modifying `requirements.txt` prematurely and introducing dependency management overhead for a task that standard library code cleanly satisfies in under 30 lines.
  - **Fail local development if `DJANGO_SECRET_KEY` is unset**: Evaluated, but generating an ephemeral key for `DEBUG=True` avoids breaking quick setup, new developer onboarding, and ad-hoc local testing while preserving absolute strictness when `DEBUG=False`.
  - **Allow `ALLOWED_HOSTS = ['*']` in development**: Rejected; restricting development defaults to loopback (`localhost`, `127.0.0.1`, `[::1]`) while allowing comma-separated host additions prevents DNS rebinding vulnerabilities even on local workstations.

- **Consequences**:
  - **Positive**:
    - `security.W009` (`SECRET_KEY`) and `security.W018` (`DEBUG`) warnings from `manage.py check --deploy` are resolved.
    - Accidental production deployment with default debug mode or wildcard hosts is impossible; startup crashes immediately with explicit configuration errors.
    - Zero changes to `requirements.txt` or third-party packages.
  - **Negative / Trade-offs**:
    - Production deployments must explicitly provide valid `DJANGO_SECRET_KEY` (min 50 chars) and `ALLOWED_HOSTS` environment variables or `.env` files.

---

## D-003: Settings Module Refactoring and Strict Environment Validation

- **Date**: 2026-10-24
- **Status**: Accepted
- **Context**:
  Following the initial environment hardening in `D-002`, `settings.py` required cleanup to improve readability, structure, and reliability. Specifically:
  1. Imports were fragmented across the module (e.g. `import secrets` inside an execution block).
  2. Boolean parsing silently converted unrecognized strings (`DEBUG=maybe`) to `False`, masking configuration typos.
  3. Generating an ephemeral random secret key on every process startup in development invalidated user sessions and CSRF tokens across local `runserver` reloads.
  4. Related settings (such as authentication models, URLs, and password validators) were dispersed across unrelated sections.

- **Decision**:
  1. **Top-Level Imports & Logical Sectioning**:
     - Consolidate all standard library and Django imports at the top of `settings.py`.
     - Organize settings into standard, labeled sections (`BASE DIRECTORIES`, `ENVIRONMENT LOADING & HELPERS`, `CORE SECURITY SETTINGS`, `APPLICATION DEFINITION`, `MIDDLEWARE`, `URLS & WSGI`, `TEMPLATES`, `AUTHENTICATION & USERS`, `DATABASE`, `INTERNATIONALIZATION`, `STATIC FILES`, `DEFAULT AUTO FIELD`, `TAILWIND & THEME`).
  2. **In-File Helpers without Unnecessary Abstractions**:
     - Maintain lightweight helpers (`_load_env_file`, `_parse_bool`, `_parse_list`) directly inside `settings.py`. Extracting them to a separate package or module was evaluated but rejected as premature abstraction for ~35 lines of straightforward parsing.
  3. **Strict Boolean Parsing**:
     - Upgrade `_parse_bool` to reject any unrecognized string with `ImproperlyConfigured`, preventing silent misconfigurations when operators mistype boolean flags. Unset or empty values safely default to `False`.
  4. **Stable Development Secret Fallback**:
     - Replace dynamic ephemeral key generation with a fixed, static development fallback (`DEV_SECRET_KEY_FALLBACK`). This prevents local session invalidation on auto-reload while ensuring `DEBUG=False` still strictly requires a secure, non-default production key (>= 50 chars).
  5. **Backward-Compatible Secret Key Resolution**:
     - Document `DJANGO_SECRET_KEY` as canonical, while retaining fallback lookup for `SECRET_KEY` to prevent breaking existing deployment scripts or environment definitions.

- **Alternatives Considered**:
  - **Separate `env.py` helper module**: Rejected to avoid unnecessary indirection and file proliferation for simple, local environment reading.
  - **Requiring manual `.env` creation before `manage.py` can run in dev**: Rejected to ensure new contributors and automated tests can run without mandatory setup steps while maintaining strict production checks.
  - **Silent fallback for malformed booleans**: Rejected because silent defaults hide operator errors and can lead to unexpected security posture.

- **Consequences**:
  - **Positive**:
    - Cleaner, standard Django settings structure with consistent formatting.
    - Developer sessions persist across local code reloads.
    - Configuration typos in `DEBUG` fail fast with clear actionable error messages.
    - Zero external dependencies introduced.
  - **Negative / Trade-offs**:
    - Developers relying on informal boolean synonyms outside `('true', '1', 'yes', 't', 'on')` and `('false', '0', 'no', 'f', 'off')` must use supported values.

---

## D-004: Separation of Environment Helpers into Dedicated env.py Module

- **Date**: 2026-10-24
- **Status**: Accepted
- **Context**:
  In `D-002` and `D-003`, environment loading and security validation helpers were consolidated directly within `rri_publications_dashboard/settings.py`. While this minimized initial file proliferation, mixing 70+ lines of imperative parsing, file I/O, and validation routines with declarative Django settings compromised the readability of `settings.py` and made isolated unit testing of configuration functions awkward without triggering full Django settings evaluation.

- **Decision**:
  1. **Dedicated `env.py` Module**:
     - Extract all environment loading and validation functions (`load_env_file`, `parse_bool`, `get_bool`, `parse_list`, `get_list`, `get_secret_key`, `get_allowed_hosts`) and constants (`DEV_SECRET_KEY_FALLBACK`, `TRUE_STRINGS`, `FALSE_STRINGS`) into `rri_publications_dashboard/env.py`.
  2. **Clean Declarative `settings.py`**:
     - Keep `settings.py` purely declarative by importing the helpers via `from .env import get_allowed_hosts, get_bool, get_secret_key, load_env_file`.
  3. **Strict Boundaries & No Framework Creep**:
     - Keep `env.py` strictly focused on environment variables; avoid creating a general-purpose settings engine or introducing third-party configuration libraries (`django-environ`, `dynaconf`).
  4. **Preserved Guarantees**:
     - Retain fail-closed validation for production (`DEBUG=False`), backward-compatibility with legacy `SECRET_KEY`, and process environment precedence over `.env`.

- **Alternatives Considered**:
  - **Retain helpers in `settings.py`**: Rejected because separating imperative parsing from declarative configuration improves code maintainability, reusability, and direct testability.
  - **Adopt `django-environ`**: Rejected because Python standard library (`os`, `pathlib`) and Django's `ImproperlyConfigured` satisfy all requirements cleanly with zero additional dependencies.

- **Consequences**:
  - **Positive**:
    - `settings.py` is succinct, readable, and standard.
    - Environment helpers can be imported and tested independently without bootstrapping the entire Django settings machinery.
    - Clear separation of concerns between environment ingestion/validation and Django settings assignment.
  - **Negative / Trade-offs**:
    - Introduces an additional file (`rri_publications_dashboard/env.py`) in the core project package.

---

## Open Questions Affecting Implementation

The following institutional and operational questions directly impact future remediation steps and must be aligned with project stakeholders:

1. **Dashboard Visibility & Access Control Policy**:
   - *Question*: Are the 21 analytical dashboard views intended to be publicly accessible as an institutional research showcase, or must they be restricted to authenticated RRI staff?
   - *Implementation Impact*: Governs whether `LoginRequiredMixin` should be applied globally across `dashboard/views.py` or scoped conditionally.

2. **Production Hosting Environment & Web Server**:
   - *Question*: Will the production environment be hosted on virtual machines running Apache (`mod_wsgi`) as implied by `makefile`, or on Nginx + Gunicorn/Uvicorn, or containerized via Docker?
   - *Implementation Impact*: Governs whether to reconstruct `generate_apache_conf.py` or provide modern systemd/Docker/Gunicorn deployment assets.

3. **Production Database Engine**:
   - *Question*: Will the production deployment remain on SQLite, or will it migrate to PostgreSQL or MySQL?
   - *Implementation Impact*: Governs whether to introduce database connection pooling, PostgreSQL-specific search features, and migration scripts.

4. **Institutional Email Relay (SMTP)**:
   - *Question*: What SMTP host, port, credentials, or transactional email service will be used for password resets?
   - *Implementation Impact*: Determines how `EMAIL_BACKEND` and `.env` credentials should be structured for development vs. production.

5. **Orphaned Manual Publication Templates**:
   - *Question*: Should the manual entry forms (`create_publication.html`, `edit_publication.html`) be wired up to new Create/Edit views, or are all publications strictly required to originate from Web of Science export files?
   - *Implementation Impact*: Governs whether to implement new view classes or archive the orphaned templates.
