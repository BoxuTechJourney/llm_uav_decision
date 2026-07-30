"""Run a paired-seed GridUAV batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from griduav.evaluation import run_batch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = run_batch(args.config, output_dir=args.output_dir)
    print(
        json.dumps(
            {
                "episodes": len(result.episodes),
                "summary_csv": str(result.summary_csv),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
