"""The suite. Laid out as a package so a test can import the harness by name.

Issue #14. Without this file the guard in `conftest.py` is importable only as a
top-level module whose name depends on how pytest was invoked, and the proof in
`test_network_guard.py` has to reach the exception type the guard raises.
"""
