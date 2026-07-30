from __future__ import annotations

from pathlib import Path

from PIL import Image

from griduav.core import (
    Cell,
    GridUAVModel,
    MoveAction,
    ScenarioConfig,
    UAVConfig,
)
from griduav.replay import render_replay
from griduav.trace import EpisodeTrace, TraceStep, write_trace

TARGET_RGB = (214, 39, 40)


def count_target_pixels(path: Path) -> int:
    image = Image.open(path).convert("RGB")
    return sum(
        pixel == TARGET_RGB for pixel in image.get_flattened_data()
    )


def detection_trace(path: Path) -> Path:
    config = ScenarioConfig(
        width=3,
        height=3,
        obstacles=frozenset(),
        uavs=(UAVConfig("uav_0", Cell(0, 0)),),
        target_cell=Cell(0, 1),
        sensing_radius=0,
        max_steps=5,
    )
    model = GridUAVModel(config)
    state, observation = model.reset(0)
    actions = {"uav_0": MoveAction(Cell(0, 1))}
    transition = model.step(state, actions)
    return write_trace(
        path,
        EpisodeTrace(
            config=config,
            seed=0,
            policy="sweep",
            initial_state=state,
            initial_observation=observation,
            steps=(TraceStep(actions, transition),),
        ),
    )


def test_replay_modes_control_target_visibility_and_frame_count(
    tmp_path: Path,
) -> None:
    trace_path = detection_trace(tmp_path / "trace.jsonl")

    public = render_replay(
        trace_path, tmp_path / "public", mode="public", make_gif=False
    )
    debug = render_replay(
        trace_path, tmp_path / "debug", mode="debug", make_gif=False
    )
    paper = render_replay(
        trace_path, tmp_path / "paper", mode="paper", make_gif=False
    )

    assert len(public.frames) == len(debug.frames) == len(paper.frames) == 2
    assert [count_target_pixels(path) for path in public.frames] == [0, 0]
    assert all(count_target_pixels(path) > 0 for path in debug.frames)
    assert [count_target_pixels(path) > 0 for path in paper.frames] == [
        False,
        True,
    ]


def test_replay_gif_uses_all_frames_in_order(tmp_path: Path) -> None:
    trace_path = detection_trace(tmp_path / "trace.jsonl")

    output = render_replay(
        trace_path, tmp_path / "gif", mode="public", make_gif=True
    )

    assert [path.name for path in output.frames] == [
        "replay_step_000.png",
        "replay_step_001.png",
    ]
    assert output.gif is not None and output.gif.exists()
    with Image.open(output.gif) as image:
        assert image.n_frames == 2
