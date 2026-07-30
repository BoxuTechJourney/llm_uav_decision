"""Private deterministic grid-navigation primitives shared by core and policies."""

from __future__ import annotations

from collections import deque
import heapq
from math import sqrt

import numpy as np

from griduav.core.types import Cell


def neighbours(
    cell: Cell, obstacle_map: np.ndarray
) -> tuple[tuple[Cell, float], ...]:
    height, width = obstacle_map.shape
    result = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            row, col = cell.row + dr, cell.col + dc
            if not (0 <= row < height and 0 <= col < width):
                continue
            if obstacle_map[row, col]:
                continue
            if dr and dc:
                if (
                    obstacle_map[cell.row + dr, cell.col]
                    or obstacle_map[cell.row, cell.col + dc]
                ):
                    continue
                cost = sqrt(2.0)
            else:
                cost = 1.0
            result.append((Cell(row, col), cost))
    return tuple(sorted(result, key=lambda item: item[0]))


def reachable_cells(
    start: Cell, obstacle_map: np.ndarray
) -> frozenset[Cell]:
    visited = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbour, _ in neighbours(current, obstacle_map):
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(neighbour)
    return frozenset(visited)


def distances_from(
    start: Cell, obstacle_map: np.ndarray
) -> dict[Cell, float]:
    distances = {start: 0.0}
    queue: list[tuple[float, int, int, Cell]] = [
        (0.0, start.row, start.col, start)
    ]
    while queue:
        distance, _, _, current = heapq.heappop(queue)
        if distance > distances[current] + 1e-12:
            continue
        for neighbour, cost in neighbours(current, obstacle_map):
            candidate = distance + cost
            if candidate + 1e-12 < distances.get(
                neighbour, float("inf")
            ):
                distances[neighbour] = candidate
                heapq.heappush(
                    queue,
                    (
                        candidate,
                        neighbour.row,
                        neighbour.col,
                        neighbour,
                    ),
                )
    return distances


def shortest_next(
    start: Cell,
    destination: Cell,
    obstacle_map: np.ndarray,
) -> tuple[Cell, float] | None:
    distances = distances_from(destination, obstacle_map)
    choices = [
        (
            cost + distances[neighbour],
            neighbour.row,
            neighbour.col,
            neighbour,
            cost,
        )
        for neighbour, cost in neighbours(start, obstacle_map)
        if neighbour in distances
    ]
    if not choices:
        return None
    _, _, _, next_cell, cost = min(choices)
    return next_cell, cost
