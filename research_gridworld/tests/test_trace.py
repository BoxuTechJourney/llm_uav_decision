from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from griduav.core import (
    Cell,
    GridUAVModel,
    MoveAction,
    ScenarioConfig,
    UAVConfig,
)
from griduav.trace import EpisodeTrace, TraceStep, read_trace, write_trace


def test_trace_roundtrip_preserves_initial_and_transition_state(
    tmp_path: Path,
) -> None:
    config = ScenarioConfig(
        width=4,
        height=4,
        obstacles=frozenset({Cell(2, 2)}),
        uavs=(UAVConfig("uav_0", Cell(0, 0)),),
        target_cell=Cell(3, 3),
        sensing_radius=0,
        max_steps=10,
    )
    model = GridUAVModel(config)
    state, observation = model.reset(3)
    actions = {"uav_0": MoveAction(Cell(3, 0))}
    transition = model.step(state, actions)
    expected = EpisodeTrace(
        config=config,
        seed=3,
        policy="sweep",
        initial_state=state,
        initial_observation=observation,
        steps=(TraceStep(actions=actions, transition=transition),),
    )
    path = tmp_path / "trace.jsonl"

    write_trace(path, expected)
    actual = read_trace(path)

    assert actual.config == expected.config
    assert (actual.seed, actual.policy) == (3, "sweep")
    assert actual.initial_state.target_cell == Cell(3, 3)
    assert np.array_equal(
        actual.initial_state.observed_count, state.observed_count
    )
    assert actual.steps[0].actions == actions
    assert (
        actual.steps[0].transition.next_state.uav_states
        == transition.next_state.uav_states
    )
    assert np.array_equal(
        actual.steps[0].transition.observation.observed_mask,
        transition.observation.observed_mask,
    )

    records = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert [record["record_type"] for record in records] == [
        "header",
        "step",
    ]
    assert records[0]["schema_version"] == 1
    assert records[1]["next_state"]["target_cell"] == [3, 3]
