"""The harness every later milestone writes into, and the guard it carries.

Issue #14. The suite runs offline, and this file is what makes that a property
of the run rather than a property of the machine somebody happened to run it
on. A test that reaches for the network is refused here, so the refusal is the
same on a workstation with a connection and on a runner without one.

What the guard covers. Creating a socket of any family, the convenience
constructor that opens one for you, and the two name lookups that reach a
resolver without a socket object ever becoming visible to the test. Each is
replaced for the length of the session and put back afterwards.

What it does not cover, said plainly so the guard is not read as more than it
is. It is a floor. A test that spawns a subprocess is outside it, because the
child is a fresh interpreter this file never patched. So is an extension module
that opens a descriptor without going through the `socket` module. Both are
reachable and neither is refused here.

The proof that the guard bites is `tests/test_network_guard.py`, and it is
written as a test that is expected to fail: it opens a socket, and the only way
it can pass is a guard that stopped working. That is why it carries
`strict=True`, which turns an unexpected pass into a red suite instead of a
green one with a note in it.

Two further conditions of the run are stated rather than enforced, because
nothing here can read either one. The suite needs no display: no test in the
tree opens one, and nothing refuses a later test that does. The suite needs no
elevation: no test asks for a privilege, and nothing refuses a later test that
does. Neither sentence is a guarantee bought by a check.

    pytest -q
"""

import socket
from collections.abc import Iterator
from typing import NoReturn

import pytest


class NetworkAccessAttempted(RuntimeError):
    """A test reached for the network, and the harness refused.

    A distinct type rather than the `OSError` a real failed connection raises,
    because the proof in `tests/test_network_guard.py` has to tell a guard that
    bit from a machine that simply had no route. Those two are the same
    exception on a disconnected runner, and a proof that cannot tell them apart
    passes for the wrong reason on exactly the machine the guard exists for.
    """


def _refuse(*arguments: object, **keywords: object) -> NoReturn:
    raise NetworkAccessAttempted(
        "a test reached for the network. The suite runs offline: input "
        "documents, intermediate expressions and results stay on the host, and "
        "a test that needs a connection is a test that is asserting something "
        "this pipeline does not do. If a stage genuinely has to be exercised "
        "against a socket, it is a stage that needs its own issue first."
    )


@pytest.fixture(autouse=True, scope="session")
def no_network() -> Iterator[None]:
    """Refuse the network for the length of the session.

    Autouse and session scoped, so no test has to remember it and no test can
    decline it. The names are restored when the session ends, which matters
    only to whoever is running the suite inside a longer-lived process.
    """
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(socket.socket, "__init__", _refuse)
        patch.setattr(socket, "create_connection", _refuse)
        patch.setattr(socket, "getaddrinfo", _refuse)
        patch.setattr(socket, "gethostbyname", _refuse)
        yield
