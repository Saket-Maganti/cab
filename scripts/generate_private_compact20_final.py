#!/usr/bin/env python3
"""Generate the private Compact-20 replacement and write only its public commitment."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from causal_agent_bench.final_pre_run.private_packet import build_private_packet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", default="private_data/final_hostile_pre_run")
    parser.add_argument("--seed-file", default=None)
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument(
        "--public-commitment",
        default="data/manifests/compact20_final_private_commitment.json",
    )
    args = parser.parse_args()
    if args.fixture == (args.seed_file is not None):
        raise SystemExit("choose exactly one of --seed-file (real private packet) or --fixture")
    if args.fixture:
        seed = hashlib.sha256(b"cab-explicit-fixture-private-packet-v1").digest()
    else:
        seed_path = Path(args.seed_file)
        if seed_path.suffix != ".key":
            raise SystemExit("real seed file must use ignored .key suffix")
        seed = seed_path.read_bytes()
    commitment = build_private_packet(Path(args.private_root), seed)
    output = Path(args.public_commitment)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(commitment, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": commitment["status"],
                "packet_id": commitment["packet_id"],
                "candidate_count": commitment["candidate_count"],
                "commitment_sha256": commitment["commitment_sha256"],
                "private_root": str(Path(args.private_root)),
                "fixture_only": args.fixture,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
