import asyncio
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


def test_an_event_loop_still_runs_but_a_direct_loopback_connect_does_not():
    # asyncio's self-pipe (Windows) is the one loopback connect the guard lets through.
    async def nothing():
        return 1

    assert asyncio.run(nothing()) == 1
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(NetworkBlockedError):
            s.connect(("127.0.0.1", 9))
    finally:
        s.close()


# --- the exemption needs all three conditions: each test fails exactly one ----

_SRC = "def {name}(sock, addr):\n    sock.connect(addr)\n"


def _connect_from(name, filename, addr):
    namespace: dict = {}
    exec(compile(_SRC.format(name=name), filename, "exec"), namespace)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        namespace[name](s, addr)
    finally:
        s.close()


def test_the_right_function_name_in_another_file_is_blocked():
    with pytest.raises(NetworkBlockedError):
        _connect_from("_fallback_socketpair", __file__, ("127.0.0.1", 9))


def test_a_file_whose_name_only_ends_in_socket_py_is_blocked():
    with pytest.raises(NetworkBlockedError):
        _connect_from("_fallback_socketpair", "/x/websocket.py", ("127.0.0.1", 9))


def test_another_function_in_the_socket_module_file_is_blocked():
    with pytest.raises(NetworkBlockedError):
        _connect_from("some_other_function", socket.__file__, ("127.0.0.1", 9))


def test_the_socketpair_function_in_the_socket_file_may_not_leave_loopback():
    with pytest.raises(NetworkBlockedError):
        _connect_from("_fallback_socketpair", socket.__file__, ("10.255.255.1", 9))
