"""Sanitized database acknowledgement and capacity view. Never prints configuration."""

import json

from alignn.db import engine
from sqlalchemy import text

QUERIES = {
    "sources": """SELECT source_name,status,count(*) AS records,max(source_checked_at) AS last_verified,
                  max(source_imported_at) AS last_imported FROM opportunities WHERE mode='EXTERNAL'
                  GROUP BY source_name,status ORDER BY source_name,status""",
    "jobs": """SELECT kind,status,count(*) AS records, min(run_at) AS oldest_due FROM jobs
               WHERE kind IN ('poll_scraper','import_scraper','recheck_scraper') GROUP BY kind,status""",
    "receipts": """SELECT source,state,count(*) AS records,max(applied_at) AS last_applied
                   FROM scraper_import_receipts GROUP BY source,state""",
    "capacity": """SELECT (SELECT count(*) FROM opportunities) AS opportunities,
                          (SELECT count(*) FROM match_snapshots) AS matches,
                          pg_total_relation_size('opportunities') AS catalog_bytes,
                          pg_total_relation_size('match_snapshots') AS match_bytes""",
}
with engine.connect() as c:
    result = {
        key: [dict(r) for r in c.execute(text(query)).mappings()] for key, query in QUERIES.items()
    }
print(json.dumps(result, default=str, indent=2))
