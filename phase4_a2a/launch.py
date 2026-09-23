"""Start the specialist agents as separate OS processes."""

import contextlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

PORTS = {"research": 8101, "analysis": 8102, "writer": 8103, "factcheck": 8104}


def _card_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/.well-known/agent-card.json"


def _wait_for(port: int, timeout: float = 45.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(_card_url(port), timeout=1):
                return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.25)
    return False


@contextlib.contextmanager
def agent_services(names=None, quiet: bool = True):
    """Run the named agents as subprocesses for the duration of the block."""
    names = list(names or PORTS)
    procs: list[subprocess.Popen] = []
    try:
        for name in names:
            port = PORTS[name]
            procs.append(
                subprocess.Popen(
                    [sys.executable, "-m", "phase4_a2a.server", name, str(port)],
                    stdout=subprocess.DEVNULL if quiet else None,
                    stderr=subprocess.DEVNULL if quiet else None,
                )
            )
        for name in names:
            if not _wait_for(PORTS[name]):
                raise RuntimeError(f"agent {name!r} did not come up on {PORTS[name]}")
            print(f"  [up] {name:9s} http://127.0.0.1:{PORTS[name]}")
        yield {n: f"http://127.0.0.1:{PORTS[n]}" for n in names}
    finally:
        for p in procs:
            p.terminate()
        for p in procs:
            with contextlib.suppress(Exception):
                p.wait(timeout=10)
