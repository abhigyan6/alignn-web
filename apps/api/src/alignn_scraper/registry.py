"""Reviewed public origins and paths; input cannot choose an arbitrary fetch URL."""

import re
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Source:
    name: str
    status: str
    indexes: tuple[str, ...] = ()
    note: str = ""


SOURCES = {
    "hackindia": Source("HackIndia", "enabled", ("https://hackindia.org/hackathons",)),
    "luma": Source(
        "Luma",
        "enabled",
        tuple("https://luma.com/" + city for city in ("bengaluru", "new-delhi", "mumbai")),
    ),
    "devfolio": Source("Devfolio", "enabled", ("https://devfolio.co/hackathons",)),
    **{
        f"greenhouse-{board}": Source(
            f"Greenhouse:{board}",
            "enabled",
            (f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true",),
        )
        for board in ("stripe", "figma", "razorpaysoftwareprivatelimited")
    },
    "unstop": Source(
        "Unstop",
        "blocked",
        note="Public catalog returned a JavaScript/cookie shell; no verified allowed extraction contract.",
    ),
    "hack2skill": Source(
        "Hack2skill",
        "needs_verification",
        note="Public listing/detail returned a JavaScript shell.",
    ),
    "konfhub": Source(
        "KonfHub", "needs_verification", note="Public events HTML has no verified catalog contract."
    ),
}
BOARDS = {
    "stripe": ("Stripe", {"stripe.com"}),
    "figma": ("Figma", {"job-boards.greenhouse.io", "boards.greenhouse.io"}),
    "razorpaysoftwareprivatelimited": (
        "Razorpay",
        {"job-boards.greenhouse.io", "boards.greenhouse.io"},
    ),
}
LUMA_SEEDS = ("https://luma.com/wrnbcpzs", "https://luma.com/xnypxxpv")
SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"


def validate_url(source, url, *, fetch=False):
    if (
        source not in SOURCES
        or SOURCES[source].status != "enabled"
        or not isinstance(url, str)
        or len(url) > 1000
    ):
        raise ValueError("unsupported_source_url")
    p = urlsplit(url)
    if (
        p.scheme != "https"
        or p.username
        or p.password
        or p.port not in (None, 443)
        or p.fragment
        or "\\" in url
        or any(ord(c) < 33 for c in url)
    ):
        raise ValueError("unsafe_source_url")
    host = p.hostname
    path = p.path
    if source == "hackindia":
        valid = (
            host == "hackindia.org"
            and not p.query
            and (path == "/hackathons" or bool(re.fullmatch(r"/20\d{2}/" + SLUG, path)))
        )
    elif source == "luma":
        valid = host == "luma.com" and not p.query and bool(re.fullmatch("/" + SLUG, path))
        valid = valid and path not in {
            "/login",
            "/signup",
            "/terms",
            "/privacy",
            "/discover",
            "/user",
            "/home",
        }
    elif source == "devfolio":
        valid = not p.query and (
            (host == "devfolio.co" and path == "/hackathons")
            or bool(re.fullmatch(SLUG + r"\.devfolio\.co", host or ""))
            and path == "/"
        )
    else:
        board = source.removeprefix("greenhouse-")
        valid = (
            (
                host == "boards-api.greenhouse.io"
                and path == f"/v1/boards/{board}/jobs"
                and p.query == "content=true"
            )
            if fetch
            else (host in BOARDS[board][1] and (host != "stripe.com" or path.startswith("/jobs/")))
        )
    if not valid:
        raise ValueError("unsafe_source_url")
    return url
