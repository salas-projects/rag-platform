"""Import smoke test — keeps the suite non-empty (pytest exits 5 on zero tests collected,
which CI would read as failure) and catches a broken package layout early."""

import importlib


def test_packages_import():
    for name in ("core", "connectors", "app"):
        importlib.import_module(name)
