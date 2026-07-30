"""Immutable schemas exposed by the GridUAV core interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Mapping, cast

import numpy as np
from numpy.typing import NDArray

BoolArray = NDArray[np.bool_]
IntArray = NDArray[np.int32]

ActionStatus = Literal["moved", "arrived", "blocked", "invalid"]
ActionReason = Literal[
    "none",
    "missing_action",
    "out_of_bounds",
    "obstacle",
    "unreachable",
    "same_destination",
    "occupied",
    "cycle",
]


def readonly_array(
    value: NDArray[Any] | list[Any], dtype: np.dtype[Any] | type[Any]
) -> NDArray[Any]:
    array = np.array(value, dtype=dtype, copy=True)
    array.setflags(write=False)
    return array


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze_value(item) for key, item in value.items()}
        )
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_value(item) for item in value)
    if isinstance(value, np.ndarray):
        return readonly_array(value, value.dtype)
    return value


@dataclass(frozen=True, order=True)
class Cell:
    row: int
    col: int


@dataclass(frozen=True)
class UAVConfig:
    uav_id: str
    start: Cell


@dataclass(frozen=True)
class ScenarioConfig:
    width: int
    height: int
    uavs: tuple[UAVConfig, ...]
    obstacles: frozenset[Cell] = field(default_factory=frozenset)
    target_cell: Cell | None = None
    sensing_radius: int = 1
    max_steps: int = 200
    env_id: str = "GridUAV-Search-v0"

    def __post_init__(self) -> None:
        object.__setattr__(self, "uavs", tuple(self.uavs))
        object.__setattr__(self, "obstacles", frozenset(self.obstacles))
        if self.width <= 0 or self.height <= 0:
            raise ValueError("grid dimensions must be positive")
        if not self.uavs:
            raise ValueError("at least one UAV is required")
        if self.sensing_radius < 0:
            raise ValueError("sensing_radius must be non-negative")
        if self.max_steps <= 0:
            raise ValueError("max_steps must be positive")

        ids = [uav.uav_id for uav in self.uavs]
        starts = [uav.start for uav in self.uavs]
        if len(ids) != len(set(ids)) or any(not item for item in ids):
            raise ValueError("UAV ids must be non-empty and unique")
        if len(starts) != len(set(starts)):
            raise ValueError("UAV starts must be unique")

        for cell in (*self.obstacles, *starts):
            if not self.contains(cell):
                raise ValueError(f"cell is outside the grid: {cell}")
        if set(starts) & self.obstacles:
            raise ValueError("UAV starts cannot overlap obstacles")
        if self.target_cell is not None:
            if not self.contains(self.target_cell):
                raise ValueError("target is outside the grid")
            if self.target_cell in self.obstacles:
                raise ValueError("target cannot overlap an obstacle")

    def contains(self, cell: Cell) -> bool:
        return 0 <= cell.row < self.height and 0 <= cell.col < self.width


@dataclass(frozen=True)
class UAVState:
    uav_id: str
    cell: Cell


@dataclass(frozen=True)
class SensorResult:
    uav_id: str
    visible_cells: tuple[Cell, ...]
    newly_observed_cells: tuple[Cell, ...]
    detected: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "visible_cells", tuple(self.visible_cells))
        object.__setattr__(
            self,
            "newly_observed_cells",
            tuple(self.newly_observed_cells),
        )


@dataclass(frozen=True)
class WorldState:
    obstacle_map: BoolArray
    target_cell: Cell
    uav_states: tuple[UAVState, ...]
    observed_count: IntArray
    target_detected: bool
    step: int
    terminated: bool
    truncated: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "obstacle_map",
            readonly_array(self.obstacle_map, np.bool_),
        )
        object.__setattr__(
            self,
            "observed_count",
            readonly_array(self.observed_count, np.int32),
        )
        object.__setattr__(self, "uav_states", tuple(self.uav_states))


@dataclass(frozen=True)
class AgentObservation:
    obstacle_map: BoolArray
    observed_mask: BoolArray
    uav_states: tuple[UAVState, ...]
    latest_sensor_results: tuple[SensorResult, ...]
    step: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "obstacle_map",
            readonly_array(self.obstacle_map, np.bool_),
        )
        object.__setattr__(
            self,
            "observed_mask",
            readonly_array(self.observed_mask, np.bool_),
        )
        object.__setattr__(self, "uav_states", tuple(self.uav_states))
        object.__setattr__(
            self,
            "latest_sensor_results",
            tuple(self.latest_sensor_results),
        )


@dataclass(frozen=True)
class MoveAction:
    destination: Cell


@dataclass(frozen=True)
class ActionResult:
    uav_id: str
    requested_destination: Cell | None
    previous_cell: Cell
    next_cell: Cell
    status: ActionStatus
    reason: ActionReason
    distance_delta: float


@dataclass(frozen=True)
class Transition:
    previous_state: WorldState
    next_state: WorldState
    observation: AgentObservation
    action_results: tuple[ActionResult, ...]
    sensor_results: tuple[SensorResult, ...]
    terminated: bool
    truncated: bool
    success: bool
    info: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "action_results", tuple(self.action_results)
        )
        object.__setattr__(
            self, "sensor_results", tuple(self.sensor_results)
        )
        object.__setattr__(
            self,
            "info",
            cast(Mapping[str, Any], _freeze_value(self.info)),
        )
