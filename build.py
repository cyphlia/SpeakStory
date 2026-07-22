#!/usr/bin/env python3
"""Build SpeakStory.exe with PyInstaller.

Usage:
    python build.py

Produces SpeakStory.exe directly in the project root folder.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def main() -> int:
    cmd = [
        sys.executable, "-m", "PyInstaller.__main__",
        "--name", "SpeakStory",
        "--noconfirm",
        "--windowed",                          # no console window
        "--onefile",                           # single executable file
        "--collect-all", "customtkinter",
        "--collect-all", "ctranslate2",
        "--collect-all", "faster_whisper",
        "--add-data", f"{ROOT / 'src'};src",
        "--add-data", f"{ROOT / 'config.yaml'};.",
        "--hidden-import", "sounddevice",
        "--hidden-import", "webrtcvad",
        "--hidden-import", "requests",
        "--hidden-import", "yaml",
        "--hidden-import", "numpy",
        "--hidden-import", "PIL",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build"),
    ]

    icon = ROOT / "assets" / "icon.ico"
    if icon.exists():
        cmd.extend(["--icon", str(icon)])

    cmd.append(str(ROOT / "app.py"))

    print(f"Running PyInstaller build:\n{' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print("PyInstaller build failed!")
        return result.returncode

    # Copy generated SpeakStory.exe to root directory for easy double-clicking
    dist_exe = ROOT / "dist" / "SpeakStory.exe"
    target_exe = ROOT / "SpeakStory.exe"
    if dist_exe.exists():
        shutil.copy2(dist_exe, target_exe)
        print(f"\nSUCCESS! Created standalone executable:\n{target_exe}")
        print("You can double-click SpeakStory.exe directly from File Explorer to launch the application.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
