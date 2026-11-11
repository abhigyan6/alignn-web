import json
import re
import time
from urllib.parse import urljoin

from .models import SourceResult, now_utc
from .parsers import Page, parse_devfolio, parse_greenhouse, parse_hackindia, parse_luma
from .registry import LUMA_SEEDS, SOURCES, validate_url
from .transport import FetchError, PublicHTTP


def collect(source):
    spec = SOURCES[source]
    http = PublicHTTP(source)
    records = []
    skipped = failed = 0
    errors = set()
    try:
        urls = []
        if source.startswith("greenhouse-"):
            data = json.loads(http.get(spec.indexes[0]))
            jobs = data["jobs"]
            if not isinstance(jobs, list) or len(jobs) != data.get("meta", {}).get("total"):
                raise ValueError("incomplete_board")
            if len({str(x["id"]) for x in jobs}) != len(jobs):
                raise ValueError("duplicate_source_identity")
            for raw in jobs:
                value = parse_greenhouse(raw, source.removeprefix("greenhouse-"), now_utc())
                if value:
                    records.append(value)
                else:
                    skipped += 1
        else:
            for index in spec.indexes:
                body = http.get(index)
                page = Page(body)
                if source == "devfolio":
                    queries = page.next_data()["dehydratedState"]["queries"]
                    lists = [
                        q["state"]["data"]["open_hackathons"]
                        for q in queries
                        if q.get("queryKey")
                        in ("fetchAllHackathonTypes", ["fetchAllHackathonTypes"])
                    ]
                    if len(lists) != 1:
                        raise ValueError("catalog_structure_changed")
                    urls.extend(f"https://{raw['slug']}.devfolio.co/" for raw in lists[0])
                elif source == "hackindia":
                    urls.extend(
                        urljoin(index, u)
                        for u in page.links
                        if re.fullmatch(r"/20\d{2}/[a-z0-9-]+", u)
                    )
                else:
                    data = page.next_data()["initialData"]["data"]
                    # Only metadata candidates; no user/guest fields copied.
                    urls.extend(
                        "https://luma.com/" + entry["event"]["url"]
                        for entry in data["events"]
                        if re.search(
                            r"\b(hackathon|buildathon|workshop|developer|tech|coding|ai|startup|founder|engineer|career)\b",
                            entry["event"]["name"],
                            re.I,
                        )
                    )
            if source == "luma":
                urls.extend(LUMA_SEEDS)
            urls = list(dict.fromkeys(urls))
            if not urls:
                raise ValueError("catalog_empty_unverified")
            if len(urls) > 100:
                errors.add("detail_budget_exhausted")
            for url in urls[:100]:
                if time.monotonic() - http.started > 160:
                    errors.add("source_budget_exhausted")
                    failed += 1
                    break
                try:
                    validate_url(source, url)
                    body = http.get(url)
                    value = {
                        "hackindia": parse_hackindia,
                        "luma": parse_luma,
                        "devfolio": parse_devfolio,
                    }[source](body, url, now_utc())
                    if value:
                        records.append(value)
                    else:
                        skipped += 1
                except (ValueError, KeyError, TypeError) as e:
                    failed += 1
                    errors.add(e.code if isinstance(e, FetchError) else "detail_validation_failed")
                    if isinstance(e, FetchError) and (
                        e.status in {403, 429}
                        or e.code in {"robots_disallowed", "source_budget_exhausted"}
                    ):
                        break
        if len(records) > 100:
            raise ValueError("source_record_limit")
        # Canonical URLs may repeat across city indexes. Stable IDs must be consistent.
        by_id = {}
        for row in records:
            if row.source_id in by_id and row.source_url != by_id[row.source_id].source_url:
                raise ValueError("duplicate_source_identity")
            by_id[row.source_id] = row
        records = list(by_id.values())
        status = "partial" if errors else "ok" if records else "empty"
    except (ValueError, KeyError, TypeError) as e:
        errors.add(e.code if isinstance(e, FetchError) else "source_validation_failed")
        status = "partial" if records else "failed"
        failed += 1
    finally:
        http.close()
    return SourceResult(
        source=source,
        status=status,
        checked_at=now_utc(),
        records=records,
        skipped=skipped,
        failed=failed,
        errors=sorted(errors),
    )
