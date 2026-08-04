# Prompt 04 — Scale-100 and Naturalistic Dataset Build


## Repository

`/Users/saketmaganti/Projects/causal-agent-bench`

## Hard Resource Envelope

Assume the user has only:

- MacBook Air M4, 16 GB unified memory, 512 GB storage;
- free Kaggle notebooks with two NVIDIA T4 GPUs when available;
- no A100/H100 cluster;
- no guaranteed paid API budget;
- no background compute service;
- limited storage and session duration.

Design every solution around this envelope. Prefer streaming, sharding, quantisation, resumability, compact artifacts, incremental exports, and CPU-safe validation.

## Scientific Integrity Rules

Never:

- fabricate human review;
- fabricate model trajectories;
- fabricate results, costs, timings, tables, plots, or claims;
- tune the benchmark after seeing confirmatory results;
- expose gold answers to agents;
- mark fixture, mock, stub, dry-run, or interrupted outputs as scientific evidence;
- use provider secrets found in the environment;
- commit or push unless explicitly authorised;
- silently delete user work;
- claim ICLR acceptance or submission readiness without evidence.

Always distinguish:

- `DESIGN_ONLY`
- `ENGINEERING_ONLY`
- `FIXTURE_ONLY`
- `HUMAN_INPUT_REQUIRED`
- `EXECUTION_PENDING`
- `PRELIMINARY_REAL_EVIDENCE`
- `AUDITED_REAL_EVIDENCE`
- `PAPER_ELIGIBLE_EVIDENCE`

## Required Working Style

- Inspect before modifying.
- Repair locally fixable defects instead of only reporting them.
- Preserve reversible history.
- Prefer canonical implementations over duplicate layers.
- Record exact commands and exit codes.
- Keep the public surface clean.
- Build fail-closed gates.
- Stop when the stated phase is complete.


## Goal

Build a genuinely diverse confirmatory set and naturalistic transfer set without paid generation.

## Diversity Audit

Measure raw tasks, unique bases, templates, normalised instructions, domains, tools, answer contracts, difficulty, intervention families, sources, lexical duplication, and structural duplication.

## Scale-100

Construct roughly 100 genuinely distinct base tasks with 8–10 domains, balanced difficulty, broad tools, diverse answer contracts, low template duplication, balanced families, no development/Compact overlap, fixed hashes, and provenance.

Quality is more important than exact count.

## Naturalistic Transfer

Create 50–100 realistic tasks using local or openly licensed artifacts in policy, spreadsheets, scheduling, files, data cleaning, travel, debugging, configuration, retrieval, conflicting sources, stale records, and tool outages.

Require provenance, licence, privacy check, injection scan, hidden gold, answer contract, and human validation.

## Intervention Strength

Define low, medium, and high strengths for selected families while preserving goals.

## Held-Out Structure

Create development, Compact-20 pilot, Scale-100 confirmatory, naturalistic transfer, optional Main, and hidden challenge roles. Block ID, text, template, source, and answer overlap.

## Resource-Aware Main Set

Do not automatically run Main-500. Proceed only if Scale-100 signal is stable, transfer is useful, diversity is strong, added power is needed, and resources permit. A diverse 150–250-task package may be preferable.

## Storage

Use JSONL, compression, deduplication, no model weights in Git, no duplicate trajectories, archive manifests, and per-study retention rules.

## Outputs

- frozen Scale-100 candidate;
- naturalistic candidate;
- overlap and diversity reports;
- licence/provenance registry;
- injection report;
- Main expansion gate;
- review packets.

## Acceptance Gate

No model-output-driven task selection.
