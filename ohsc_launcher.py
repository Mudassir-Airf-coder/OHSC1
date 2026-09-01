"""Global OHSC launcher / entry point.

This is the single binary entry that the ``ohsc`` command invokes.
It is intentionally tiny: it puts the OHSC install root on ``sys.path``
and delegates to :func:`ohsc.cli.main`.

The install root is resolved portably:
1. OHSC_SYSTEM_ROOT environment variable (if set)
2. Directory containing this file (repo / install root)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Portable OHSC root (overridable via env for testing/portability).
_HERE = Path(__file__).resolve().parent
SYSTEM_ROOT = Path(os.environ.get("OHSC_SYSTEM_ROOT", str(_HERE))).expanduser().resolve()
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))


def main() -> int:
    from ohsc.cli import main as cli_main
    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
