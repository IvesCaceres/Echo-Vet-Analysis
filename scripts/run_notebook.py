"""Offline sequential code-cell runner; does not persist notebook outputs."""
from pathlib import Path
import argparse
import contextlib
import io
import json
import os
import socket
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook")
    parser.add_argument("--allow-private", action="store_true")
    args = parser.parse_args()
    mode = os.environ.get("ECHO_MODE", "PUBLIC_DEMO")
    if mode == "PRIVATE_ANALYSIS" and not args.allow_private:
        raise SystemExit("Private execution needs explicit --allow-private; review output handling first")
    root = Path(__file__).resolve().parents[1]
    notebook = (root / args.notebook).resolve(strict=True)
    if not notebook.is_relative_to(root / "notebooks") or notebook.suffix != ".ipynb":
        raise SystemExit("Select an included notebook")
    def no_network(*args, **kwargs):
        raise RuntimeError("Network disabled for this runner")
    socket.create_connection = no_network
    socket.socket.connect = no_network
    def audit(event, args):
        if event in {"socket.connect", "socket.bind", "subprocess.Popen", "os.system", "os.exec"}:
            raise RuntimeError("External operation disabled")
    sys.addaudithook(audit)
    os.environ.setdefault("MPLBACKEND", "Agg")
    document = json.loads(notebook.read_text(encoding="utf-8"))
    namespace = {"__name__": "__main__"}
    try:
        from IPython.display import display
        namespace["display"] = display
    except ImportError:
        namespace["display"] = lambda *a, **k: None
    completed = 0
    for index, cell in enumerate(document["cells"]):
        if cell["cell_type"] != "code":
            continue
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                exec(compile("".join(cell["source"]), f"candidate_cell_{index}", "exec"), namespace)
            completed += 1
        except Exception as error:
            print(json.dumps({"status": "FAIL", "cell": index, "exception": type(error).__name__,
                              "message": "Details withheld; no cell output retained"}))
            return 1
    print(json.dumps({"status": "PASS", "code_cells": completed, "mode": mode,
                      "outputs_saved_in_notebook": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
