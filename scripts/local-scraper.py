"""Run one local scraper service using existing gh authentication, never token output."""

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("service", choices=["scheduler", "maintenance", "collection"])
    args = p.parse_args()
    env = {
        **os.environ,
        "SCRAPER_SYNC_ENABLED": "true",
        "SCRAPER_AUTH_MODE": "cli",
        "SCRAPER_REPOSITORY": "abhigyan6/alignn-scraper",
        "SCRAPER_REPOSITORY_ID": "1453961313",
        "SCRAPER_WORKFLOW_ID": "414656784",
        "PYTHONPATH": str(ROOT / "apps/api/src"),
    }
    command = [
        str(ROOT / "apps/api/.venv/bin/python"),
        "-m",
        "alignn.jobs.scheduler" if args.service == "scheduler" else "alignn.jobs.worker",
    ]
    if args.service != "scheduler":
        command += ["--lane", args.service]
    os.chdir(ROOT)
    os.execve(command[0], command, env)


if __name__ == "__main__":
    main()
