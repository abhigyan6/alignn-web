"""Byte-aware JSON chunks. ZIP members are verified in memory, never extracted."""

import hashlib
import io
import json
import re
import stat
import zipfile
from datetime import datetime, timedelta

from .models import SourceResult
from .registry import SOURCES

CHUNK = 1024 * 1024
MAX_ZIP = 85 * 1024 * 1024
MAX_TOTAL = 80 * 1024 * 1024


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_bundle(results, now):
    manifest = {"schema_version": 1, "generated_at": now.isoformat(), "sources": [], "chunks": []}
    files = {}
    for result in results:
        result = SourceResult.model_validate(result)
        report = result.model_dump(mode="json", exclude={"records"})
        report["accepted"] = len(result.records)
        manifest["sources"].append(report)
        batch = []

        def flush():
            if not batch:
                return
            name = f"{result.source}-{len(files):03}.json"
            content = json_bytes(batch)
            if len(content) > CHUNK:
                raise ValueError("row_exceeds_chunk")
            files[name] = content
            manifest["chunks"].append(
                {
                    "name": name,
                    "source": result.source,
                    "size": len(content),
                    "sha256": digest(content),
                    "count": len(batch),
                }
            )
            batch.clear()

        for row in result.records:
            value = row.model_dump(mode="json")
            if batch and (len(batch) >= 100 or len(json_bytes([*batch, value])) > CHUNK):
                flush()
            batch.append(value)
        flush()
    files["manifest.json"] = json_bytes(manifest)
    # Stored compression avoids highly repetitive legitimate descriptions tripping ratio guards.
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as z:
        for name, content in files.items():
            z.writestr(name, content)
    packed = output.getvalue()
    if len(packed) > MAX_ZIP:
        raise ValueError("bundle_exceeds_download_limit")
    read_bundle(packed, now)
    return packed


def read_bundle(data, now):
    if len(data) > MAX_ZIP:
        raise ValueError("download_too_large")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            infos = z.infolist()
            names = [i.filename for i in infos]
            if len(infos) > 128 or len(set(names)) != len(names) or "manifest.json" not in names:
                raise ValueError("invalid_members")
            if sum(i.file_size for i in infos) > MAX_TOTAL:
                raise ValueError("uncompressed_too_large")
            for i in infos:
                if (
                    not re.fullmatch(r"[a-z0-9-]+\.json", i.filename)
                    or stat.S_ISLNK(i.external_attr >> 16)
                    or i.flag_bits & 1
                    or i.file_size > max(1, i.compress_size) * 100
                    or i.file_size > (256 * 1024 if i.filename == "manifest.json" else CHUNK)
                ):
                    raise ValueError("unsafe_zip_member")
            manifest = json.loads(z.read("manifest.json"))
            if (
                set(manifest) != {"schema_version", "generated_at", "sources", "chunks"}
                or manifest["schema_version"] != 1
            ):
                raise ValueError("unsupported_envelope")
            generated = datetime.fromisoformat(manifest["generated_at"].replace("Z", "+00:00"))
            if generated.tzinfo is None or not now - timedelta(
                hours=24
            ) <= generated <= now + timedelta(minutes=5):
                raise ValueError("stale_envelope")
            if not isinstance(manifest["sources"], list) or not 1 <= len(manifest["sources"]) <= 8:
                raise ValueError("source_count")
            parts = {}
            for report in manifest["sources"]:
                key = report["source"]
                if key in parts or key not in SOURCES or SOURCES[key].status != "enabled":
                    raise ValueError("unsupported_source")
                # Row validation happens atomically per source at import, not incrementally here.
                if set(report) != {
                    "source",
                    "status",
                    "checked_at",
                    "skipped",
                    "failed",
                    "errors",
                    "accepted",
                }:
                    raise ValueError("invalid_report")
                checked = datetime.fromisoformat(report["checked_at"].replace("Z", "+00:00"))
                if (
                    checked.tzinfo is None
                    or not generated - timedelta(hours=24) <= checked <= generated
                ):
                    raise ValueError("invalid_check_time")
                if type(report["accepted"]) is not int or not 0 <= report["accepted"] <= 100:
                    raise ValueError("record_count")
                parts[key] = {k: v for k, v in report.items() if k != "accepted"}
                parts[key]["records"] = []
            seen = set()
            for chunk in manifest["chunks"]:
                if set(chunk) != {"name", "source", "size", "sha256", "count"}:
                    raise ValueError("invalid_chunk")
                name = chunk["name"]
                key = chunk["source"]
                if name == "manifest.json" or name in seen or key not in parts:
                    raise ValueError("chunk_identity")
                seen.add(name)
                content = z.read(name)
                if len(content) != chunk["size"] or digest(content) != chunk["sha256"]:
                    raise ValueError("chunk_integrity")
                rows = json.loads(content)
                if not isinstance(rows, list) or len(rows) != chunk["count"] or len(rows) > 100:
                    raise ValueError("chunk_count")
                parts[key]["records"].extend(rows)
            if set(names) != seen | {"manifest.json"}:
                raise ValueError("unexpected_member")
            for report in manifest["sources"]:
                if len(parts[report["source"]]["records"]) != report["accepted"]:
                    raise ValueError("source_count_mismatch")
            return manifest, parts
    except (KeyError, TypeError, OverflowError, zipfile.BadZipFile, UnicodeError) as e:
        raise ValueError("invalid_bundle") from e
