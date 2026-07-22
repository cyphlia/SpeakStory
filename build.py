#!/usr/bin/env python3
"""Build SpeakStory.exe with PyInstaller.

Usage:
    python build.py

Produces  dist/SpeakStory/SpeakStory.exe  (single-folder distribution).
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def main() -> int:
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "SpeakStory",
        "--noconfirm",
        "--windowed",                         # no console window
        # Collect customtkinter data files (required for CTk widgets)
        "--collect-data", "customtkinter",
        # Include our source packages
        "--add-data", f"{ROOT / 'src'};src",
        "--add-data", f"{ROOT / 'config.yaml'};.",
        # Hidden imports that PyInstaller may miss
        "--hidden-import", "sounddevice",
        "--hidden-import", "webrtcvad",
        "--hidden-import", "faster_whisper",
        "--hidden-import", "requests",
        "--hidden-import", "yaml",
        "--hidden-import", "numpy",
        "--hidden-import", "PIL",
    ]

    # Add icon if available
    icon = ROOT / "assets" / "icon.ico"
    if icon.exists():
        cmd.extend(["--icon", str(icon)])

    # Entry point
    cmd.append(str(ROOT / "app.py"))

    print(f"Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=str(ROOT))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
