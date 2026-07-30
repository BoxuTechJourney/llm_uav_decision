"""Deterministic single-episode and paired-seed batch runners."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml

from griduav.core import GridUAVModel, ScenarioConfig
from griduav.policies import (
    PolicyName,
    TeamPolicy,
    create_policy,
    policy_name,
)
from griduav.replay import (
    REPLAY_MODES,
    ReplayMode,
    ReplayOutput,
    render_replay,
    replay_mode,
)
from griduav.scenario import scenario_from_dict
from griduav.trace import EpisodeTrace, TraceStep, write_trace

SUMMARY_FIELDS = (
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
)


@dataclass(frozen=True)
class EpisodeSummary:
    episode_id: str
    seed: int
    policy: PolicyName
    num_uav: int
    grid_width: int
    grid_height: int
    success: bool
    time_to_discovery: int | None
    total_distance: float
    coverage_ratio: float
    coverage_redundancy: float
    blocked_actions: int
    invalid_actions: int
    makespan: int

    def to_row(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "seed": self.seed,
            "policy": self.policy,
            "num_uav": self.num_uav,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "success": self.success,
            "time_to_discovery": self.time_to_discovery,
            "total_distance": f"{self.total_distance:.6f}",
            "coverage_ratio": f"{self.coverage_ratio:.6f}",
            "coverage_redundancy": f"{self.coverage_redundancy:.6f}",
            "blocked_actions": self.blocked_actions,
            "invalid_actions": self.invalid_actions,
            "makespan": self.makespan,
        }


@dataclass(frozen=True)
class EpisodeResult:
    summary: EpisodeSummary
    trace: EpisodeTrace
    trace_path: Path | None
    replay: ReplayOutput | None


@dataclass(frozen=True)
class EvaluationConfig:
    seeds: tuple[int, ...]
    policies: tuple[PolicyName, ...]
    output_dir: Path
    write_trace: bool = True
    write_replay: bool = False
    replay_mode: ReplayMode = "public"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "policies",
            tuple(policy_name(name) for name in self.policies),
        )
        if not self.seeds:
            raise ValueError("evaluation.seeds cannot be empty")
        if len(self.seeds) != len(set(self.seeds)):
            raise ValueError("evaluation.seeds must be unique")
        if not self.policies:
            raise ValueError("evaluation.policies cannot be empty")
        if self.replay_mode not in REPLAY_MODES:
            raise ValueError("invalid evaluation.replay_mode")


@dataclass(frozen=True)
class BatchResult:
    episodes: tuple[EpisodeResult, ...]
    summary_csv: Path


def _summary(
    config: ScenarioConfig,
    seed: int,
    policy_name: PolicyName,
    trace: EpisodeTrace,
) -> EpisodeSummary:
    final_state = (
        trace.steps[-1].transition.next_state
        if trace.steps
        else trace.initial_state
    )
    action_results = [
        result
        for step in trace.steps
        for result in step.transition.action_results
    ]
    traversable = ~final_state.obstacle_map
    observed = final_state.observed_count[traversable]
    traversable_count = int(np.count_nonzero(traversable))
    distinct_observed = int(np.count_nonzero(observed > 0))
    total_observations = int(observed.sum())
    coverage_ratio = (
        distinct_observed / traversable_count
        if traversable_count
        else 0.0
    )
    coverage_redundancy = (
        (total_observations - distinct_observed) / total_observations
        if total_observations
        else 0.0
    )
    episode_id = _episode_id(config, seed, policy_name)
    return EpisodeSummary(
        episode_id=episode_id,
        seed=seed,
        policy=policy_name,
        num_uav=len(config.uavs),
        grid_width=config.width,
        grid_height=config.height,
        success=final_state.target_detected,
        time_to_discovery=(
            final_state.step if final_state.target_detected else None
        ),
        total_distance=sum(
            result.distance_delta for result in action_results
        ),
        coverage_ratio=coverage_ratio,
        coverage_redundancy=coverage_redundancy,
        blocked_actions=sum(
            result.status == "blocked" for result in action_results
        ),
        invalid_actions=sum(
            result.status == "invalid" for result in action_results
        ),
        makespan=final_state.step,
    )


def run_episode(
    config: ScenarioConfig,
    policy: TeamPolicy,
    *,
    policy_name: PolicyName,
    seed: int,
    output_dir: str | Path | None = None,
    write_trace_file: bool = True,
    replay_mode: ReplayMode | None = None,
) -> EpisodeResult:
    model = GridUAVModel(config)
    initial_state, initial_observation = model.reset(seed)
    state, observation = initial_state, initial_observation
    policy.reset(observation, seed)
    steps: list[TraceStep] = []

    while not state.terminated and not state.truncated:
        actions = policy.act(observation)
        transition = model.step(state, actions)
        steps.append(TraceStep(actions=actions, transition=transition))
        state = transition.next_state
        observation = transition.observation

    trace = EpisodeTrace(
        config=config,
        seed=seed,
        policy=policy_name,
        initial_state=initial_state,
        initial_observation=initial_observation,
        steps=tuple(steps),
    )
    summary = _summary(config, seed, policy_name, trace)

    trace_path: Path | None = None
    replay: ReplayOutput | None = None
    if output_dir is not None:
        episode_dir = Path(output_dir)
        episode_dir.mkdir(parents=True, exist_ok=True)
        if write_trace_file or replay_mode is not None:
            trace_path = write_trace(episode_dir / "trace.jsonl", trace)
        if replay_mode is not None:
            assert trace_path is not None
            replay = render_replay(
                trace_path,
                episode_dir / f"replay_{replay_mode}",
                mode=replay_mode,
                make_gif=True,
            )
    return EpisodeResult(summary, trace, trace_path, replay)


def _episode_id(
    config: ScenarioConfig, seed: int, name: PolicyName
) -> str:
    return f"{config.env_id}_seed{seed:03d}_{name}"


def _load_batch_config(
    path: str | Path,
) -> tuple[ScenarioConfig, EvaluationConfig]:
    with Path(path).open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, Mapping):
        raise ValueError("batch config root must be a mapping")
    scenario = scenario_from_dict(data)
    evaluation = data.get("evaluation")
    if not isinstance(evaluation, Mapping):
        raise ValueError("evaluation mapping is required")
    return scenario, EvaluationConfig(
        seeds=tuple(int(seed) for seed in evaluation["seeds"]),
        policies=tuple(
            policy_name(str(name)) for name in evaluation["policies"]
        ),
        output_dir=Path(evaluation.get("output_dir", "results")),
        write_trace=bool(evaluation.get("write_trace", True)),
        write_replay=bool(evaluation.get("write_replay", False)),
        replay_mode=replay_mode(
            str(evaluation.get("replay_mode", "public"))
        ),
    )


def run_batch(
    config_path: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> BatchResult:
    scenario, evaluation = _load_batch_config(config_path)
    root = Path(output_dir) if output_dir is not None else evaluation.output_dir
    root.mkdir(parents=True, exist_ok=True)
    episodes = []
    for seed in evaluation.seeds:
        for policy_name in evaluation.policies:
            episode_id = _episode_id(scenario, seed, policy_name)
            episodes.append(
                run_episode(
                    scenario,
                    create_policy(policy_name),
                    policy_name=policy_name,
                    seed=seed,
                    output_dir=root / episode_id,
                    write_trace_file=evaluation.write_trace,
                    replay_mode=(
                        evaluation.replay_mode
                        if evaluation.write_replay
                        else None
                    ),
                )
            )

    summary_csv = root / "summary.csv"
    with summary_csv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(result.summary.to_row() for result in episodes)
    return BatchResult(tuple(episodes), summary_csv)
