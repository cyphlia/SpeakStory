#!/usr/bin/env python3
"""SYS - Speak Your Story — AI-powered voice notes desktop app.

Launch with:
    python app.py

The CLI entry point (main.py) still works for headless use.
"""
from __future__ import annotations

import sys


def main() -> int:
    # Import here so import errors surface after the guard
    import customtkinter as ctk
    from src.ui.main_window import MainWindow

    ctk.set_appearance_mode("dark")

    app = MainWindow()

    # Try to set a window icon (non-fatal if missing)
    try:
        import os, pathlib
        icon_path = pathlib.Path(__file__).parent / "assets" / "icon.ico"
        if icon_path.exists():
            app.iconbitmap(str(icon_path))
    except Exception:
        pass

    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
