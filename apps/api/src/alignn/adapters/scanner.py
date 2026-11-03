import socket
import struct

from alignn.adapters.mail import PermanentDeliveryError


class ClamScanner:
    def __init__(self, host: str | None, port: int = 3310):
        self.host, self.port = host, port

    def clean(self, stream) -> bool:
        if not self.host:
            raise PermanentDeliveryError("scanner_not_configured")
        with socket.create_connection((self.host, self.port), timeout=10) as connection:
            connection.settimeout(10)
            connection.sendall(b"zINSTREAM\0")
            while chunk := stream.read(65536):
                connection.sendall(struct.pack("!I", len(chunk)) + chunk)
            connection.sendall(struct.pack("!I", 0))
            reply = b""
            while len(reply) < 4096:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                reply += chunk
                if b"\0" in chunk:
                    break
        if b"FOUND" in reply:
            return False
        if b"stream: OK" not in reply:
            raise OSError("Scanner did not return a clean verdict")
        return True
