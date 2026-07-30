"""Target-blind baseline policies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol, cast

import numpy as np

from griduav._navigation import distances_from, shortest_next
from griduav.core import AgentObservation, Cell, MoveAction

PolicyName = Literal["random", "sweep", "greedy"]
POLICY_NAMES: tuple[PolicyName, ...] = ("random", "sweep", "greedy")


class TeamPolicy(Protocol):
    def reset(
        self, observation: AgentObservation, seed: int
    ) -> None: ...

    def act(
        self, observation: AgentObservation
    ) -> dict[str, MoveAction]: ...


def _traversable(observation: AgentObservation) -> tuple[Cell, ...]:
    height, width = observation.obstacle_map.shape
    return tuple(
        Cell(row, col)
        for row in range(height)
        for col in range(width)
        if not observation.obstacle_map[row, col]
    )


@dataclass
class RandomPolicy:
    _rng: np.random.Generator | None = field(init=False, default=None)
    _cells: tuple[Cell, ...] = field(init=False, default=())

    def reset(self, observation: AgentObservation, seed: int) -> None:
        self._rng = np.random.default_rng(seed)
        self._cells = _traversable(observation)

    def act(
        self, observation: AgentObservation
    ) -> dict[str, MoveAction]:
        if self._rng is None:
            raise RuntimeError("policy must be reset before act")
        return {
            uav.uav_id: MoveAction(
                self._cells[int(self._rng.integers(len(self._cells)))]
            )
            for uav in observation.uav_states
        }


@dataclass
class SweepPolicy:
    _sequence: tuple[Cell, ...] = field(init=False, default=())
    _cursor: int = field(init=False, default=0)
    _goals: dict[str, Cell] = field(init=False, default_factory=dict)

    def reset(self, observation: AgentObservation, seed: int) -> None:
        del seed
        height, width = observation.obstacle_map.shape
        cells = []
        for row in range(height):
            columns = range(width) if row % 2 == 0 else range(width - 1, -1, -1)
            cells.extend(
                Cell(row, col)
                for col in columns
                if not observation.obstacle_map[row, col]
            )
        self._sequence = tuple(cells)
        self._cursor = 0
        self._goals = {}

    def act(
        self, observation: AgentObservation
    ) -> dict[str, MoveAction]:
        if not self._sequence:
            raise RuntimeError("policy must be reset before act")
        reserved_next_cells: set[Cell] = set()
        actions: dict[str, MoveAction] = {}
        ordered_uavs = sorted(
            observation.uav_states, key=lambda item: item.uav_id
        )
        for index, uav in enumerate(ordered_uavs):
            protected_current_cells = {
                item.cell for item in ordered_uavs[index + 1 :]
            }
            next_cell = self._next_distinct_cell(
                observation,
                uav.uav_id,
                uav.cell,
                reserved_next_cells | protected_current_cells,
            )
            reserved_next_cells.add(next_cell)
            actions[uav.uav_id] = MoveAction(next_cell)
        return actions

    def _next_distinct_cell(
        self,
        observation: AgentObservation,
        uav_id: str,
        current: Cell,
        reserved_next_cells: set[Cell],
    ) -> Cell:
        goal = self._goals.get(uav_id)
        for _ in range(len(self._sequence)):
            if (
                goal is None
                or goal == current
                or observation.observed_mask[goal.row, goal.col]
            ):
                goal = self._next_goal(observation)
            segment = shortest_next(
                current, goal, observation.obstacle_map
            )
            next_cell = current if segment is None else segment[0]
            if next_cell not in reserved_next_cells:
                self._goals[uav_id] = goal
                return next_cell
            goal = None
        if current in reserved_next_cells:
            raise RuntimeError("no distinct sweep next-cell assignment exists")
        return current

    def _next_goal(self, observation: AgentObservation) -> Cell:
        for _ in range(len(self._sequence)):
            cell = self._sequence[self._cursor % len(self._sequence)]
            self._cursor += 1
            if not observation.observed_mask[cell.row, cell.col]:
                return cell
        return min(uav.cell for uav in observation.uav_states)


@dataclass
class GreedyPolicy:
    _ready: bool = field(init=False, default=False)

    def reset(self, observation: AgentObservation, seed: int) -> None:
        del observation, seed
        self._ready = True

    def act(
        self, observation: AgentObservation
    ) -> dict[str, MoveAction]:
        if not self._ready:
            raise RuntimeError("policy must be reset before act")
        candidates = {
            cell
            for cell in _traversable(observation)
            if not observation.observed_mask[cell.row, cell.col]
        }
        reserved: set[Cell] = set()
        actions: dict[str, MoveAction] = {}
        for uav in sorted(observation.uav_states, key=lambda item: item.uav_id):
            distances = distances_from(uav.cell, observation.obstacle_map)
            available = [
                cell
                for cell in candidates - reserved
                if cell in distances
            ]
            goal = (
                min(
                    available,
                    key=lambda cell: (
                        distances[cell],
                        cell.row,
                        cell.col,
                    ),
                )
                if available
                else uav.cell
            )
            reserved.add(goal)
            actions[uav.uav_id] = MoveAction(goal)
        return actions


POLICY_FACTORIES = {
    "random": RandomPolicy,
    "sweep": SweepPolicy,
    "greedy": GreedyPolicy,
}


def policy_name(value: str) -> PolicyName:
    if value not in POLICY_FACTORIES:
        raise ValueError(f"unknown policy: {value}")
    return cast(PolicyName, value)


def create_policy(name: str) -> TeamPolicy:
    return POLICY_FACTORIES[policy_name(name)]()
