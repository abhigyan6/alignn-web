"""Trusted Actions artifact delivery. Authenticated API and signed storage are separate."""

import io
import json
import re
import subprocess
import zipfile
from datetime import timedelta
from urllib.parse import urlsplit

import httpx
from alignn_scraper.bundle import MAX_ZIP, digest

API = "https://api.github.com"
ARTIFACT = "alignn-opportunities-v1"


def download_host_allowed(url):
    p = urlsplit(url)
    host = p.hostname or ""
    return (
        p.scheme == "https"
        and not p.username
        and not p.password
        and p.port in {None, 443}
        and (
            host.endswith(".blob.core.windows.net")
            or host.endswith(".actions.githubusercontent.com")
        )
    )


def trusted_run(run, *, repository_id, workflow_id, branch, workflow_path):
    return (
        run.get("repository", {}).get("id") == repository_id
        and run.get("head_repository", {}).get("id") == repository_id
        and run.get("workflow_id") == workflow_id
        and run.get("head_branch") == branch
        and run.get("path") == workflow_path
        and run.get("event") in {"workflow_dispatch", "schedule"}
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
    )


class GitHubReader:
    def __init__(self, repository, *, http=None, token=None, cli=False):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError("invalid_repository")
        self.repository = repository
        self.http = http or httpx.Client(timeout=30, follow_redirects=False, trust_env=False)
        self.token = token
        self.cli = cli
        self.owns = http is None

    def close(self):
        if self.owns:
            self.http.close()

    def _gh(self, path, limit):
        # gh owns local authentication. Its token/cache contents are never read or returned.
        with subprocess.Popen(
            ["gh", "api", "--hostname", "github.com", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ) as p:
            data = bytearray()
            try:
                import selectors
                import time

                with selectors.DefaultSelector() as selector:
                    selector.register(p.stdout, selectors.EVENT_READ)
                    end = time.monotonic() + 120
                    while True:
                        if time.monotonic() > end:
                            raise ValueError("github_timeout")
                        if not selector.select(timeout=1):
                            continue
                        chunk = p.stdout.read1(65536)
                        if not chunk:
                            break
                        data.extend(chunk)
                        if len(data) > limit:
                            raise ValueError("github_response_limit")
                if p.wait(timeout=5) != 0:
                    raise ValueError("github_access_failed")
            except BaseException:
                p.kill()
                p.wait()
                raise
        return bytes(data)

    def _headers(self):
        if not self.token:
            raise ValueError("github_access_missing")
        return {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get(self, path):
        route = f"repos/{self.repository}/{path}" if path else f"repos/{self.repository}"
        if self.cli:
            return json.loads(self._gh(route, 4 * 1024 * 1024))
        with self.http.stream(
            "GET", API + "/" + route, headers=self._headers(), follow_redirects=False
        ) as r:
            if r.status_code != 200:
                raise ValueError("github_metadata_failed")
            data = bytearray()
            for chunk in r.iter_bytes():
                data.extend(chunk)
                if len(data) > 4 * 1024 * 1024:
                    raise ValueError("github_response_limit")
        return json.loads(data)

    def download(self, artifact_id):
        if type(artifact_id) is not int or artifact_id <= 0:
            raise ValueError("invalid_artifact_id")
        route = f"repos/{self.repository}/actions/artifacts/{artifact_id}/zip"
        if self.cli:
            return self._gh(route, MAX_ZIP + 1024 * 1024)
        # Do not follow the authenticated redirect automatically or persist/log its signed URL.
        r = self.http.get(API + "/" + route, headers=self._headers(), follow_redirects=False)
        location = r.headers.get("location", "")
        if r.status_code != 302 or not download_host_allowed(location):
            raise ValueError("unsafe_artifact_redirect")
        data = bytearray()
        with self.http.stream("GET", location, follow_redirects=False, headers={}) as response:
            if response.status_code != 200:
                raise ValueError("artifact_download_failed")
            for chunk in response.iter_bytes():
                data.extend(chunk)
                if len(data) > MAX_ZIP + 1024 * 1024:
                    raise ValueError("artifact_too_large")
        return bytes(data)


def reader_from_settings(settings):
    if not settings.scraper_sync_enabled:
        raise ValueError("scraper_sync_disabled")
    return GitHubReader(
        settings.scraper_repository,
        cli=settings.scraper_auth_mode == "cli",
        token=settings.scraper_github_token.get_secret_value()
        if settings.scraper_github_token
        else None,
    )


def unwrap_artifact(packed, expected_digest):
    if (
        not re.fullmatch(r"sha256:[a-f0-9]{64}", expected_digest or "")
        or digest(packed) != expected_digest[7:]
    ):
        raise ValueError("artifact_digest_mismatch")
    if len(packed) > MAX_ZIP + 1024 * 1024:
        raise ValueError("artifact_too_large")
    with zipfile.ZipFile(io.BytesIO(packed)) as z:
        infos = z.infolist()
        if (
            len(infos) != 1
            or infos[0].filename != "opportunities.zip"
            or infos[0].file_size > MAX_ZIP
            or infos[0].file_size > max(1, infos[0].compress_size) * 100
        ):
            raise ValueError("invalid_artifact_wrapper")
        return z.read(infos[0])


def _poll(settings):
    from alignn.db import SessionLocal, utcnow
    from alignn.jobs.worker import enqueue_job

    from .ingestion_models import ScraperCursor

    reader = reader_from_settings(settings)
    now = utcnow()
    discovered = 0
    try:
        repo = reader.get("")
        workflow = reader.get(f"actions/workflows/{settings.scraper_workflow_id}")
        if (
            repo.get("id") != settings.scraper_repository_id
            or not repo.get("private")
            or repo.get("default_branch") != settings.scraper_branch
            or workflow.get("path") != settings.scraper_workflow_path
        ):
            raise ValueError("github_identity_mismatch")
        page = 1
        while True:
            payload = reader.get(
                f"actions/workflows/{settings.scraper_workflow_id}/runs?per_page=100&page={page}&status=completed"
            )
            runs = payload["workflow_runs"]
            for run in runs:
                if not trusted_run(
                    run,
                    repository_id=settings.scraper_repository_id,
                    workflow_id=settings.scraper_workflow_id,
                    branch=settings.scraper_branch,
                    workflow_path=settings.scraper_workflow_path,
                ):
                    continue
                from datetime import datetime

                created = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                if created < now - timedelta(hours=24):
                    continue
                artifact_page = 1
                while True:
                    artifacts = reader.get(
                        f"actions/runs/{run['id']}/artifacts?per_page=100&page={artifact_page}"
                    )["artifacts"]
                    for artifact in artifacts:
                        if artifact.get("name") != ARTIFACT or artifact.get("expired"):
                            continue
                        if not re.fullmatch(r"sha256:[a-f0-9]{64}", artifact.get("digest", "")):
                            raise ValueError("artifact_digest_missing")
                        identity = dict(
                            repository_id=repo["id"],
                            workflow_id=run["workflow_id"],
                            run_id=run["id"],
                            run_attempt=run["run_attempt"],
                            artifact_id=artifact["id"],
                        )
                        with SessionLocal.begin() as db:
                            enqueue_job(
                                db,
                                kind="import_scraper",
                                key=f"scraper-{run['id']}-{run['run_attempt']}-{artifact['id']}",
                                payload={"identity": identity, "digest": artifact["digest"]},
                                run_at=now,
                                expires_at=created + timedelta(hours=24),
                            )
                        discovered += 1
                    if len(artifacts) < 100:
                        break
                    artifact_page += 1
            # No application cursor can skip pending work: jobs are durable before this watermark.
            with SessionLocal.begin() as db:
                from sqlalchemy.dialects.postgresql import insert

                db.execute(
                    insert(ScraperCursor)
                    .values(
                        key="github-enumeration",
                        value={"page": page, "checked_at": now.isoformat()},
                    )
                    .on_conflict_do_update(
                        index_elements=["key"],
                        set_={"value": {"page": page, "checked_at": now.isoformat()}},
                    )
                )
            if len(runs) < 100 or (
                runs and runs[-1]["created_at"] < (now - timedelta(hours=24)).isoformat()
            ):
                break
            page += 1
            if page > 100:
                raise ValueError("github_enumeration_budget")
        return discovered
    finally:
        reader.close()


def import_artifact(settings, payload):
    from alignn.db import SessionLocal

    from .import_scraped import ensure_receipt, import_bundle

    reader = reader_from_settings(settings)
    identity = payload["identity"]
    try:
        run = reader.get(f"actions/runs/{identity['run_id']}")
        if (
            not trusted_run(
                run,
                repository_id=settings.scraper_repository_id,
                workflow_id=settings.scraper_workflow_id,
                branch=settings.scraper_branch,
                workflow_path=settings.scraper_workflow_path,
            )
            or run["run_attempt"] != identity["run_attempt"]
        ):
            raise ValueError("untrusted_run")
        metadata = reader.get(f"actions/artifacts/{identity['artifact_id']}")
        if (
            metadata.get("workflow_run", {}).get("id") != identity["run_id"]
            or metadata.get("name") != ARTIFACT
            or metadata.get("digest") != payload["digest"]
            or metadata.get("expired")
        ):
            raise ValueError("untrusted_artifact")
        with SessionLocal.begin() as db:
            receipt = ensure_receipt(db, identity, "__artifact__", payload["digest"][7:])
            if receipt.state in {"APPLIED", "REJECTED"}:
                return receipt.counts
        packed = reader.download(identity["artifact_id"])
        bundle = unwrap_artifact(packed, payload["digest"])
        outcome = import_bundle(bundle, identity=identity)
        with SessionLocal.begin() as db:
            receipt = ensure_receipt(db, identity, "__artifact__", payload["digest"][7:])
            receipt.state = "APPLIED"
            receipt.counts = outcome
        return outcome
    except Exception:
        # Values/errors from providers may contain signed URLs. Store only a fixed code.
        from sqlalchemy import select

        from alignn.jobs.models import Job

        with SessionLocal.begin() as db:
            receipt = ensure_receipt(db, identity, "__artifact__", payload["digest"][7:])
            job = db.scalar(
                select(Job).where(
                    Job.key
                    == f"scraper-{identity['run_id']}-{identity['run_attempt']}-{identity['artifact_id']}"
                )
            )
            if receipt.state not in {"APPLIED", "REJECTED"}:
                receipt.state = "FAILED" if job and job.attempts >= 5 else "RETRYABLE"
                receipt.error = "artifact_delivery_failed"
        raise
    finally:
        reader.close()


def poll(settings):
    """Durable backoff applies to new minute jobs as well as retries of one job."""
    from datetime import datetime

    from sqlalchemy import select
    from sqlalchemy.dialects.postgresql import insert

    from alignn.db import SessionLocal, utcnow

    from .ingestion_models import ScraperCursor

    now = utcnow()
    with SessionLocal.begin() as db:
        db.execute(
            insert(ScraperCursor)
            .values(key="github-poll-state", value={})
            .on_conflict_do_nothing(index_elements=["key"])
        )
        cursor = db.scalar(
            select(ScraperCursor).where(ScraperCursor.key == "github-poll-state").with_for_update()
        )
        if cursor.value.get("next_at") and datetime.fromisoformat(cursor.value["next_at"]) > now:
            return 0
        previous = cursor.value
        cursor.value = {**previous, "next_at": (now + timedelta(minutes=2)).isoformat()}
    try:
        count = _poll(settings)
    except Exception:
        with SessionLocal.begin() as db:
            cursor = db.scalar(
                select(ScraperCursor)
                .where(ScraperCursor.key == "github-poll-state")
                .with_for_update()
            )
            failures = min(10, int(previous.get("failures", 0)) + 1)
            cursor.value = {
                "failures": failures,
                "next_at": (utcnow() + timedelta(seconds=min(3600, 60 * 2**failures))).isoformat(),
                "last_failure_at": utcnow().isoformat(),
                "error": "github_poll_failed",
            }
        raise
    with SessionLocal.begin() as db:
        cursor = db.scalar(
            select(ScraperCursor).where(ScraperCursor.key == "github-poll-state").with_for_update()
        )
        cursor.value = {
            "failures": 0,
            "next_at": (utcnow() + timedelta(seconds=60)).isoformat(),
            "last_success_at": utcnow().isoformat(),
        }
    return count
