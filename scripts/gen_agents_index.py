"""Generate AGENTS_INDEX.md and FINAL reports with live data."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, r"D:\HOSC")

from ohsc.config import SystemConfig
from ohsc.system import build_runtime


def build_rt():
    tmp = Path(tempfile.mkdtemp())
    cfg = SystemConfig(
        vault_root=tmp / "v", system_root=tmp / "s",
    )
    return build_runtime(cfg)


def agents_index():
    rt = build_rt()
    lines = ["# OHSC — Agents Index", "",
             "Total agents: {}".format(rt.registry.count()),
             "Enabled: {}".format(rt.registry.enabled_count()), ""]
    lines += ["## Registered Agents", "",
              "| Agent | Role | Enabled | Healthy | Responsibilities |",
              "|-------|------|---------|---------|------------------|"]
    for a in rt.registry.list_agents():
        c = rt.registry._contracts.get(a["name"])
        resp = ", ".join(c.responsibilities) if c else ""
        lines.append("| {} | {} | {} | {} | {} |".format(
            a["name"], a["role"], a["enabled"], a["healthy"], resp))
    lines += ["", "## Adding a New Agent", "",
              "1. Create `ohsc/agents/my_agent.py` subclassing `BaseAgent`.",
              "2. Define `contract = AgentContract(...)` and implement `execute`.",
              "3. Add one `rt.registry.register(MyAgent(rt))` line in `ohsc/system.py`.",
              "4. Add unit/integration tests under `tests/`.",
              "",
              "The core architecture is unchanged; only the registry grows."]
    return "\n".join(lines)


def main():
    out = agents_index()
    Path(r"D:\HOSC\AGENTS_INDEX.md").write_text(out, encoding="utf-8")
    print(out)
    print("\nWROTE AGENTS_INDEX.md")


if __name__ == "__main__":
    main()
