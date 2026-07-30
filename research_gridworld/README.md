# GridUAV

GridUAV is a deterministic, traceable multi-UAV grid-search environment.
`PLATFORM_SPEC.md` defines the v0 behavior.

Install for development:

```bash
python -m pip install -e ".[test]"
```

Run tests:

```bash
python -m pytest
```

Run a batch and render a trace:

```bash
python -m griduav.scripts.run_batch --config configs/smoke.yaml
python -m griduav.scripts.render_replay --trace results/GridUAV-Smoke-v0_seed000_random/trace.jsonl --mode public --gif
```
