"""Deterministic GridUAV transition model."""

from __future__ import annotations

from dataclasses import replace
from types import MappingProxyType
from typing import Mapping

import numpy as np

from griduav._navigation import reachable_cells, shortest_next
from griduav.core.types import (
    ActionResult,
    AgentObservation,
    Cell,
    MoveAction,
    ScenarioConfig,
    SensorResult,
    Transition,
    UAVState,
    WorldState,
    readonly_array,
)


class GridUAVModel:
    """A deep module containing all world transition semantics."""

    def __init__(self, config: ScenarioConfig):
        self.config = config

    def reset(self, seed: int) -> tuple[WorldState, AgentObservation]:
        obstacle_map = np.zeros(
            (self.config.height, self.config.width), dtype=np.bool_
        )
        for cell in self.config.obstacles:
            obstacle_map[cell.row, cell.col] = True

        target = self.config.target_cell
        if target is None:
            candidates = self._random_target_candidates(obstacle_map)
            if not candidates:
                raise ValueError(
                    "no reachable target cell exists outside initial sensing"
                )
            rng = np.random.default_rng(seed)
            target = candidates[int(rng.integers(len(candidates)))]

        uav_states = tuple(
            UAVState(item.uav_id, item.start) for item in self.config.uavs
        )
        observed_count = np.zeros_like(obstacle_map, dtype=np.int32)
        sensor_results = self._sense(uav_states, target, observed_count)
        detected = any(result.detected for result in sensor_results)
        state = WorldState(
            obstacle_map=readonly_array(obstacle_map, np.bool_),
            target_cell=target,
            uav_states=uav_states,
            observed_count=readonly_array(observed_count, np.int32),
            target_detected=detected,
            step=0,
            terminated=detected,
            truncated=False,
        )
        return state, self._observation(state, sensor_results)

    def step(
        self, state: WorldState, actions: Mapping[str, MoveAction]
    ) -> Transition:
        if state.terminated or state.truncated:
            raise RuntimeError("cannot step a completed episode")

        known_ids = {uav.uav_id for uav in state.uav_states}
        unknown_ids = tuple(sorted(set(actions) - known_ids))
        results: list[ActionResult] = []
        next_uavs: list[UAVState] = []

        for uav in state.uav_states:
            action = actions.get(uav.uav_id)
            result = self._propose_action(state, uav, action)
            results.append(result)
        results = self._resolve_same_destination(results)
        results = self._resolve_occupancy(results)
        for result in results:
            next_uavs.append(UAVState(result.uav_id, result.next_cell))

        observed_count = np.array(state.observed_count, dtype=np.int32, copy=True)
        sensor_results = self._sense(
            tuple(next_uavs), state.target_cell, observed_count
        )
        detected = any(result.detected for result in sensor_results)
        next_step = state.step + 1
        terminated = detected
        truncated = not terminated and next_step >= self.config.max_steps
        next_state = WorldState(
            obstacle_map=state.obstacle_map,
            target_cell=state.target_cell,
            uav_states=tuple(next_uavs),
            observed_count=readonly_array(observed_count, np.int32),
            target_detected=state.target_detected or detected,
            step=next_step,
            terminated=terminated,
            truncated=truncated,
        )
        observation = self._observation(next_state, sensor_results)
        return Transition(
            previous_state=state,
            next_state=next_state,
            observation=observation,
            action_results=tuple(results),
            sensor_results=sensor_results,
            terminated=terminated,
            truncated=truncated,
            success=terminated,
            info=MappingProxyType({"unknown_action_ids": unknown_ids}),
        )

    def _resolve_same_destination(
        self, results: list[ActionResult]
    ) -> list[ActionResult]:
        by_destination: dict[Cell, list[int]] = {}
        for index, result in enumerate(results):
            by_destination.setdefault(result.next_cell, []).append(index)

        resolved = list(results)
        for indices in by_destination.values():
            if len(indices) < 2:
                continue
            stationary = [
                index
                for index in indices
                if results[index].previous_cell == results[index].next_cell
            ]
            contenders = stationary or indices
            winner = min(contenders, key=lambda index: results[index].uav_id)
            for index in indices:
                if index == winner:
                    continue
                result = results[index]
                if result.previous_cell == result.next_cell:
                    continue
                resolved[index] = replace(
                    result,
                    next_cell=result.previous_cell,
                    status="blocked",
                    reason="same_destination",
                    distance_delta=0.0,
                )
        return resolved

    def _resolve_occupancy(
        self, results: list[ActionResult]
    ) -> list[ActionResult]:
        resolved = list(results)
        occupant_by_cell = {
            result.previous_cell: result.uav_id for result in results
        }
        index_by_id = {
            result.uav_id: index for index, result in enumerate(results)
        }

        active_ids = {
            result.uav_id
            for result in resolved
            if result.status == "moved"
            and result.next_cell != result.previous_cell
        }
        dependency = {
            uav_id: occupant_by_cell.get(
                resolved[index_by_id[uav_id]].next_cell
            )
            for uav_id in active_ids
        }

        cycle_ids: set[str] = set()
        for start in sorted(active_ids):
            path: list[str] = []
            positions: dict[str, int] = {}
            current: str | None = start
            while current in active_ids and current not in positions:
                positions[current] = len(path)
                path.append(current)
                current = dependency.get(current)
            if current is not None and current in positions:
                cycle_ids.update(path[positions[current] :])

        for uav_id in cycle_ids:
            index = index_by_id[uav_id]
            result = resolved[index]
            resolved[index] = replace(
                result,
                next_cell=result.previous_cell,
                status="blocked",
                reason="cycle",
                distance_delta=0.0,
            )

        changed = True
        while changed:
            changed = False
            active_ids = {
                result.uav_id
                for result in resolved
                if result.status == "moved"
                and result.next_cell != result.previous_cell
            }
            for index, result in enumerate(resolved):
                if result.uav_id not in active_ids:
                    continue
                occupant = occupant_by_cell.get(result.next_cell)
                if occupant is not None and occupant not in active_ids:
                    resolved[index] = replace(
                        result,
                        next_cell=result.previous_cell,
                        status="blocked",
                        reason="occupied",
                        distance_delta=0.0,
                    )
                    changed = True
        return resolved

    def _propose_action(
        self,
        state: WorldState,
        uav: UAVState,
        action: MoveAction | None,
    ) -> ActionResult:
        if action is None:
            return ActionResult(
                uav.uav_id,
                None,
                uav.cell,
                uav.cell,
                "invalid",
                "missing_action",
                0.0,
            )

        destination = action.destination
        if not self.config.contains(destination):
            return ActionResult(
                uav.uav_id,
                destination,
                uav.cell,
                uav.cell,
                "invalid",
                "out_of_bounds",
                0.0,
            )
        if state.obstacle_map[destination.row, destination.col]:
            return ActionResult(
                uav.uav_id,
                destination,
                uav.cell,
                uav.cell,
                "blocked",
                "obstacle",
                0.0,
            )
        if destination == uav.cell:
            return ActionResult(
                uav.uav_id,
                destination,
                uav.cell,
                uav.cell,
                "arrived",
                "none",
                0.0,
            )

        segment = shortest_next(uav.cell, destination, state.obstacle_map)
        if segment is None:
            return ActionResult(
                uav.uav_id,
                destination,
                uav.cell,
                uav.cell,
                "blocked",
                "unreachable",
                0.0,
            )
        next_cell, cost = segment
        return ActionResult(
            uav.uav_id,
            destination,
            uav.cell,
            next_cell,
            "moved",
            "none",
            cost,
        )

    def _random_target_candidates(
        self, obstacle_map: np.ndarray
    ) -> list[Cell]:
        reachable: set[Cell] = set()
        for item in self.config.uavs:
            reachable.update(reachable_cells(item.start, obstacle_map))
        initially_visible = {
            cell
            for item in self.config.uavs
            for cell in self._visible_cells(item.start)
        }
        return sorted(reachable - initially_visible)

    def _visible_cells(self, center: Cell) -> tuple[Cell, ...]:
        radius = self.config.sensing_radius
        cells = []
        for row in range(center.row - radius, center.row + radius + 1):
            for col in range(center.col - radius, center.col + radius + 1):
                cell = Cell(row, col)
                if self.config.contains(cell):
                    cells.append(cell)
        return tuple(sorted(cells))

    def _sense(
        self,
        uav_states: tuple[UAVState, ...],
        target: Cell,
        observed_count: np.ndarray,
    ) -> tuple[SensorResult, ...]:
        results = []
        for uav in uav_states:
            visible = self._visible_cells(uav.cell)
            newly_observed = tuple(
                cell
                for cell in visible
                if observed_count[cell.row, cell.col] == 0
            )
            for cell in visible:
                observed_count[cell.row, cell.col] += 1
            results.append(
                SensorResult(
                    uav_id=uav.uav_id,
                    visible_cells=visible,
                    newly_observed_cells=newly_observed,
                    detected=target in visible,
                )
            )
        return tuple(results)

    def _observation(
        self,
        state: WorldState,
        sensor_results: tuple[SensorResult, ...],
    ) -> AgentObservation:
        return AgentObservation(
            obstacle_map=state.obstacle_map,
            observed_mask=readonly_array(state.observed_count > 0, np.bool_),
            uav_states=state.uav_states,
            latest_sensor_results=sensor_results,
            step=state.step,
        )
