# Offline Data and Drift Skill

Use this skill for database schema, queries, persistence, migrations,
and backup/restore.

## Rules

-   SQLite/Drift is the source of truth for all village and upgrade
    data.
-   Read `architecture.md` before changing schema.
-   Use typed Drift tables/queries and repository/DAO boundaries.
-   Keep foreign keys and delete behavior explicit.
-   Store absolute timestamps consistently in UTC.
-   Never persist a ticking countdown as the source of truth.
-   Add indexes for common active-upgrade and expected-completion
    queries.
-   Schema changes require an explicit version bump and migration.
-   Test migrations and important query behavior.
-   Seed bundled catalog data idempotently; never overwrite user data
    during a catalog refresh.
-   Backup import must validate data before applying it and must not
    destroy current data on failure.

## Safety

Do not add cloud sync, remote analytics, or a backend as a shortcut. Any
future sync proposal requires an explicit product-scope decision.
