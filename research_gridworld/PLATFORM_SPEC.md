# GridUAV v0 Platform Specification

This document is the implementation authority for GridUAV v0. The earlier
research and architecture documents are background only.

## 1. Frozen scope

GridUAV v0 provides a two-dimensional static-obstacle grid, one or more UAVs,
one hidden target, deterministic local sensing, JSONL traces, offline PNG/GIF
replay, random/sweep/greedy baselines, a PettingZoo `ParallelEnv` adapter, and
paired-seed batch evaluation.

Bayesian belief, EIG, LLM integration, semantic maps, Scout-Responder roles,
multiple targets, noisy sensing, dynamic obstacles, live UI, Pygame, and random
obstacle generation are out of scope.

Coordinates are always `(row, col)`, with `(0, 0)` at the top left.

## 2. Core interface and schemas

```python
model = GridUAVModel(config)
state, observation = model.reset(seed)
transition = model.step(state, actions)
```

`GridUAVModel` is a pure in-process module. `step` is deterministic, does not
write files, does not call a policy, and does not own mutable episode state.

The public core types are immutable dataclasses:

- `Cell(row, col)`.
- `UAVState(uav_id, cell)`.
- `WorldState(obstacle_map, target_cell, uav_states, observed_count,
  target_detected, step, terminated, truncated)`.
- `SensorResult(uav_id, visible_cells, newly_observed_cells, detected)`.
- `AgentObservation(obstacle_map, observed_mask, uav_states,
  latest_sensor_results, step)`.
- `MoveAction(destination)`.
- `ActionResult(uav_id, requested_destination, previous_cell, next_cell,
  status, reason, distance_delta)`.
- `Transition(previous_state, next_state, observation, action_results,
  sensor_results, terminated, truncated, success, info)`.

NumPy arrays exposed by core types are read-only. `AgentObservation` never
contains `target_cell` or a `WorldState`.

`ScenarioConfig` contains `env_id`, grid dimensions, explicit obstacle cells,
fixed UAV ids and start cells, one optional fixed target cell, sensing radius,
and `max_steps`. An omitted target means seeded random placement. Configuration
validation rejects invalid dimensions, duplicate ids/starts, out-of-bounds or
overlapping starts/obstacles, invalid targets, negative radii, and non-positive
step limits.

## 3. Reset and step semantics

Random targets are sampled uniformly from sorted traversable cells that are
reachable from at least one UAV and outside the union of initial sensing
footprints. Fixed targets may be initially visible, in which case reset returns
a successful terminal state at step 0.

Each UAV senses after reset and after every step. Visibility is the in-bounds
Chebyshev ball of the configured radius; obstacles do not occlude sensing.
Every UAV increments `observed_count` for every visible cell, including overlap.
Detection occurs when any visibility footprint contains the target.

An action names any destination cell. A step advances at most one grid segment
along a deterministic shortest path:

- 8-neighbour movement;
- cardinal cost `1`, diagonal cost `sqrt(2)`;
- no diagonal corner cutting;
- deterministic `(row, col)` tie breaking.

Missing actions stay in place with `invalid/missing_action`. Unknown UAV ids are
ignored and listed in `Transition.info["unknown_action_ids"]`. Out-of-bounds,
obstacle, and unreachable destinations produce stable status/reason values.

Movement proposals are resolved simultaneously. A stationary occupant keeps
its cell. Otherwise equal-destination contention is won by lexicographically
smallest UAV id. Acyclic following into cells vacated in the same step is
allowed. Swaps and longer closed occupancy cycles are blocked. Blocking
propagates backward through following chains.

Detection sets `terminated=True` and `success=True`. Reaching `max_steps`
without detection sets `truncated=True`. Detection wins if both conditions
occur on the same step. Calling `step` on a terminal/truncated state raises
`RuntimeError`.

## 4. Policies and PettingZoo adapter

A `TeamPolicy` receives the shared `AgentObservation` and returns one action
mapping for all UAVs. Policies own their RNG and cannot receive `WorldState`.

- Random samples traversable destinations independently per UAV.
- Sweep assigns distinct next cells from a shared row-wise lawn-mower sequence.
- Greedy assigns nearest unobserved, unreserved cells in UAV-id order using the
  same path metric and tie rule as core.

`GridUAVParallelEnv` uses `MultiDiscrete([height, width])` actions. Every agent
receives the same Gymnasium `Dict` observation containing the obstacle mask,
observed mask, all UAV positions, per-UAV latest detections, and step. Terminal
results are returned for the agents active before the step, then `agents`
becomes empty.

On a success step every active agent receives `+1.0`. Otherwise an agent whose
action result is `moved` receives `-0.01`, and all other agents receive `0.0`.
Rewards are compatibility output and are not research metrics.

## 5. Trace and replay

`trace.jsonl` schema version 1 is self-contained:

1. One `header` record with schema version, seed, policy, serialized scenario,
   initial private state, and initial public observation.
2. One `step` record per transition containing actions, action results, sensor
   results, complete next state, public observation, and terminal flags.

Replay consumes the trace only and never calls core. For `T` transitions it
generates `replay_step_000.png` for the initial state plus `T` transition
frames, followed by a GIF in the same order.

- `public`: never draw target truth; public detection status may be shown.
- `debug`: always draw target truth.
- `paper`: draw target truth only from the first detected state onward.

The trace contains private truth and must not be distributed as a public
artifact.

## 6. Evaluation and acceptance

Batch evaluation runs every configured policy on the same ordered seed list.
CSV rows are ordered by seed and then configured policy order. Fields are:
`episode_id`, `seed`, `policy`, `num_uav`, `grid_width`, `grid_height`,
`success`, `time_to_discovery`, `total_distance`, `coverage_ratio`,
`coverage_redundancy`, `blocked_actions`, `invalid_actions`, and `makespan`.
Failed discovery leaves `time_to_discovery` empty.

Coverage counts traversable cells only. Redundancy is
`(total traversable observations - distinct observed traversable cells) /
total traversable observations`, or zero when there are no observations.

Acceptance requires all pytest tests, PettingZoo `parallel_api_test` and
`parallel_seed_test`, one- and three-UAV policy smoke runs, batch CLI output,
offline replay output, and final code review to pass.
