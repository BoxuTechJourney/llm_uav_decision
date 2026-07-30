from __future__ import annotations

import numpy as np

from griduav.core import (
    Cell,
    GridUAVModel,
    MoveAction,
    ScenarioConfig,
    UAVConfig,
)


def test_seed_reproducibility() -> None:
    config = ScenarioConfig(
        width=6,
        height=5,
        obstacles=frozenset({Cell(1, 1), Cell(2, 3)}),
        uavs=(UAVConfig("uav_0", Cell(0, 0)),),
        sensing_radius=1,
        max_steps=20,
    )
    model = GridUAVModel(config)

    state_a, observation_a = model.reset(17)
    state_b, observation_b = model.reset(17)

    assert state_a.target_cell == state_b.target_cell
    assert state_a.uav_states == state_b.uav_states
    assert np.array_equal(state_a.obstacle_map, state_b.obstacle_map)
    assert np.array_equal(state_a.observed_count, state_b.observed_count)
    assert np.array_equal(observation_a.observed_mask, observation_b.observed_mask)


def test_step_advances_one_deterministic_segment() -> None:
    config = ScenarioConfig(
        width=5,
        height=5,
        obstacles=frozenset(),
        uavs=(UAVConfig("uav_0", Cell(0, 0)),),
        target_cell=Cell(4, 0),
        sensing_radius=0,
        max_steps=10,
    )
    model = GridUAVModel(config)
    state, _ = model.reset(1)

    transition = model.step(
        state, {"uav_0": MoveAction(destination=Cell(3, 3))}
    )

    assert transition.next_state.uav_states[0].cell == Cell(1, 1)
    assert transition.action_results[0].status == "moved"
    assert transition.action_results[0].distance_delta == np.sqrt(2.0)


def test_same_destination_conflict_has_deterministic_winner() -> None:
    config = ScenarioConfig(
        width=4,
        height=4,
        obstacles=frozenset(),
        uavs=(
            UAVConfig("uav_0", Cell(1, 0)),
            UAVConfig("uav_1", Cell(1, 2)),
        ),
        target_cell=Cell(3, 3),
        sensing_radius=0,
        max_steps=10,
    )
    model = GridUAVModel(config)
    state, _ = model.reset(0)

    transition = model.step(
        state,
        {
            "uav_0": MoveAction(Cell(1, 1)),
            "uav_1": MoveAction(Cell(1, 1)),
        },
    )

    assert tuple(uav.cell for uav in transition.next_state.uav_states) == (
        Cell(1, 1),
        Cell(1, 2),
    )
    assert tuple(
        (result.status, result.reason)
        for result in transition.action_results
    ) == (("moved", "none"), ("blocked", "same_destination"))


def test_swap_conflict_blocks_both_uavs() -> None:
    config = ScenarioConfig(
        width=4,
        height=4,
        obstacles=frozenset(),
        uavs=(
            UAVConfig("uav_0", Cell(1, 1)),
            UAVConfig("uav_1", Cell(1, 2)),
        ),
        target_cell=Cell(3, 3),
        sensing_radius=0,
        max_steps=10,
    )
    model = GridUAVModel(config)
    state, _ = model.reset(0)

    transition = model.step(
        state,
        {
            "uav_0": MoveAction(Cell(1, 2)),
            "uav_1": MoveAction(Cell(1, 1)),
        },
    )

    assert tuple(uav.cell for uav in transition.next_state.uav_states) == (
        Cell(1, 1),
        Cell(1, 2),
    )
    assert {result.reason for result in transition.action_results} == {
        "cycle"
    }
