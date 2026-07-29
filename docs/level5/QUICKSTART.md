# Level-5 quickstart

```bash
python3 -m pip install -e ".[dev]"
cab env doctor
cab registry init
cab benchmark validate --spec examples/level5/public_fixture/authoring.yaml
cab benchmark compile --spec examples/level5/public_fixture/authoring.yaml
cab run --dry-run
cab reproduce --workdir /tmp/cab_level5_reproduction
cab level5 check
```

The reproduction command executes only deterministic fixtures. The expected
gate is foundation complete with genuine human, live, external reproduction and
pilot blockers. Never interpret the fixture receipt as model evidence.
