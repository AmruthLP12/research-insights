# Architecture and Engineering Decision Log (DECISIONS.md)

This document records the architectural, security, and engineering decisions made during the maintenance, remediation, and modernization of the RRI Publications Dashboard (*Research Insights*).

---

## Decision Record Index

| ID | Title | Date | Status |
| :--- | :--- | :--- | :--- |
| **[D-001](#d-001-incremental-remediation-workflow)** | Incremental Remediation Workflow and Evidence-Based Verification | 2026-10-24 | **Accepted** |

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
