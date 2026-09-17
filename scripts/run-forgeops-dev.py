"""Run ForgeOps from this repository's exact source tree."""

from __future__ import annotations

import os
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"

# Insert before importing ForgeOps so stale installed metadata cannot choose an
# older package first. The marker lets the provenance command validate that the
# loaded module and pyproject version belong to this exact checkout.
sys.path.insert(0, str(SOURCE_ROOT))
os.environ["FORGEOPS_SOURCE_ROOT"] = str(REPOSITORY_ROOT)

from forgeops.cli import main  # noqa: E402


raise SystemExit(main())
