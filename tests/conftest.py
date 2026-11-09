"""Session-wide guard: the suite never opens a network connection (spec B21)."""

import socket

import pytest


class NetworkBlockedError(RuntimeError):
    pass


@pytest.fixture(autouse=True, scope="session")
def _block_network():
    mp = pytest.MonkeyPatch()

    def blocked(self, *args, **kwargs):
        raise NetworkBlockedError("network access is blocked in tests")

    mp.setattr(socket.socket, "connect", blocked)
    mp.setattr(socket.socket, "connect_ex", blocked)
    mp.setattr(socket, "create_connection", blocked)
    yield
    mp.undo()
