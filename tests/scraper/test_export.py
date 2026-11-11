import subprocess
import sys
from pathlib import Path


def test_export_contains_only_standalone_files(tmp_path):
    root = Path(__file__).resolve().parents[2]
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/export-scraper.py"),
            "--output",
            str(tmp_path / "bot"),
        ],
        check=True,
        capture_output=True,
    )
    target = tmp_path / "bot"
    assert (target / "src/alignn_scraper/__main__.py").is_file()
    assert not (target / "src/alignn").exists()
    assert not list(target.rglob(".env*"))
    assert not (target / ".git").exists()
    for file in target.glob("src/**/*.py"):
        assert "from alignn." not in file.read_text() and "import alignn." not in file.read_text()
    workflow = (target / ".github/workflows/scrape.yml").read_text()
    assert "workflow_dispatch:" in workflow and "contents: read" in workflow
    assert "persist-credentials: false" in workflow and "retention-days: 7" in workflow
    assert "DATABASE_URL" not in workflow and "max-parallel: 2" in workflow
