# CAB Research OS CLI

Core commands:

```text
cab registry init|doctor|export|verify|backup|restore|results
cab env doctor
cab benchmark init|compile|validate|diversity|review-packet|freeze|retire
cab plan
cab run --dry-run
cab run --level5-fixture-dir PATH
cab status|cancel|resume|merge
cab artifacts verify|export|gc --dry-run
cab reliability inject|campaign|report
cab review serve|qualify|assign|status|export|adjudicate|validate
cab evaluator validate-submission|dry-run|run-fixture|audit|receipt
cab evidence trace|verify
cab certify
cab model-card
cab claims validate
cab plugins list
cab reproduce
cab redteam
cab level5 check
cab release-check
```

The legacy CAB command surface remains available. `cab run --dry-run` is the
provider-free Level-5 planner; normal legacy `cab run --config` behavior is
unchanged. `cab benchmark freeze` fails until a genuine C10 certificate exists.
