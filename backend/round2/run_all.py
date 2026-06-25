"""Run each round2 module's self-check as a package module from backend/.

Modules use package imports (round2.*), so they must be run with `-m` and
cwd=backend (not as bare scripts).
"""
import sys
import subprocess
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent  # .../backend

MODULES = [
    "round2.intent.classify",
    "round2.affect.emotion",
    "round2.drift.timeline",
    "round2.drift.demo_arc",
    "round2.rag.conflict_resolver",
    "round2.sync.demo_sync",
]


def run_module(mod):
    print(f"Running {mod} ...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", mod],
            cwd=str(BACKEND_DIR),
            capture_output=True,
            text=True,
            timeout=240,
        )
        if result.returncode == 0:
            print(f"\033[92m[PASS] {mod}\033[0m")
        else:
            print(f"\033[91m[FAIL] {mod} (exit {result.returncode})\033[0m")
            print(result.stderr[-600:])
    except Exception as e:
        print(f"\033[91m[ERROR] {mod} - {e}\033[0m")


def main():
    for mod in MODULES:
        run_module(mod)


if __name__ == "__main__":
    main()
