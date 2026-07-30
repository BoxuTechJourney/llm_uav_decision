# T2 — Trace + Replay

## Dependency

T1 is green.

## Deliverables

- Versioned, self-contained JSONL trace writer/reader.
- Round-trip conversion for public core schemas.
- Offline Matplotlib PNG frames and Pillow GIF generation.
- `public`, `debug`, and `paper` target visibility modes.

## Red/green slices

1. Header and transition JSONL round trip.
2. Initial plus per-transition frame generation.
3. Public/debug/paper target visibility.
4. Ordered animated GIF generation.

## Acceptance

Replay uses only `trace.jsonl`, produces `T+1` frames for `T` transitions, and
never invokes `GridUAVModel`.

## Not in scope

Live UI, Pygame, interactive controls, trajectory plots, or coverage plots.
