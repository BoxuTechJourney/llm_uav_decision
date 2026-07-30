from __future__ import annotations

import csv
from pathlib import Path

from griduav.core import (
    AgentObservation,
    Cell,
    MoveAction,
    ScenarioConfig,
    UAVConfig,
)
from griduav.evaluation import run_batch, run_episode
from griduav.policies import GreedyPolicy, RandomPolicy, SweepPolicy


class StayPolicy:
    def reset(self, observation: AgentObservation, seed: int) -> None:
        del observation, seed

    def act(
        self, observation: AgentObservation
    ) -> dict[str, MoveAction]:
        return {
            uav.uav_id: MoveAction(uav.cell)
            for uav in observation.uav_states
        }


def test_all_baselines_complete_one_and_three_uav_smoke_runs() -> None:
    policies = [
        ("random", RandomPolicy),
        ("sweep", SweepPolicy),
        ("greedy", GreedyPolicy),
    ]
    for num_uav in (1, 3):
        config = ScenarioConfig(
            width=6,
            height=5,
            obstacles=frozenset({Cell(2, 2)}),
            uavs=tuple(
                UAVConfig(f"uav_{index}", Cell(0, index * 2))
                for index in range(num_uav)
            ),
            target_cell=Cell(4, 5),
            sensing_radius=1,
            max_steps=30,
        )
        for name, factory in policies:
            result = run_episode(
                config,
                factory(),
                policy_name=name,
                seed=4,
            )
            assert result.summary.policy == name
            assert result.summary.num_uav == num_uav
            assert result.summary.makespan <= 30
            assert (
                result.trace.steps[-1].transition.terminated
                or result.trace.steps[-1].transition.truncated
            )


def test_batch_uses_paired_seeds_and_writes_ordered_summary_csv(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "batch.yaml"
    config_path.write_text(
        f"""
env:
  id: BatchTest-v0
  max_steps: 8
grid:
  width: 6
  height: 5
  obstacles: [[2, 2]]
uavs:
  - id: uav_0
    start: [0, 0]
target:
  placement: random_reachable
sensing:
  radius_cells: 1
evaluation:
  seeds: [2, 5]
  policies: [random, sweep]
  output_dir: "{(tmp_path / "results").as_posix()}"
  write_trace: true
  write_replay: false
""".strip(),
        encoding="utf-8",
    )

    result = run_batch(config_path)

    assert [
        (item.summary.seed, item.summary.policy)
        for item in result.episodes
    ] == [(2, "random"), (2, "sweep"), (5, "random"), (5, "sweep")]
    for offset in (0, 2):
        assert (
            result.episodes[offset].trace.initial_state.target_cell
            == result.episodes[offset + 1].trace.initial_state.target_cell
        )
    with result.summary_csv.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert [(int(row["seed"]), row["policy"]) for row in rows] == [
        (2, "random"),
        (2, "sweep"),
        (5, "random"),
        (5, "sweep"),
    ]
    assert rows[0].keys() == {
        "episode_id",
        "seed",
        "policy",
        "num_uav",
        "grid_width",
        "grid_height",
        "success",
        "time_to_discovery",
        "total_distance",
        "coverage_ratio",
        "coverage_redundancy",
        "blocked_actions",
        "invalid_actions",
        "makespan",
    }
    assert list((tmp_path / "results").glob("*/summary.json")) == []


def test_episode_metrics_have_literal_coverage_and_failure_values() -> None:
    config = ScenarioConfig(
        width=2,
        height=2,
        obstacles=frozenset(),
        uavs=(UAVConfig("uav_0", Cell(0, 0)),),
        target_cell=Cell(1, 1),
        sensing_radius=0,
        max_steps=1,
    )

    result = run_episode(
        config,
        StayPolicy(),
        policy_name="sweep",
        seed=0,
    )

    assert result.summary.success is False
    assert result.summary.time_to_discovery is None
    assert result.summary.coverage_ratio == 0.25
    assert result.summary.coverage_redundancy == 0.5
    assert result.summary.total_distance == 0.0
    assert result.summary.to_row()["time_to_discovery"] is None
