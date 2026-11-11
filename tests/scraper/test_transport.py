import httpx
import pytest
from alignn_scraper.transport import FetchError, PublicHTTP


def test_robots_disallow_and_redirect_are_not_followed():
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, text="User-agent: *\nDisallow: /2026/\n")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        http = PublicHTTP("hackindia", client=client, delay=0)
        with pytest.raises(FetchError):
            http.get("https://hackindia.org/2026/test")
    assert calls == ["/robots.txt"]

    def redirect(request):
        return (
            httpx.Response(404)
            if request.url.path == "/robots.txt"
            else httpx.Response(302, headers={"location": "http://127.0.0.1"})
        )

    with httpx.Client(transport=httpx.MockTransport(redirect)) as client:
        with pytest.raises(FetchError):
            PublicHTTP("hackindia", client=client, delay=0).get("https://hackindia.org/hackathons")


def test_response_and_request_count_limits():
    def large(request):
        return (
            httpx.Response(404)
            if request.url.path == "/robots.txt"
            else httpx.Response(200, content=b"x" * (2 * 1024 * 1024 + 1))
        )

    with httpx.Client(transport=httpx.MockTransport(large)) as client:
        with pytest.raises(FetchError):
            PublicHTTP("hackindia", client=client, delay=0).get("https://hackindia.org/hackathons")


def test_dns_failure_is_a_controlled_source_failure(monkeypatch):
    import socket

    def broken(*args, **kwargs):
        raise socket.gaierror("fixture DNS failure")

    monkeypatch.setattr(socket, "getaddrinfo", broken)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200))) as client:
        http = PublicHTTP("hackindia", client=client, delay=0)
        http.owns = True
        with pytest.raises(FetchError):
            http.get("https://hackindia.org/hackathons")
