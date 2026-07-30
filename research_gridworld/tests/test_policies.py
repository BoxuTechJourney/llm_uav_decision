from __future__ import annotations

from dataclasses import replace

import numpy as np

from griduav.core import Cell, GridUAVModel, ScenarioConfig, UAVConfig
from griduav.policies import GreedyPolicy, RandomPolicy, SweepPolicy


def policy_observation():
    config = ScenarioConfig(
        width=5,
        height=4,
        obstacles=frozenset({Cell(1, 1)}),
        uavs=(
            UAVConfig("uav_0", Cell(0, 0)),
            UAVConfig("uav_1", Cell(0, 4)),
            UAVConfig("uav_2", Cell(3, 0)),
        ),
        target_cell=Cell(3, 4),
        sensing_radius=0,
        max_steps=20,
    )
    return GridUAVModel(config).reset(0)[1]


def test_random_policy_is_seeded_and_never_targets_obstacles() -> None:
    observation = policy_observation()
    first = RandomPolicy()
    second = RandomPolicy()
    first.reset(observation, seed=13)
    second.reset(observation, seed=13)

    first_actions = first.act(observation)
    second_actions = second.act(observation)

    assert first_actions == second_actions
    assert all(
        not observation.obstacle_map[
            action.destination.row, action.destination.col
        ]
        for action in first_actions.values()
    )


def test_sweep_policy_assigns_distinct_shared_waypoints() -> None:
    observation = policy_observation()
    policy = SweepPolicy()
    policy.reset(observation, seed=0)

    actions = policy.act(observation)

    destinations = {action.destination for action in actions.values()}
    assert len(destinations) == len(observation.uav_states)
    assert Cell(1, 1) not in destinations
    positions = {
        uav.uav_id: uav.cell for uav in observation.uav_states
    }
    assert all(
        max(
            abs(action.destination.row - positions[uav_id].row),
            abs(action.destination.col - positions[uav_id].col),
        )
        <= 1
        for uav_id, action in actions.items()
    )


def test_sweep_fallback_preserves_distinct_cells_when_goals_are_scarce() -> None:
    config = ScenarioConfig(
        width=3,
        height=2,
        obstacles=frozenset(),
        uavs=(
            UAVConfig("uav_0", Cell(0, 1)),
            UAVConfig("uav_1", Cell(1, 0)),
            UAVConfig("uav_2", Cell(1, 1)),
        ),
        target_cell=Cell(1, 2),
        sensing_radius=0,
        max_steps=5,
    )
    _, observation = GridUAVModel(config).reset(0)
    observed_mask = np.ones((2, 3), dtype=np.bool_)
    observed_mask[1, 2] = False
    observation = replace(observation, observed_mask=observed_mask)
    policy = SweepPolicy()
    policy.reset(observation, seed=0)

    actions = policy.act(observation)

    assert len({action.destination for action in actions.values()}) == 3


def test_greedy_policy_assigns_nearest_unobserved_unreserved_cells() -> None:
    observation = policy_observation()
    policy = GreedyPolicy()
    policy.reset(observation, seed=0)

    actions = policy.act(observation)

    assert actions["uav_0"].destination == Cell(0, 1)
    assert actions["uav_1"].destination == Cell(0, 3)
    assert len({action.destination for action in actions.values()}) == 3
