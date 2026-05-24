"""
Build Pickleball HQ as a standalone desktop app for the CURRENT platform.

Usage:
    python build.py

Output:
    Windows: dist/Pickleball HQ/Pickleball HQ.exe
    macOS:   dist/Pickleball HQ.app
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def clean():
    """Remove previous build artifacts."""
    for d in ("build", "dist"):
        p = ROOT / d
        if p.exists():
            print(f"Cleaning {d}/")
            shutil.rmtree(p)


def ensure_pyinstaller():
    try:
        import PyInstaller  # noqa
    except ImportError:
        print("Installing PyInstaller…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build():
    print("Building Pickleball HQ for", sys.platform)
    subprocess.check_call(
        [sys.executable, "-m", "PyInstaller", "pickleball-hq.spec", "--noconfirm"],
        cwd=ROOT,
    )

    dist = ROOT / "dist"
    print("\n" + "=" * 50)
    print("Build complete.")
    if sys.platform == "darwin":
        target = dist / "Pickleball HQ.app"
        print(f"App: {target}")
        print("Drag it into /Applications to install.")
    elif sys.platform == "win32":
        target = dist / "Pickleball HQ" / "Pickleball HQ.exe"
        print(f"Exe: {target}")
        print("The whole 'Pickleball HQ' folder is portable — zip it or make a shortcut to the .exe.")
    else:
        target = dist / "Pickleball HQ"
        print(f"Built to: {target}")
    print("=" * 50)


if __name__ == "__main__":
    clean()
    ensure_pyinstaller()
    build()
