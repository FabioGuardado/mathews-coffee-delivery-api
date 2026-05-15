"""
fix_cassandra_py313.py
----------------------
Patches cassandra-driver 3.30.0 to work on Python 3.12+ (where asyncore was
removed) without C extensions or gevent.

Root cause
~~~~~~~~~~
The installed wheel ships a Cython-compiled `cluster.cp3XX-win_amd64.pyd` that
takes priority over `cluster.py`. That `.pyd` has a hard-coded fallback chain:
    gevent → eventlet → libev → asyncore
None of those work on Python 3.12+ without extra setup. The `.pyd` cannot be
patched, so we delete it and patch the source `cluster.py` to add
`AsyncioConnection` as a final fallback.

AsyncioConnection is safe here: it spins up its own asyncio event loop in a
background daemon thread, completely independent from FastAPI's event loop.
run_in_executor calls work correctly because FastAPI's loop is still running
while the executor thread blocks on a threading.Event waiting for Cassandra's
async I/O to complete on that separate loop.

Usage
~~~~~
    python scripts/fix_cassandra_py313.py

Run this once after `pip install -r requirements.txt` whenever setting up a
fresh virtual environment on Python 3.12+.
"""

import importlib.util
import os
import re
import sys
import textwrap

MIN_PYTHON = (3, 12)
DRIVER_PACKAGE = "cassandra"
TARGET_MODULE = "cassandra.cluster"


def _find_package_dir() -> str:
    spec = importlib.util.find_spec(DRIVER_PACKAGE)
    if spec is None or not spec.submodule_search_locations:
        sys.exit("ERROR: cassandra-driver not found in the current environment.")
    return list(spec.submodule_search_locations)[0]


def _remove_pyd(pkg_dir: str) -> None:
    """Delete the compiled cluster extension so cluster.py takes priority."""
    pattern = re.compile(r"^cluster\.cp\d+-.*\.(pyd|so)$")
    removed = []
    for name in os.listdir(pkg_dir):
        if pattern.match(name):
            path = os.path.join(pkg_dir, name)
            os.remove(path)
            removed.append(name)
    if removed:
        print(f"  Removed compiled extension(s): {', '.join(removed)}")
    else:
        print("  No compiled cluster extension found (already removed or pure Python install).")


_ASYNCIO_FALLBACK = textwrap.dedent("""\
    def _try_asyncio_import():
        # Added by scripts/fix_cassandra_py313.py
        # Fallback for Python 3.12+ where asyncore was removed and libev/gevent
        # are not available. AsyncioConnection runs its own event loop in a daemon
        # thread, fully compatible with run_in_executor usage from asyncio apps.
        try:
            from cassandra.io.asyncioreactor import AsyncioConnection
            return (AsyncioConnection, None)
        except Exception as e:
            return (None, e)

""")

_OLD_CONN_FNS = (
    "conn_fns = (_try_gevent_import, _try_eventlet_import, "
    "_try_libev_import, _try_asyncore_import)"
)
_NEW_CONN_FNS = (
    "conn_fns = (_try_gevent_import, _try_eventlet_import, "
    "_try_libev_import, _try_asyncore_import, _try_asyncio_import)"
)
_ALREADY_PATCHED_MARKER = "_try_asyncio_import"


def _patch_cluster_py(pkg_dir: str) -> None:
    """Inject _try_asyncio_import into the fallback chain in cluster.py."""
    cluster_py = os.path.join(pkg_dir, "cluster.py")
    if not os.path.exists(cluster_py):
        sys.exit(f"ERROR: {cluster_py} not found.")

    with open(cluster_py, "r", encoding="utf-8") as f:
        source = f.read()

    if _ALREADY_PATCHED_MARKER in source:
        print("  cluster.py already patched — nothing to do.")
        return

    if _OLD_CONN_FNS not in source:
        sys.exit(
            "ERROR: Expected conn_fns definition not found in cluster.py.\n"
            "The cassandra-driver version may be different from 3.30.0.\n"
            "Please inspect the file manually."
        )

    # Insert the new function right before conn_fns = (...)
    patched = source.replace(
        _OLD_CONN_FNS,
        _ASYNCIO_FALLBACK + _NEW_CONN_FNS,
    )

    # Remove stale bytecode so Python picks up the patched source
    pyc_dir = os.path.join(pkg_dir, "__pycache__")
    if os.path.isdir(pyc_dir):
        for name in os.listdir(pyc_dir):
            if name.startswith("cluster.") and name.endswith(".pyc"):
                os.remove(os.path.join(pyc_dir, name))

    with open(cluster_py, "w", encoding="utf-8") as f:
        f.write(patched)

    print("  cluster.py patched successfully.")


def main() -> None:
    if sys.version_info < MIN_PYTHON:
        print(
            f"Python {sys.version_info.major}.{sys.version_info.minor} detected — "
            "patch not needed (asyncore is available). Exiting."
        )
        return

    print(f"Python {sys.version_info.major}.{sys.version_info.minor} detected — applying patch.")
    pkg_dir = _find_package_dir()
    print(f"cassandra package at: {pkg_dir}")

    print("Step 1: Remove compiled cluster extension...")
    _remove_pyd(pkg_dir)

    print("Step 2: Patch cluster.py...")
    _patch_cluster_py(pkg_dir)

    print("\nVerifying...")
    # Force reimport
    import importlib
    for mod in list(sys.modules):
        if mod.startswith("cassandra"):
            del sys.modules[mod]
    try:
        import cassandra.cluster as cc
        print(f"  DefaultConnection: {cc.DefaultConnection.__name__}")
        print("\nPatch applied successfully.")
    except Exception as exc:
        print(f"\nERROR: patch did not fix the issue — {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
