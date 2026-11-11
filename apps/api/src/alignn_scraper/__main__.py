import argparse
import json
from pathlib import Path

from .bundle import read_bundle, write_bundle
from .collect import collect
from .models import SourceResult, now_utc
from .registry import SOURCES


def main():
    parser = argparse.ArgumentParser(
        description="Public India-first opportunity collection, no database access"
    )
    parser.add_argument(
        "--source",
        choices=["all", *[k for k, s in SOURCES.items() if s.status == "enabled"]],
        default="all",
    )
    parser.add_argument("--output", type=Path, default=Path("output/opportunities.zip"))
    parser.add_argument("--merge", nargs="+", type=Path)
    args = parser.parse_args()
    now = now_utc()
    if args.merge:
        sources = {}
        for file in args.merge:
            _, parts = read_bundle(file.read_bytes(), now)
            for key, part in parts.items():
                if key in sources:
                    raise ValueError("duplicate_source_partition")
                sources[key] = SourceResult.model_validate(part)
        results = list(sources.values())
    else:
        results = [
            collect(key)
            for key, s in SOURCES.items()
            if s.status == "enabled" and args.source in {"all", key}
        ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(write_bundle(results, now_utc()))
    report = {
        "sources": [
            dict(
                source=r.source,
                status=r.status,
                accepted=len(r.records),
                skipped=r.skipped,
                failed=r.failed,
                errors=r.errors,
            )
            for r in results
        ],
        "unavailable": {k: s.status for k, s in SOURCES.items() if s.status != "enabled"},
    }
    print(json.dumps(report, sort_keys=True))
    return 1 if all(r.status == "failed" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
