"""Versioned JSONL trace serialization."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence, cast

import numpy as np

from griduav.core import (
    ActionResult,
    AgentObservation,
    Cell,
    MoveAction,
    ScenarioConfig,
    SensorResult,
    Transition,
    UAVState,
    WorldState,
)
from griduav.core.types import ActionReason, ActionStatus, readonly_array
from griduav.policies import PolicyName, policy_name
from griduav.scenario import scenario_from_dict, scenario_to_dict

TRACE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class TraceStep:
    actions: Mapping[str, MoveAction]
    transition: Transition


@dataclass(frozen=True)
class EpisodeTrace:
    config: ScenarioConfig
    seed: int
    policy: PolicyName
    initial_state: WorldState
    initial_observation: AgentObservation
    steps: tuple[TraceStep, ...]


def _cell_to_data(cell: Cell) -> list[int]:
    return [cell.row, cell.col]


def _cell_from_data(value: Sequence[int]) -> Cell:
    return Cell(int(value[0]), int(value[1]))


def _uav_to_data(uav: UAVState) -> dict[str, Any]:
    return {"uav_id": uav.uav_id, "cell": _cell_to_data(uav.cell)}


def _uav_from_data(data: Mapping[str, Any]) -> UAVState:
    return UAVState(
        uav_id=str(data["uav_id"]), cell=_cell_from_data(data["cell"])
    )


def _sensor_to_data(sensor: SensorResult) -> dict[str, Any]:
    return {
        "uav_id": sensor.uav_id,
        "visible_cells": [
            _cell_to_data(cell) for cell in sensor.visible_cells
        ],
        "newly_observed_cells": [
            _cell_to_data(cell) for cell in sensor.newly_observed_cells
        ],
        "detected": sensor.detected,
    }


def _sensor_from_data(data: Mapping[str, Any]) -> SensorResult:
    return SensorResult(
        uav_id=str(data["uav_id"]),
        visible_cells=tuple(
            _cell_from_data(cell) for cell in data["visible_cells"]
        ),
        newly_observed_cells=tuple(
            _cell_from_data(cell)
            for cell in data["newly_observed_cells"]
        ),
        detected=bool(data["detected"]),
    )


def state_to_dict(state: WorldState) -> dict[str, Any]:
    return {
        "obstacle_map": state.obstacle_map.astype(int).tolist(),
        "target_cell": _cell_to_data(state.target_cell),
        "uav_states": [_uav_to_data(uav) for uav in state.uav_states],
        "observed_count": state.observed_count.tolist(),
        "target_detected": state.target_detected,
        "step": state.step,
        "terminated": state.terminated,
        "truncated": state.truncated,
    }


def state_from_dict(data: Mapping[str, Any]) -> WorldState:
    return WorldState(
        obstacle_map=readonly_array(data["obstacle_map"], np.bool_),
        target_cell=_cell_from_data(data["target_cell"]),
        uav_states=tuple(
            _uav_from_data(item) for item in data["uav_states"]
        ),
        observed_count=readonly_array(data["observed_count"], np.int32),
        target_detected=bool(data["target_detected"]),
        step=int(data["step"]),
        terminated=bool(data["terminated"]),
        truncated=bool(data["truncated"]),
    )


def observation_to_dict(observation: AgentObservation) -> dict[str, Any]:
    return {
        "obstacle_map": observation.obstacle_map.astype(int).tolist(),
        "observed_mask": observation.observed_mask.astype(int).tolist(),
        "uav_states": [
            _uav_to_data(uav) for uav in observation.uav_states
        ],
        "latest_sensor_results": [
            _sensor_to_data(item)
            for item in observation.latest_sensor_results
        ],
        "step": observation.step,
    }


def observation_from_dict(data: Mapping[str, Any]) -> AgentObservation:
    return AgentObservation(
        obstacle_map=readonly_array(data["obstacle_map"], np.bool_),
        observed_mask=readonly_array(data["observed_mask"], np.bool_),
        uav_states=tuple(
            _uav_from_data(item) for item in data["uav_states"]
        ),
        latest_sensor_results=tuple(
            _sensor_from_data(item)
            for item in data["latest_sensor_results"]
        ),
        step=int(data["step"]),
    )


def _action_result_to_data(result: ActionResult) -> dict[str, Any]:
    return {
        "uav_id": result.uav_id,
        "requested_destination": (
            None
            if result.requested_destination is None
            else _cell_to_data(result.requested_destination)
        ),
        "previous_cell": _cell_to_data(result.previous_cell),
        "next_cell": _cell_to_data(result.next_cell),
        "status": result.status,
        "reason": result.reason,
        "distance_delta": result.distance_delta,
    }


def _action_result_from_data(data: Mapping[str, Any]) -> ActionResult:
    destination = data["requested_destination"]
    return ActionResult(
        uav_id=str(data["uav_id"]),
        requested_destination=(
            None if destination is None else _cell_from_data(destination)
        ),
        previous_cell=_cell_from_data(data["previous_cell"]),
        next_cell=_cell_from_data(data["next_cell"]),
        status=cast(ActionStatus, str(data["status"])),
        reason=cast(ActionReason, str(data["reason"])),
        distance_delta=float(data["distance_delta"]),
    )


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _header_record(trace: EpisodeTrace) -> dict[str, Any]:
    return {
        "record_type": "header",
        "schema_version": TRACE_SCHEMA_VERSION,
        "seed": trace.seed,
        "policy": trace.policy,
        "scenario": scenario_to_dict(trace.config),
        "initial_state": state_to_dict(trace.initial_state),
        "initial_observation": observation_to_dict(
            trace.initial_observation
        ),
    }


def _step_record(step: TraceStep) -> dict[str, Any]:
    transition = step.transition
    return {
        "record_type": "step",
        "step": transition.next_state.step,
        "actions": {
            uav_id: _cell_to_data(action.destination)
            for uav_id, action in sorted(step.actions.items())
        },
        "action_results": [
            _action_result_to_data(item)
            for item in transition.action_results
        ],
        "sensor_results": [
            _sensor_to_data(item) for item in transition.sensor_results
        ],
        "next_state": state_to_dict(transition.next_state),
        "observation": observation_to_dict(transition.observation),
        "terminated": transition.terminated,
        "truncated": transition.truncated,
        "success": transition.success,
        "info": _jsonable(transition.info),
    }


def write_trace(path: str | Path, trace: EpisodeTrace) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    records = [_header_record(trace), *map(_step_record, trace.steps)]
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(
                json.dumps(
                    record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                )
            )
            stream.write("\n")
    return output


def read_trace(path: str | Path) -> EpisodeTrace:
    source = Path(path)
    with source.open("r", encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    if not records or records[0].get("record_type") != "header":
        raise ValueError("trace must start with a header record")
    header = records[0]
    if header.get("schema_version") != TRACE_SCHEMA_VERSION:
        raise ValueError("unsupported trace schema version")

    config = scenario_from_dict(header["scenario"])
    initial_state = state_from_dict(header["initial_state"])
    initial_observation = observation_from_dict(
        header["initial_observation"]
    )
    previous_state = initial_state
    steps: list[TraceStep] = []
    for expected_step, record in enumerate(records[1:], start=1):
        if record.get("record_type") != "step":
            raise ValueError("non-step record found after trace header")
        if int(record["step"]) != expected_step:
            raise ValueError("trace steps must be contiguous and one-based")
        actions = MappingProxyType(
            {
                str(uav_id): MoveAction(_cell_from_data(destination))
                for uav_id, destination in record["actions"].items()
            }
        )
        next_state = state_from_dict(record["next_state"])
        observation = observation_from_dict(record["observation"])
        sensor_results = tuple(
            _sensor_from_data(item) for item in record["sensor_results"]
        )
        raw_info = dict(record.get("info", {}))
        if "unknown_action_ids" in raw_info:
            raw_info["unknown_action_ids"] = tuple(
                raw_info["unknown_action_ids"]
            )
        transition = Transition(
            previous_state=previous_state,
            next_state=next_state,
            observation=observation,
            action_results=tuple(
                _action_result_from_data(item)
                for item in record["action_results"]
            ),
            sensor_results=sensor_results,
            terminated=bool(record["terminated"]),
            truncated=bool(record["truncated"]),
            success=bool(record["success"]),
            info=MappingProxyType(raw_info),
        )
        steps.append(TraceStep(actions=actions, transition=transition))
        previous_state = next_state

    return EpisodeTrace(
        config=config,
        seed=int(header["seed"]),
        policy=policy_name(str(header["policy"])),
        initial_state=initial_state,
        initial_observation=initial_observation,
        steps=tuple(steps),
    )
