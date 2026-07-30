"""YAML and dictionary adapters for ScenarioConfig."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from griduav.core import Cell, ScenarioConfig, UAVConfig


def _cell(value: Any, field_name: str) -> Cell:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 2
        or not all(isinstance(item, int) for item in value)
    ):
        raise ValueError(f"{field_name} must be [row, col]")
    return Cell(int(value[0]), int(value[1]))


def scenario_from_dict(data: Mapping[str, Any]) -> ScenarioConfig:
    try:
        env = data.get("env", {})
        grid = data["grid"]
        uavs_data = data["uavs"]
        target = data.get("target", {"placement": "random_reachable"})
        sensing = data.get("sensing", {})
        obstacles = frozenset(
            _cell(value, "grid.obstacles[]")
            for value in grid.get("obstacles", [])
        )
        uavs = tuple(
            UAVConfig(
                uav_id=str(item["id"]),
                start=_cell(item["start"], "uavs[].start"),
            )
            for item in uavs_data
        )
        placement = target.get("placement", "random_reachable")
        if placement == "random_reachable":
            target_cell = None
        elif placement == "fixed":
            target_cell = _cell(target["cell"], "target.cell")
        else:
            raise ValueError(
                "target.placement must be random_reachable or fixed"
            )
        return ScenarioConfig(
            env_id=str(env.get("id", "GridUAV-Search-v0")),
            width=int(grid["width"]),
            height=int(grid["height"]),
            obstacles=obstacles,
            uavs=uavs,
            target_cell=target_cell,
            sensing_radius=int(sensing.get("radius_cells", 1)),
            max_steps=int(env.get("max_steps", 200)),
        )
    except (KeyError, TypeError) as error:
        raise ValueError(f"invalid scenario configuration: {error}") from error


def scenario_to_dict(config: ScenarioConfig) -> dict[str, Any]:
    target: dict[str, Any]
    if config.target_cell is None:
        target = {"placement": "random_reachable"}
    else:
        target = {
            "placement": "fixed",
            "cell": [config.target_cell.row, config.target_cell.col],
        }
    return {
        "env": {"id": config.env_id, "max_steps": config.max_steps},
        "grid": {
            "width": config.width,
            "height": config.height,
            "obstacles": [
                [cell.row, cell.col] for cell in sorted(config.obstacles)
            ],
        },
        "uavs": [
            {
                "id": item.uav_id,
                "start": [item.start.row, item.start.col],
            }
            for item in config.uavs
        ],
        "target": target,
        "sensing": {"radius_cells": config.sensing_radius},
    }


def load_scenario(path: str | Path) -> ScenarioConfig:
    with Path(path).open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, Mapping):
        raise ValueError("scenario root must be a mapping")
    return scenario_from_dict(data)
