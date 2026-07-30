from __future__ import annotations

from dataclasses import fields, replace

import numpy as np
import pytest

from griduav.core import (
    Cell,
    GridUAVModel,
    MoveAction,
    ScenarioConfig,
    UAVConfig,
    UAVState,
    WorldState,
)


def make_config(
    *,
    width: int = 5,
    height: int = 5,
    starts: tuple[Cell, ...] = (Cell(0, 0),),
    obstacles: frozenset[Cell] = frozenset(),
    target: Cell = Cell(4, 4),
    radius: int = 1,
    max_steps: int = 10,
) -> ScenarioConfig:
    return ScenarioConfig(
        width=width,
        height=height,
        obstacles=obstacles,
        uavs=tuple(
            UAVConfig(f"uav_{index}", cell)
            for index, cell in enumerate(starts)
        ),
        target_cell=target,
        sensing_radius=radius,
        max_steps=max_steps,
    )


def test_observation_hides_target_and_arrays_are_read_only() -> None:
    model = GridUAVModel(make_config())
    state, observation = model.reset(0)

    assert "target_cell" not in {item.name for item in fields(observation)}
    assert all(
        "target" not in item.name for item in fields(type(observation))
    )
    assert state.target_cell == Cell(4, 4)
    with pytest.raises(ValueError):
        observation.observed_mask[0, 0] = False
    with pytest.raises(ValueError):
        state.observed_count[0, 0] = 99


def test_public_types_copy_mutable_inputs_and_freeze_nested_info() -> None:
    obstacle_map = np.zeros((2, 2), dtype=np.bool_)
    observed_count = np.zeros((2, 2), dtype=np.int32)
    state = WorldState(
        obstacle_map=obstacle_map,
        target_cell=Cell(1, 1),
        uav_states=[UAVState("uav_0", Cell(0, 0))],  # type: ignore[arg-type]
        observed_count=observed_count,
        target_detected=False,
        step=0,
        terminated=False,
        truncated=False,
    )
    obstacle_map[0, 0] = True
    observed_count[0, 0] = 7

    assert state.obstacle_map[0, 0] == np.False_
    assert state.observed_count[0, 0] == 0
    assert state.obstacle_map.flags.writeable is False
    assert state.observed_count.flags.writeable is False

    model = GridUAVModel(make_config(radius=0))
    initial, _ = model.reset(0)
    transition = model.step(
        initial, {"uav_0": MoveAction(Cell(0, 1))}
    )
    mutable_info = {"nested": ["value"]}
    frozen_transition = replace(transition, info=mutable_info)
    mutable_info["nested"].append("changed")

    assert frozen_transition.info["nested"] == ("value",)
    with pytest.raises(TypeError):
        frozen_transition.info["new"] = "value"  # type: ignore[index]


def test_sensor_radius_clips_at_grid_edge() -> None:
    model = GridUAVModel(make_config(radius=1))

    state, observation = model.reset(0)

    assert observation.latest_sensor_results[0].visible_cells == (
        Cell(0, 0),
        Cell(0, 1),
        Cell(1, 0),
        Cell(1, 1),
    )
    assert int(state.observed_count.sum()) == 4


def test_detection_terminates_when_target_becomes_visible() -> None:
    model = GridUAVModel(
        make_config(width=4, height=3, target=Cell(0, 2), radius=0)
    )
    state, _ = model.reset(0)

    first = model.step(state, {"uav_0": MoveAction(Cell(0, 2))})
    second = model.step(
        first.next_state, {"uav_0": MoveAction(Cell(0, 2))}
    )

    assert first.terminated is False
    assert second.terminated is True
    assert second.success is True
    assert second.observation.latest_sensor_results[0].detected is True


def test_overlapping_sensors_increment_observed_count_per_uav() -> None:
    model = GridUAVModel(
        make_config(
            starts=(Cell(1, 0), Cell(1, 2)),
            target=Cell(4, 4),
            radius=1,
        )
    )

    state, _ = model.reset(0)

    assert state.observed_count[1, 1] == 2
    assert np.all(state.observed_count >= 0)

    transition = model.step(
        state,
        {
            "uav_0": MoveAction(Cell(1, 0)),
            "uav_1": MoveAction(Cell(1, 2)),
        },
    )
    assert np.all(transition.next_state.observed_count >= state.observed_count)


def test_no_corner_cutting_chooses_cardinal_segment() -> None:
    model = GridUAVModel(
        make_config(
            width=3,
            height=3,
            obstacles=frozenset({Cell(0, 1)}),
            target=Cell(2, 0),
            radius=0,
        )
    )
    state, _ = model.reset(0)

    transition = model.step(
        state, {"uav_0": MoveAction(Cell(1, 1))}
    )

    assert transition.next_state.uav_states[0].cell == Cell(1, 0)
    assert transition.action_results[0].distance_delta == 1.0


def test_unreachable_destination_is_blocked() -> None:
    obstacles = frozenset(
        {
            Cell(0, 1),
            Cell(1, 0),
            Cell(1, 2),
            Cell(2, 1),
        }
    )
    model = GridUAVModel(
        make_config(
            width=3,
            height=3,
            starts=(Cell(1, 1),),
            obstacles=obstacles,
            target=Cell(0, 0),
            radius=0,
        )
    )
    state, _ = model.reset(0)

    transition = model.step(
        state, {"uav_0": MoveAction(Cell(0, 0))}
    )

    result = transition.action_results[0]
    assert (result.status, result.reason) == ("blocked", "unreachable")
    assert result.next_cell == Cell(1, 1)


def test_following_chain_into_vacated_cell_is_allowed() -> None:
    model = GridUAVModel(
        make_config(
            width=5,
            height=3,
            starts=(Cell(1, 0), Cell(1, 1)),
            target=Cell(2, 4),
            radius=0,
        )
    )
    state, _ = model.reset(0)

    transition = model.step(
        state,
        {
            "uav_0": MoveAction(Cell(1, 1)),
            "uav_1": MoveAction(Cell(1, 2)),
        },
    )

    assert tuple(uav.cell for uav in transition.next_state.uav_states) == (
        Cell(1, 1),
        Cell(1, 2),
    )
    assert all(
        result.status == "moved"
        for result in transition.action_results
    )


def test_blocking_propagates_back_through_following_chain() -> None:
    model = GridUAVModel(
        make_config(
            width=5,
            height=3,
            starts=(Cell(1, 0), Cell(1, 1), Cell(1, 2)),
            target=Cell(2, 4),
            radius=0,
        )
    )
    state, _ = model.reset(0)

    transition = model.step(
        state,
        {
            "uav_0": MoveAction(Cell(1, 1)),
            "uav_1": MoveAction(Cell(1, 2)),
            "uav_2": MoveAction(Cell(1, 2)),
        },
    )

    assert tuple(uav.cell for uav in transition.next_state.uav_states) == (
        Cell(1, 0),
        Cell(1, 1),
        Cell(1, 2),
    )
    assert tuple(item.reason for item in transition.action_results) == (
        "occupied",
        "same_destination",
        "none",
    )


def test_longer_occupancy_cycle_is_blocked() -> None:
    model = GridUAVModel(
        make_config(
            width=4,
            height=4,
            starts=(Cell(0, 0), Cell(0, 1), Cell(1, 1)),
            target=Cell(3, 3),
            radius=0,
        )
    )
    state, _ = model.reset(0)

    transition = model.step(
        state,
        {
            "uav_0": MoveAction(Cell(0, 1)),
            "uav_1": MoveAction(Cell(1, 1)),
            "uav_2": MoveAction(Cell(0, 0)),
        },
    )

    assert tuple(uav.cell for uav in transition.next_state.uav_states) == (
        Cell(0, 0),
        Cell(0, 1),
        Cell(1, 1),
    )
    assert {item.reason for item in transition.action_results} == {"cycle"}


def test_max_steps_truncates_and_completed_state_cannot_step() -> None:
    model = GridUAVModel(
        make_config(target=Cell(4, 4), radius=0, max_steps=1)
    )
    state, _ = model.reset(0)

    transition = model.step(
        state, {"uav_0": MoveAction(Cell(0, 1))}
    )

    assert transition.terminated is False
    assert transition.truncated is True
    with pytest.raises(RuntimeError):
        model.step(
            transition.next_state, {"uav_0": MoveAction(Cell(0, 2))}
        )


def test_detection_wins_over_max_step_truncation() -> None:
    model = GridUAVModel(
        make_config(
            width=3,
            height=3,
            target=Cell(0, 1),
            radius=0,
            max_steps=1,
        )
    )
    state, _ = model.reset(0)

    transition = model.step(
        state, {"uav_0": MoveAction(Cell(0, 1))}
    )

    assert transition.terminated is True
    assert transition.truncated is False


def test_fixed_target_can_be_detected_at_reset() -> None:
    model = GridUAVModel(
        make_config(target=Cell(0, 0), radius=0, max_steps=2)
    )

    state, observation = model.reset(0)

    assert state.step == 0
    assert state.terminated is True
    assert state.target_detected is True
    assert observation.latest_sensor_results[0].detected is True


def test_missing_and_unknown_actions_are_reported_without_crashing() -> None:
    model = GridUAVModel(make_config(radius=0))
    state, _ = model.reset(0)

    transition = model.step(
        state, {"unknown": MoveAction(Cell(1, 1))}
    )

    result = transition.action_results[0]
    assert (result.status, result.reason) == ("invalid", "missing_action")
    assert transition.info["unknown_action_ids"] == ("unknown",)


def test_random_target_is_not_initially_visible() -> None:
    config = ScenarioConfig(
        width=6,
        height=6,
        obstacles=frozenset(),
        uavs=(UAVConfig("uav_0", Cell(0, 0)),),
        sensing_radius=1,
        max_steps=10,
    )

    state, _ = GridUAVModel(config).reset(9)

    assert max(state.target_cell.row, state.target_cell.col) > 1
