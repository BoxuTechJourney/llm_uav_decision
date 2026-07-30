# T3 — PettingZoo + Evaluation

## Dependency

T1 and T2 are green.

## Deliverables

- PettingZoo `ParallelEnv` adapter and Gymnasium spaces.
- Team random, sweep, and greedy policies.
- Single-episode and paired-seed batch runners.
- Summary CSV and CLI entry modules.

## Red/green slices

1. Adapter reset, spaces, step, rewards, and terminal lifecycle.
2. Official Parallel API and seed tests.
3. Random, sweep, and greedy one-/three-UAV smoke runs.
4. Episode metrics, paired seeds, deterministic row order, and CSV output.
5. Batch and replay CLI smoke tests.

## Acceptance

All policies use only `AgentObservation`; different policies receive identical
initial states for a paired seed; all documented commands run from the project
environment.

## Not in scope

RL training, centralized Gym wrappers, additional policies, or result plots.
