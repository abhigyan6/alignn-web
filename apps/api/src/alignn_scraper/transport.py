"""Bounded identified public HTTP, robots, no redirects or arbitrary origins."""

import ipaddress
import socket
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from .registry import validate_url

USER_AGENT = "AlignnOpportunityBot/1.0 (+https://github.com/abhigyan6/alignn-scraper; public career discovery)"


class FetchError(ValueError):
    def __init__(self, code, status=None, retry_after=None):
        super().__init__(code)
        self.code = code
        self.status = status
        self.retry_after = retry_after


class PublicHTTP:
    def __init__(self, source, client=None, delay=1):
        self.source = source
        self.client = client or httpx.Client(follow_redirects=False, timeout=15, trust_env=False)
        self.owns = client is None
        self.delay = delay
        self.started = time.monotonic()
        self.last = {}
        self.robots = {}
        self.requests = 0

    def close(self):
        if self.owns:
            self.client.close()

    def _request(self, url, limit=2 * 1024 * 1024):
        host = urlsplit(url).hostname
        for attempt in range(2):
            elapsed = time.monotonic() - self.started
            if elapsed >= 180 or self.requests >= 110:
                raise FetchError("source_budget_exhausted")
            wait = max(0, self.delay - (time.monotonic() - self.last.get(host, 0)))
            if elapsed + wait >= 180:
                raise FetchError("source_budget_exhausted")
            time.sleep(wait)
            self.requests += 1
            self.last[host] = time.monotonic()
            if self.owns:
                try:
                    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
                except OSError as exc:
                    raise FetchError("network_failure") from exc
                if not addresses or any(
                    not ipaddress.ip_address(a[4][0]).is_global for a in addresses
                ):
                    raise FetchError("unsafe_address")
            try:
                with self.client.stream(
                    "GET",
                    url,
                    headers={"User-Agent": USER_AGENT},
                    follow_redirects=False,
                    timeout=min(15, max(0.1, 180 - (time.monotonic() - self.started))),
                ) as r:
                    if r.status_code == 429 or r.status_code >= 500:
                        if not attempt and r.status_code != 429:
                            continue
                        after = r.headers.get("retry-after", "")
                        raise FetchError(
                            "rate_limited" if r.status_code == 429 else "upstream_failure",
                            r.status_code,
                            int(after) if after.isdigit() else None,
                        )
                    if r.status_code != 200:
                        raise FetchError("http_status", r.status_code)
                    data = bytearray()
                    for chunk in r.iter_bytes():
                        data.extend(chunk)
                        if len(data) > limit or time.monotonic() - self.started >= 180:
                            raise FetchError("response_limit")
                    return bytes(data).decode("utf-8")
            except httpx.HTTPError as e:
                if attempt:
                    raise FetchError("network_failure") from e
        raise FetchError("network_failure")

    def get(self, url):
        validate_url(self.source, url, fetch=True)
        parsed = urlsplit(url)
        origin = f"https://{parsed.hostname}"
        if origin not in self.robots:
            try:
                body = self._request(origin + "/robots.txt", 256 * 1024)
            except FetchError as e:
                if e.status in {404, 410}:
                    body = "User-agent: *\nAllow: /"
                else:
                    raise
            rules = RobotFileParser()
            rules.parse(body.splitlines())
            self.robots[origin] = rules
        if not self.robots[origin].can_fetch(USER_AGENT, url):
            raise FetchError("robots_disallowed")
        return self._request(
            url, 20 * 1024 * 1024 if self.source.startswith("greenhouse-") else 2 * 1024 * 1024
        )
