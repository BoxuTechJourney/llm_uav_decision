"""Render an offline GridUAV trace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from griduav.replay import REPLAY_MODES, render_replay


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--mode",
        choices=REPLAY_MODES,
        default="public",
    )
    parser.add_argument("--gif", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_dir = (
        args.output_dir
        if args.output_dir is not None
        else args.trace.parent / f"replay_{args.mode}"
    )
    result = render_replay(
        args.trace,
        output_dir,
        mode=args.mode,
        make_gif=args.gif,
    )
    print(
        json.dumps(
            {
                "frames": len(result.frames),
                "gif": None if result.gif is None else str(result.gif),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
