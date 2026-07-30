from __future__ import annotations

import numpy as np
from pettingzoo.test import parallel_api_test, parallel_seed_test

from griduav.core import Cell, ScenarioConfig, UAVConfig
from griduav.envs import GridUAVParallelEnv, parallel_env


def test_parallel_env_spaces_contain_reset_and_step_values() -> None:
    config = ScenarioConfig(
        width=5,
        height=4,
        obstacles=frozenset({Cell(2, 2)}),
        uavs=(
            UAVConfig("uav_0", Cell(0, 0)),
            UAVConfig("uav_1", Cell(0, 2)),
        ),
        target_cell=Cell(3, 4),
        sensing_radius=1,
        max_steps=10,
    )
    env = GridUAVParallelEnv(config)

    observations, infos = env.reset(seed=7)

    assert set(observations) == {"uav_0", "uav_1"}
    assert set(infos) == {"uav_0", "uav_1"}
    for agent, observation in observations.items():
        assert env.observation_space(agent).contains(observation)

    actions = {
        "uav_0": np.array([3, 0], dtype=np.int64),
        "uav_1": np.array([3, 2], dtype=np.int64),
    }
    results = env.step(actions)

    for agent, observation in results[0].items():
        assert env.observation_space(agent).contains(observation)
    assert all(isinstance(value, float) for value in results[1].values())


def test_parallel_env_clears_agents_after_team_detection() -> None:
    config = ScenarioConfig(
        width=3,
        height=3,
        obstacles=frozenset(),
        uavs=(UAVConfig("uav_0", Cell(0, 0)),),
        target_cell=Cell(0, 1),
        sensing_radius=0,
        max_steps=5,
    )
    env = GridUAVParallelEnv(config)
    env.reset(seed=0)

    observations, rewards, terminations, truncations, infos = env.step(
        {"uav_0": np.array([0, 1], dtype=np.int64)}
    )

    assert set(observations) == {"uav_0"}
    assert rewards == {"uav_0": 1.0}
    assert terminations == {"uav_0": True}
    assert truncations == {"uav_0": False}
    assert infos["uav_0"]["success"] is True
    assert env.agents == []


def test_official_parallel_contract_and_seed_checks() -> None:
    config = ScenarioConfig(
        width=6,
        height=6,
        obstacles=frozenset({Cell(2, 2)}),
        uavs=(
            UAVConfig("uav_0", Cell(0, 0)),
            UAVConfig("uav_1", Cell(0, 3)),
        ),
        sensing_radius=1,
        max_steps=25,
    )

    parallel_api_test(parallel_env(config), num_cycles=40)
    parallel_seed_test(lambda: parallel_env(config), num_cycles=40)


def test_reset_time_detection_supports_empty_parallel_step() -> None:
    config = ScenarioConfig(
        width=3,
        height=3,
        obstacles=frozenset(),
        uavs=(UAVConfig("uav_0", Cell(0, 0)),),
        target_cell=Cell(0, 0),
        sensing_radius=0,
        max_steps=3,
    )
    env = parallel_env(config)

    observations, infos = env.reset(seed=0)

    assert set(observations) == {"uav_0"}
    assert set(infos) == {"uav_0"}
    assert env.agents == ["uav_0"]
    results = env.step(
        {"uav_0": np.array([2, 2], dtype=np.int64)}
    )
    assert results[1] == {"uav_0": 1.0}
    assert results[2] == {"uav_0": True}
    assert env.agents == []
    assert env.step({}) == ({}, {}, {}, {}, {})
    parallel_api_test(parallel_env(config), num_cycles=2)
