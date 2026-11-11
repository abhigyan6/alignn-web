#!/usr/bin/env python3
"""Explicit allowlist export, without app history/configuration/user fixtures."""

import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def export(output):
    output = output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError("Export must be outside app checkout")
    marker = output / "EXPORT.json"
    if output.exists() and any(output.iterdir()) and not marker.is_file():
        raise ValueError("Refusing unknown nonempty destination")
    output.mkdir(parents=True, exist_ok=True)
    files = {
        Path("src/alignn_scraper") / p.name: p
        for p in (ROOT / "apps/api/src/alignn_scraper").glob("*.py")
    }
    for name in ("test_contract.py", "test_transport.py"):
        files[Path("tests") / name] = ROOT / "tests/scraper" / name
    template = ROOT / "scripts/scraper-template"
    for p in template.rglob("*"):
        if p.is_file():
            files[p.relative_to(template)] = p
    previous = (
        json.loads(marker.read_text()).get("files", []) if marker.exists() else []
    )
    for name in previous:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or ".git" in path.parts:
            raise ValueError("Invalid export marker")
        if path not in files and (output / path).is_file():
            (output / path).unlink()
    for relative, source in files.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    dirty = bool(
        subprocess.check_output(
            [
                "git",
                "status",
                "--porcelain",
                "--",
                "apps/api/src/alignn_scraper",
                "tests/scraper",
                "scripts/export-scraper.py",
                "scripts/scraper-template",
            ],
            cwd=ROOT,
            text=True,
        )
    )
    marker.write_text(
        json.dumps(
            {
                "origin": "abhigyan6/alignn-web",
                "commit": sha,
                "dirty": dirty,
                "files": sorted(str(p) for p in files),
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps({"exported_files": len(files), "origin_commit": sha, "dirty": dirty})
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True, type=Path)
    export(p.parse_args().output)
