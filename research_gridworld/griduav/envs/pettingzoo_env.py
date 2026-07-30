"""PettingZoo ParallelEnv adapter for GridUAV core."""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np
from gymnasium import spaces
from pettingzoo import ParallelEnv

from griduav.core import (
    AgentObservation,
    Cell,
    GridUAVModel,
    MoveAction,
    ScenarioConfig,
    Transition,
    WorldState,
)


def _default_config() -> ScenarioConfig:
    from griduav.core import UAVConfig

    return ScenarioConfig(
        width=8,
        height=8,
        obstacles=frozenset(),
        uavs=(UAVConfig("uav_0", Cell(0, 0)),),
        sensing_radius=1,
        max_steps=100,
    )


class GridUAVParallelEnv(ParallelEnv):
    metadata = {
        "name": "griduav_v0",
        "render_modes": [],
        "is_parallelizable": True,
    }

    def __init__(
        self,
        config: ScenarioConfig | None = None,
        render_mode: str | None = None,
    ):
        if render_mode is not None:
            raise ValueError("GridUAV v0 supports offline replay only")
        self.config = config or _default_config()
        self.render_mode = render_mode
        self.model = GridUAVModel(self.config)
        self.possible_agents = [item.uav_id for item in self.config.uavs]
        self.agents: list[str] = []
        self.max_cycles = self.config.max_steps
        self._state: WorldState | None = None
        self._observation: AgentObservation | None = None

        nvec = np.tile(
            np.array([self.config.height, self.config.width], dtype=np.int64),
            (len(self.possible_agents), 1),
        )
        observation_space = spaces.Dict(
            {
                "obstacle_map": spaces.MultiBinary(
                    (self.config.height, self.config.width)
                ),
                "observed_mask": spaces.MultiBinary(
                    (self.config.height, self.config.width)
                ),
                "uav_positions": spaces.MultiDiscrete(
                    nvec, dtype=np.int64
                ),
                "latest_detections": spaces.MultiBinary(
                    len(self.possible_agents)
                ),
                "step": spaces.Discrete(self.config.max_steps + 1),
            }
        )
        action_space = spaces.MultiDiscrete(
            [self.config.height, self.config.width], dtype=np.int64
        )
        self._observation_spaces = {
            agent: observation_space for agent in self.possible_agents
        }
        self._action_spaces = {
            agent: action_space for agent in self.possible_agents
        }

    def observation_space(self, agent: str) -> spaces.Space[Any]:
        return self._observation_spaces[agent]

    def action_space(self, agent: str) -> spaces.Space[Any]:
        return self._action_spaces[agent]

    def reset(
        self,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
        del options
        if seed is None:
            seed = int(
                np.random.SeedSequence().generate_state(1, dtype=np.uint32)[0]
            )
        self.agents = list(self.possible_agents)
        self._state, self._observation = self.model.reset(seed)
        encoded = self._encode_observation(self._observation)
        observations = {
            agent: self._copy_observation(encoded) for agent in self.agents
        }
        infos = {agent: {"seed": seed} for agent in self.agents}
        return observations, infos

    def step(
        self, actions: Mapping[str, Any]
    ) -> tuple[
        dict[str, dict[str, Any]],
        dict[str, float],
        dict[str, bool],
        dict[str, bool],
        dict[str, dict[str, Any]],
    ]:
        if self._state is None:
            raise RuntimeError("reset must be called before step")
        if not self.agents:
            if actions:
                raise RuntimeError(
                    "completed environment accepts only an empty action mapping"
                )
            return {}, {}, {}, {}, {}

        active_agents = tuple(self.agents)
        if self._state.terminated or self._state.truncated:
            assert self._observation is not None
            encoded = self._encode_observation(self._observation)
            observations = {
                agent: self._copy_observation(encoded)
                for agent in active_agents
            }
            rewards = {
                agent: 1.0 if self._state.target_detected else 0.0
                for agent in active_agents
            }
            terminations = {
                agent: self._state.terminated for agent in active_agents
            }
            truncations = {
                agent: self._state.truncated for agent in active_agents
            }
            infos = {
                agent: {
                    "success": self._state.target_detected,
                    "reset_terminal": True,
                }
                for agent in active_agents
            }
            self.agents = []
            return (
                observations,
                rewards,
                terminations,
                truncations,
                infos,
            )

        core_actions = {
            agent: MoveAction(
                Cell(int(value[0]), int(value[1]))
            )
            for agent, value in actions.items()
        }
        transition = self.model.step(self._state, core_actions)
        self._state = transition.next_state
        self._observation = transition.observation
        encoded = self._encode_observation(transition.observation)
        observations = {
            agent: self._copy_observation(encoded)
            for agent in active_agents
        }
        result_by_agent = {
            result.uav_id: result
            for result in transition.action_results
        }
        rewards = self._rewards(active_agents, transition)
        terminations = {
            agent: transition.terminated for agent in active_agents
        }
        truncations = {
            agent: transition.truncated for agent in active_agents
        }
        infos = {
            agent: {
                "action_status": result_by_agent[agent].status,
                "action_reason": result_by_agent[agent].reason,
                "success": transition.success,
            }
            for agent in active_agents
        }
        if transition.terminated or transition.truncated:
            self.agents = []
        return observations, rewards, terminations, truncations, infos

    def _rewards(
        self, agents: tuple[str, ...], transition: Transition
    ) -> dict[str, float]:
        if transition.success:
            return {agent: 1.0 for agent in agents}
        result_by_agent = {
            result.uav_id: result for result in transition.action_results
        }
        return {
            agent: (
                -0.01
                if result_by_agent[agent].status == "moved"
                else 0.0
            )
            for agent in agents
        }

    def _encode_observation(
        self, observation: AgentObservation
    ) -> dict[str, Any]:
        return {
            "obstacle_map": observation.obstacle_map.astype(
                np.int8, copy=True
            ),
            "observed_mask": observation.observed_mask.astype(
                np.int8, copy=True
            ),
            "uav_positions": np.array(
                [
                    [uav.cell.row, uav.cell.col]
                    for uav in observation.uav_states
                ],
                dtype=np.int64,
            ),
            "latest_detections": np.array(
                [
                    int(result.detected)
                    for result in observation.latest_sensor_results
                ],
                dtype=np.int8,
            ),
            "step": observation.step,
        }

    @staticmethod
    def _copy_observation(
        observation: Mapping[str, Any]
    ) -> dict[str, Any]:
        return {
            key: value.copy() if isinstance(value, np.ndarray) else value
            for key, value in observation.items()
        }

    def close(self) -> None:
        return None


def parallel_env(
    config: ScenarioConfig | None = None,
    render_mode: str | None = None,
) -> GridUAVParallelEnv:
    return GridUAVParallelEnv(config=config, render_mode=render_mode)
