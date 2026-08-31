"""Global OHSC launcher / entry point.

This is the single binary entry that the ``ohsc`` command (Windows .cmd
shim and git-bash shell shim) invokes. It is intentionally tiny: it puts
``D:\HOSC`` on ``sys.path`` and delegates to :func:`ohsc.cli.main`.

Because the absolute root is hard-coded here, the ``ohsc`` command works
from ANY directory without ``cd D:\HOSC`` first.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Authoritative OHSC root (overridable via env for testing/portability).
SYSTEM_ROOT = Path(os.environ.get("OHSC_SYSTEM_ROOT", r"D:\HOSC")).resolve()
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))


def main() -> int:
    from ohsc.cli import main as cli_main
    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
