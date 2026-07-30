"""Offline trace renderer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
from PIL import Image

from griduav.core import ActionResult, SensorResult, WorldState
from griduav.trace import read_trace

ReplayMode = Literal["public", "debug", "paper"]
REPLAY_MODES: tuple[ReplayMode, ...] = ("public", "debug", "paper")


def replay_mode(value: str) -> ReplayMode:
    if value not in REPLAY_MODES:
        raise ValueError("mode must be public, debug, or paper")
    return cast(ReplayMode, value)

TARGET_COLOR = "#d62728"
OBSTACLE_COLOR = "#333333"
UNOBSERVED_COLOR = "#f2f2f2"
OBSERVED_COLOR = "#cfe8f3"
NEWLY_OBSERVED_COLOR = "#98df8a"
UAV_COLORS = ("#1f77b4", "#ff7f0e", "#9467bd", "#17becf", "#8c564b")


@dataclass(frozen=True)
class ReplayOutput:
    frames: tuple[Path, ...]
    gif: Path | None


def _show_target(mode: ReplayMode, state: WorldState) -> bool:
    return mode == "debug" or (mode == "paper" and state.target_detected)


def _draw_frame(
    path: Path,
    state: WorldState,
    mode: ReplayMode,
    sensor_results: tuple[SensorResult, ...],
    action_results: tuple[ActionResult, ...] = (),
) -> None:
    height, width = state.obstacle_map.shape
    figure, axis = plt.subplots(
        figsize=(max(3.0, width * 0.55), max(3.0, height * 0.55)),
        dpi=100,
    )
    newly_observed = {
        cell
        for result in sensor_results
        for cell in result.newly_observed_cells
    }
    newly_observed_positions = {
        (cell.row, cell.col) for cell in newly_observed
    }

    for row in range(height):
        for col in range(width):
            if state.obstacle_map[row, col]:
                color = OBSTACLE_COLOR
            elif (row, col) in newly_observed_positions:
                color = NEWLY_OBSERVED_COLOR
            elif state.observed_count[row, col] > 0:
                color = OBSERVED_COLOR
            else:
                color = UNOBSERVED_COLOR
            axis.add_patch(
                Rectangle(
                    (col, row),
                    1,
                    1,
                    facecolor=color,
                    edgecolor="#b0b0b0",
                    linewidth=0.8,
                    antialiased=False,
                )
            )

    for result in action_results:
        if result.previous_cell != result.next_cell:
            axis.add_patch(
                FancyArrowPatch(
                    (
                        result.previous_cell.col + 0.5,
                        result.previous_cell.row + 0.5,
                    ),
                    (
                        result.next_cell.col + 0.5,
                        result.next_cell.row + 0.5,
                    ),
                    arrowstyle="->",
                    mutation_scale=10,
                    color="#4d4d4d",
                    linewidth=1.4,
                    zorder=3,
                )
            )

    if _show_target(mode, state):
        axis.add_patch(
            Rectangle(
                (state.target_cell.col + 0.15, state.target_cell.row + 0.15),
                0.7,
                0.7,
                facecolor=TARGET_COLOR,
                edgecolor=TARGET_COLOR,
                linewidth=0,
                antialiased=False,
                zorder=4,
            )
        )

    for index, uav in enumerate(state.uav_states):
        color = UAV_COLORS[index % len(UAV_COLORS)]
        axis.add_patch(
            Circle(
                (uav.cell.col + 0.5, uav.cell.row + 0.5),
                0.25,
                facecolor=color,
                edgecolor="white",
                linewidth=1,
                zorder=5,
            )
        )
        axis.text(
            uav.cell.col + 0.5,
            uav.cell.row + 0.5,
            str(index),
            color="white",
            fontsize=7,
            ha="center",
            va="center",
            zorder=6,
        )

    status = "DETECTED" if state.target_detected else "SEARCHING"
    axis.set_title(f"GridUAV step {state.step} · {status} · {mode}")
    axis.set_xlim(0, width)
    axis.set_ylim(height, 0)
    axis.set_aspect("equal")
    axis.set_xticks([])
    axis.set_yticks([])
    figure.tight_layout()
    figure.savefig(path, facecolor="white")
    plt.close(figure)


def render_replay(
    trace_path: str | Path,
    output_dir: str | Path,
    *,
    mode: ReplayMode = "public",
    make_gif: bool = True,
    frame_duration_ms: int = 400,
) -> ReplayOutput:
    mode = replay_mode(mode)
    trace = read_trace(trace_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    frames: list[Path] = []
    initial_path = output / "replay_step_000.png"
    _draw_frame(
        initial_path,
        trace.initial_state,
        mode,
        trace.initial_observation.latest_sensor_results,
    )
    frames.append(initial_path)
    for index, step in enumerate(trace.steps, start=1):
        frame_path = output / f"replay_step_{index:03d}.png"
        _draw_frame(
            frame_path,
            step.transition.next_state,
            mode,
            step.transition.sensor_results,
            step.transition.action_results,
        )
        frames.append(frame_path)

    gif_path: Path | None = None
    if make_gif:
        gif_path = output / "replay.gif"
        images = [Image.open(frame).convert("RGB") for frame in frames]
        try:
            images[0].save(
                gif_path,
                save_all=True,
                append_images=images[1:],
                duration=frame_duration_ms,
                loop=0,
                disposal=2,
            )
        finally:
            for image in images:
                image.close()
    return ReplayOutput(frames=tuple(frames), gif=gif_path)
