"""Session-wide guard: the suite never opens a network connection (spec B21)."""

import socket
import sys

import pytest


class NetworkBlockedError(RuntimeError):
    pass


@pytest.fixture(autouse=True, scope="session")
def _block_network():
    mp = pytest.MonkeyPatch()
    real_connect = socket.socket.connect

    def blocked(self, *args, **kwargs):
        raise NetworkBlockedError("network access is blocked in tests")

    def blocked_connect(self, *args, **kwargs):
        # On Windows every asyncio event loop (Starlette's TestClient makes one)
        # builds its self-pipe with `socket._fallback_socketpair`, which connects
        # two sockets of its own over loopback. That, and nothing else, is allowed.
        caller = sys._getframe(1).f_code
        address = args[0] if args else None
        if (
            caller.co_name == "_fallback_socketpair"
            and caller.co_filename.endswith("socket.py")
            and isinstance(address, tuple)
            and address[0] in ("127.0.0.1", "::1")
        ):
            return real_connect(self, *args, **kwargs)
        return blocked(self, *args, **kwargs)

    mp.setattr(socket.socket, "connect", blocked_connect)
    mp.setattr(socket.socket, "connect_ex", blocked)
    mp.setattr(socket, "create_connection", blocked)
    yield
    mp.undo()
