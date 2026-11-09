import socket

import pytest

from tests.conftest import NetworkBlockedError


def test_socket_connect_is_blocked():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(NetworkBlockedError):
            s.connect(("127.0.0.1", 9))
    finally:
        s.close()


def test_create_connection_is_blocked():
    with pytest.raises(NetworkBlockedError):
        socket.create_connection(("127.0.0.1", 9))
