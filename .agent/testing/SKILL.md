# Testing Skill

Use this skill when writing or updating tests for Clash Command.

## Test layers

-   **Unit:** time arithmetic, reminder schedule calculation, lifecycle
    transitions, validation, capacity rules, stable notification IDs.
-   **Database:** repository/DAO behavior, active-upgrade queries,
    relationships, migrations, catalog seeding.
-   **Widget:** village switcher, dashboard empty/active states, forms,
    validation and permission-denied states.
-   **Integration/device:** schedule, edit, cancel, reboot
    reconciliation, app restart, denied permissions,
    time-zone/system-clock changes.

## Rules

-   Inject or wrap the current clock for deterministic tests.
-   Avoid tests that rely on real waiting or actual wall-clock timing.
-   Test past-due upgrades and reminders whose pre-alert time has
    passed.
-   Test failure paths as well as happy paths.
-   Test migration from every supported prior schema version.
-   Run `flutter test` and `flutter analyze`; use device tests for
    Android-specific notification behavior.
-   Do not claim a device notification test passed if only unit tests
    were run.
