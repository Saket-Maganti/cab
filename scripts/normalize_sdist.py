#!/usr/bin/env python3
"""Normalize a built source distribution for byte-reproducible release attestation."""

from __future__ import annotations

import argparse
import gzip
import io
import os
import tarfile
from pathlib import Path


def normalize_sdist(source: Path, output: Path, *, epoch: int) -> None:
    members: list[tuple[tarfile.TarInfo, bytes | None]] = []
    with tarfile.open(source, "r:gz") as archive:
        for original in archive.getmembers():
            payload = None
            if original.isfile():
                extracted = archive.extractfile(original)
                if extracted is None:
                    raise ValueError(f"unable to read sdist member: {original.name}")
                payload = extracted.read()
            info = tarfile.TarInfo(original.name)
            info.size = len(payload) if payload is not None else 0
            info.mode = original.mode
            info.type = original.type
            info.linkname = original.linkname
            info.mtime = epoch
            info.uid = 0
            info.gid = 0
            info.uname = "root"
            info.gname = "root"
            info.pax_headers = {}
            members.append((info, payload))
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w", format=tarfile.PAX_FORMAT) as normalized:
        for info, payload in sorted(members, key=lambda row: row[0].name):
            normalized.addfile(info, io.BytesIO(payload) if payload is not None else None)
    output.parent.mkdir(parents=True, exist_ok=True)
    with (
        output.open("wb") as destination,
        gzip.GzipFile(
            filename="",
            mode="wb",
            compresslevel=9,
            fileobj=destination,
            mtime=epoch,
        ) as compressed,
    ):
        compressed.write(tar_stream.getvalue())
    os.chmod(output, 0o644)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--epoch", type=int, required=True)
    args = parser.parse_args()
    normalize_sdist(args.source, args.output, epoch=args.epoch)
    print(args.output)


if __name__ == "__main__":
    main()
