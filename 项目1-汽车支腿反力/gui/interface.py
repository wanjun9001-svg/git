from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _workspace_root() -> Path:
    return _project_root().parent


def _reexec_with_venv() -> None:
    script = Path(__file__).resolve()
    venv_scripts = _workspace_root() / ".venv" / "Scripts"

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
    subprocess.Popen([str(target), str(script), *sys.argv[1:]], cwd=str(_project_root()))
    raise SystemExit(0)


def _ensure_project_root_on_path() -> None:
    root = str(_project_root())
    if root not in sys.path:
        sys.path.insert(0, root)


_reexec_with_venv()
_ensure_project_root_on_path()

from gui.calculation_app import run


if __name__ == "__main__":
    run()
