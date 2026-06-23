from __future__ import annotations

import socket


class AlreadyRunning(RuntimeError):
    pass


class InstanceLock:
    """Tiny process-lifetime singleton lock using a localhost TCP port.

    Windows file locks are a swamp. A bound localhost port is simple, released on
    process exit, and works for GUI processes launched from shortcuts.
    """

    def __init__(self, port: int, name: str):
        self.port = port
        self.name = name
        self._sock: socket.socket | None = None

    def acquire(self) -> "InstanceLock":
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        try:
            sock.bind(("127.0.0.1", self.port))
            sock.listen(1)
        except OSError as exc:
            sock.close()
            raise AlreadyRunning(f"{self.name} is already running") from exc
        self._sock = sock
        return self

    def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None


def acquire_instance_lock(port: int, name: str) -> InstanceLock:
    return InstanceLock(port, name).acquire()
