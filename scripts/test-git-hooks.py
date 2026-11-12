import json
import secrets
import shutil
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="alignn-hooks-") as folder:
    p = Path(folder)

    def run(args, check=True):
        r = subprocess.run(args, cwd=p, text=True, capture_output=True, check=False)
        if check and r.returncode:
            raise RuntimeError("Command failed: " + args[0] + "; code=" + str(r.returncode))
        return r

    run(["git", "init", "-q"])
    run(["git", "config", "user.email", "hooks@alignn.test"])
    run(["git", "config", "user.name", "Hook Test"])
    (p / "node_modules").symlink_to(root / "node_modules", target_is_directory=True)
    for name in ["eslint.config.mjs", "lint-staged.config.mjs", ".gitignore"]:
        shutil.copyfile(root / name, p / name)
    (p / "package.json").write_text('{"type":"module"}\n')
    run(
        [
            "git",
            "add",
            "--",
            ".gitignore",
            "package.json",
            "eslint.config.mjs",
            "lint-staged.config.mjs",
        ]
    )
    run(["git", "commit", "-qm", "test: establish temporary fixture"])
    f = p / "probe.ts"
    f.write_text("export const answer=1\n")
    run(["git", "add", "probe.ts"])
    f.write_text(f.read_text() + "// Preserve this unstaged note.\n")
    hook = run(["sh", str(root / ".githooks/pre-commit")])
    staged = run(["git", "show", ":probe.ts"]).stdout
    assert staged == "export const answer = 1;\n"
    assert "Preserve this unstaged note." in f.read_text()
    assert "Preserve this unstaged note." not in staged
    # A variable that is never read must fail linting.
    f.write_text("const neverRead = 1;\nexport {};\n")
    run(["git", "add", "probe.ts"])
    assert run(["sh", str(root / ".githooks/pre-commit")], False).returncode != 0
    # A synthetic token exercises detection; never print it or scanner matches.
    f.write_text(
        'export const probe = "'
        + "ghp_"
        + "".join(
            secrets.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
            for _ in range(36)
        )
        + '";\n'
    )
    run(["git", "add", "probe.ts"])
    assert run(["sh", str(root / ".githooks/pre-commit")], False).returncode != 0
    (p / "other/node_modules").mkdir(parents=True)
    ignored = [
        ".env",
        "apps/web/.env.local",
        "dist/test.js",
        "other/node_modules/test.js",
        ".DS_Store",
        ".vscode/settings.json",
        "build/file.js",
        "test-results/test.txt",
        "local.key",
    ]
    for name in ignored:
        assert run(["git", "check-ignore", name], False).returncode == 0, name
    assert run(["git", "check-ignore", ".env.example"], False).returncode == 1
    assert run(["git", "check-ignore", "apps/web/.env.example"], False).returncode == 1
    print(
        json.dumps(
            {
                "format_staged": True,
                "unstaged_hunks_preserved": True,
                "lint_rejects_error": True,
                "synthetic_secret_rejected": True,
                "ignore_patterns": True,
                "example_files_allowed": True,
            }
        )
    )
