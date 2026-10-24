# Android Local Notifications Skill

Use this skill for notification permissions, scheduling, cancellation,
reboot recovery, and reminder preferences.

## Required process

1.  Verify current stable plugin documentation and Android setup
    requirements before changing platform configuration.
2.  Keep plugin calls behind an app-owned notification service
    interface.
3.  Derive reminder timestamps from each upgrade's absolute expected
    completion time.
4.  Use stable IDs for each upgrade/reminder pair.
5.  Persist upgrade changes before reconciling notification state;
    repair partial failures during the next reconciliation.
6.  Reconcile active upgrades on app launch and after reboot where
    supported.
7.  Skip reminders whose scheduled time is already in the past.
8.  Do not block timer tracking when permission is denied.

## Android behavior

-   Request permission contextually and explain why it is needed.
-   Confirm current Android notification permission requirements and any
    exact-alarm policy before implementation.
-   Prefer inexact alarms unless exact timing is demonstrably needed.
-   Test on a physical device and consider manufacturer-specific battery
    optimization.
-   Never promise that a notification will arrive at the exact second.
-   Do not create a persistent background service merely to update
    countdown text; derive countdowns from stored timestamps.
