#!/usr/bin/env python3
"""Wrapper for build-release-manifest CLI."""

from __future__ import annotations

from causal_agent_bench.release.build_manifest import build_release_manifest


def main() -> int:
    manifest = build_release_manifest()
    print(f"wrote release/release_manifest.json (hash={manifest['release_bundle_hash'][:16]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
