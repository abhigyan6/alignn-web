# Core career discovery: first live source

Implemented locally: Remotive public API ingestion through the Python worker, six-hour scheduling, source identity uniqueness, source attribution, plain-text descriptions, safe snapshot validation, updates and closure of missing listings. Imported listings have unknown dates rather than synthetic deadlines. They do not claim verified structured eligibility. The feed organization is not marked verified.

Source documentation: https://github.com/remotive-com/remote-jobs-api . Listings must remain publicly viewable, link back to the supplied Remotive URL, and display attribution. Do not syndicate this data to other third-party job boards. The public feed is delayed by 24 hours. Recheck source terms before public launch.

Run from the active checkout:

```sh
PYTHONPATH=apps/api/src apps/api/.venv/bin/python -m alembic -c apps/api/alembic.ini upgrade head
PYTHONPATH=apps/api/src apps/api/.venv/bin/python -m alignn.domains.opportunities.ingestion
PYTHONPATH=apps/api/src apps/api/.venv/bin/python -m alignn.jobs.worker
PYTHONPATH=apps/api/src apps/api/.venv/bin/python -m alignn.jobs.scheduler
```

The local scheduler needs to remain running; nothing is deployed to AWS. Worker jobs use existing leases and bounded retries. Successful syncs throttle using their last source-check timestamp; failed attempts use existing worker backoff. Incomplete or empty responses preserve the previous catalog. Source provenance does not imply an employer endorsement.

Explore defaults to profile match, polls pending rankings, and keeps anonymous discovery available. Detail pages expose the existing deterministic fit factors and source application links. Existing saves and manual external tracking remain available. Profile-interest matching uses case-insensitive tokens.

Remaining core work: event/hackathon and additional internship sources, resume text extraction with user-confirmed profile changes, fuller career guidance, and end-to-end testing of the complete onboarding-to-application journey. Remote work mode does not prove a role accepts candidates from India; users must confirm the listing's geographic requirements. No claim of full original-product parity.
