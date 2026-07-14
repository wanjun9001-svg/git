from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _reexec_with_venv() -> None:
    script = Path(__file__).resolve()
    venv_scripts = script.parent.parent / ".venv" / "Scripts"

    venv_python = venv_scripts / "python.exe"
    venv_pythonw = venv_scripts / "pythonw.exe"

    if not venv_python.exists() and not venv_pythonw.exists():
        return

    current = Path(sys.executable).resolve()
    if (venv_python.exists() and current == venv_python.resolve()) or (
        venv_pythonw.exists() and current == venv_pythonw.resolve()
    ):
        return

    target = venv_pythonw if venv_pythonw.exists() else venv_python
    subprocess.Popen([str(target), str(script), *sys.argv[1:]], cwd=str(script.parent))
    raise SystemExit(0)


_reexec_with_venv()

if __name__ == "__main__":
    from gui.interface import run

    run()
