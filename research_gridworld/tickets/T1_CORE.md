# T1 — GridUAV Core

## Dependency

`PLATFORM_SPEC.md` is frozen.

## Deliverables

- Python project metadata and scenario configuration loader.
- Immutable core schemas.
- `GridUAVModel.reset(seed)` and deterministic `step(state, actions)`.
- Static obstacles, shortest-path movement, simultaneous conflicts, sensing,
  detection, termination, and truncation.

## Red/green slices

1. Seeded reset and target placement.
2. Public observation information isolation.
3. Deterministic movement, obstacles, bounds, and unreachable goals.
4. Sensor radius, detection, and monotonic observation counts.
5. Equal-destination contention, following, swaps, cycles, and propagation.
6. Termination and truncation.

## Acceptance

All core behavior is exercised through `GridUAVModel`; tests do not call
private pathfinding, sensing, or collision helpers.

## Not in scope

Trace files, rendering, PettingZoo, policies, evaluation, or random obstacles.
