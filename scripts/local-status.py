"""Read-only local service checks. Does not load credentials or mutate app data."""
import json
import socket
import urllib.error
import urllib.request


def tcp(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except OSError:
        return False


def http(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


checks = {
    "web": http("http://localhost:3000/explore"),
    "api": http("http://127.0.0.1:8000/api/health"),
    "database_ready": http("http://127.0.0.1:8000/api/ready"),
    "postgres_port": tcp(55432),
    "scanner_port": tcp(3310),
    "local_mail_port": tcp(1025),
}
print(json.dumps(checks, indent=2))
print("Port checks establish reachability, not scanner signature freshness or mail delivery.")
print("Worker and scheduler require separate process/job checks; no cloud services checked.")
raise SystemExit(0 if all(checks.values()) else 1)
