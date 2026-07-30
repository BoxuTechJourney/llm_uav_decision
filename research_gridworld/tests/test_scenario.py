from __future__ import annotations

from pathlib import Path

from griduav.core import Cell
from griduav.scenario import load_scenario


def test_yaml_scenario_loads_explicit_obstacles_and_random_target(
    tmp_path: Path,
) -> None:
    path = tmp_path / "scenario.yaml"
    path.write_text(
        """
env:
  id: Test-v0
  max_steps: 12
grid:
  width: 5
  height: 4
  obstacles: [[1, 1], [2, 3]]
uavs:
  - id: uav_0
    start: [0, 0]
target:
  placement: random_reachable
sensing:
  radius_cells: 2
""".strip(),
        encoding="utf-8",
    )

    config = load_scenario(path)

    assert config.env_id == "Test-v0"
    assert config.obstacles == frozenset({Cell(1, 1), Cell(2, 3)})
    assert config.target_cell is None
    assert config.sensing_radius == 2
    assert config.max_steps == 12
