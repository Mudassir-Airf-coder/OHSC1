"""Harness: run `graphify extract` against a vault using an OpenAI-compatible backend.

Reads backend config from environment (NEVER printed):
  GF_BASE_URL, GF_MODEL, GF_API_KEY, GF_VAULT, GF_OUT_LOG
The key is passed only to the child subprocess env, never logged.
"""
import os, sys, subprocess, pathlib, shutil

VENV = r"C:\Users\HAJI LAPTOP G55\AppData\Roaming\uv\tools\graphifyy\Scripts\python.exe"
vault = os.environ["GF_VAULT"]
log_path = os.environ.get("GF_OUT_LOG", "/tmp/gf_extract.log")

env = dict(os.environ)
env["OPENAI_BASE_URL"] = os.environ["GF_BASE_URL"]
env["OPENAI_MODEL"] = os.environ["GF_MODEL"]
env["OPENAI_API_KEY"] = os.environ["GF_API_KEY"]
env.pop("PYTHONPATH", None)

out_dir = pathlib.Path(vault) / "graphify-out"
if out_dir.exists():
    shutil.rmtree(out_dir, ignore_errors=True)

cmd = [VENV, "-m", "graphify", "extract", vault]
with open(log_path, "w", encoding="utf-8") as f:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900, env=env)
        f.write(f"EXIT={proc.returncode}\n")
        f.write("=== STDOUT ===\n" + proc.stdout + "\n")
        f.write("=== STDERR ===\n" + proc.stderr + "\n")
    except subprocess.TimeoutExpired as e:
        f.write("TIMEOUT\n")
        f.write("STDOUT:\n" + (e.stdout or "") + "\n")
        f.write("STDERR:\n" + (e.stderr or "") + "\n")

gp = out_dir / "graph.json"
print(f"EXIT={proc.returncode if 'proc' in dir() else 'TIMEOUT'}")
print(f"graph.json exists: {gp.exists()}")
if gp.exists():
    print(f"graph.json bytes: {gp.stat().st_size}")
