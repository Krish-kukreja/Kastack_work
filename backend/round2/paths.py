"""Single source of truth for filesystem paths used across the round2 package.

Works identically in dev (``Kastack/backend/round2/``) and in the Docker image
(``/app/backend/round2/``) by locating the project root via the ``data/processed``
directory, instead of fragile ``parent.parent.parent`` counting.
"""
from pathlib import Path


def _find_project_root(start) -> Path:
    start = Path(start).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / "data" / "processed").exists():
            return candidate
    # Fallback: this file lives at <root>/backend/round2/paths.py
    return start.parents[2]


ROUND2_DIR = Path(__file__).resolve().parent          # .../backend/round2
PROJECT_ROOT = _find_project_root(__file__)            # contains data/ and backend/
DATA_DIR = PROJECT_ROOT / "data" / "processed"
