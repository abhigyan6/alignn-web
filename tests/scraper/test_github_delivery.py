import httpx
from alignn.domains.opportunities.github_sync import (
    GitHubReader,
    download_host_allowed,
    trusted_run,
)


def test_pinned_run_and_redirect_hosts():
    settings = dict(
        repository_id=1,
        workflow_id=2,
        branch="main",
        workflow_path=".github/workflows/scrape.yml",
    )
    run = dict(
        repository={"id": 1},
        workflow_id=2,
        head_branch="main",
        path=".github/workflows/scrape.yml",
        event="workflow_dispatch",
        status="completed",
        conclusion="success",
        head_repository={"id": 1},
    )
    assert trusted_run(run, **settings)
    for change in [
        {"head_branch": "evil"},
        {"workflow_id": 3},
        {"event": "pull_request"},
        {"head_repository": {"id": 4}},
    ]:
        assert not trusted_run({**run, **change}, **settings)
    for url in [
        "http://localhost/a",
        "https://evil.com/a",
        "https://api.github.com/a",
        "https://blob.core.windows.net.evil.com/a",
        "https://127.0.0.1/a",
    ]:
        assert not download_host_allowed(url)
    assert download_host_allowed(
        "https://productionresultssa1.blob.core.windows.net/actions/x?sig=test"
    )


def test_api_authorization_never_reaches_signed_storage():
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.host == "api.github.com":
            return httpx.Response(
                302,
                headers={
                    "location": "https://productionresultssa1.blob.core.windows.net/actions/x?sig=test"
                },
            )
        return httpx.Response(200, content=b"bundle")

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        reader = GitHubReader("owner/repo", http=http, token="fixture-token")
        assert reader.download(123) == b"bundle"
    assert requests[0].headers["authorization"] == "Bearer fixture-token"
    assert "authorization" not in requests[1].headers
