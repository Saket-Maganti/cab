# CAB CPU Fixture Analysis Report

Status: **PASS** (`FIXTURE_ONLY`)

The fixture-safe suite completed 62 tests in 4.42 seconds. It covered paired
metrics, exact binary transitions, clustered and stratified bootstrap,
resumable shard merge and duplicate rejection, rank uncertainty and ties,
zero/near-zero denominator suppression, scorer-error sensitivity,
naturalistic predictive-validity functions, RAAC traces and opportunity
denominators, and paper-asset refusal for ineligible evidence.

A separate canonical clustered bootstrap requested 1,000 fixture replicates
and completed in 0.351 seconds over four fixture clusters. All additive
metrics had 1,000 valid replicates; ratio metrics had 994 because six
resamples correctly triggered zero-denominator suppression.

These checks validate algorithms and edge handling only. Their numerical
values are synthetic and are not research findings, model measurements,
scientific evidence, or paper-eligible assets.
