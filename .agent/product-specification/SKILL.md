# Product Specification Skill

Use this skill when planning or changing product behavior in Clash
Command.

## Required process

1.  Read `prod.md` and `essential-architecture.md`.
2.  Identify the affected user story and acceptance criteria.
3.  Separate MVP requirements from later enhancements.
4.  State any new behavior, data, permissions, or platform assumptions
    before implementation.
5.  Keep offline use and local ownership as defaults.

## Product rules

-   The app tracks timers; it does not read the live game state.
-   Always allow custom upgrade names and durations.
-   Never invent in-game durations or imply automatic synchronization.
-   Avoid features that require a backend unless the product scope is
    explicitly revised.
-   A permission denial must not prevent the user from tracking
    upgrades.

## Definition of done

A feature is done only when its acceptance criteria, empty/error states,
and relevant tests are addressed. Update the product specification when
a deliberate scope change is approved.
