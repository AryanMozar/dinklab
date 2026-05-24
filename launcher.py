"""
Pickleball HQ — Desktop launcher
Starts the Flask server in a background thread and opens a native window via pywebview.
Cross-platform: works on Windows and macOS.
"""

import sys
import threading
import time
import socket
from pathlib import Path

# Make backend/ importable
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "backend"))

import webview  # pywebview
from app import app  # Flask app


def find_free_port(preferred: int = 5000) -> int:
    """Try preferred port, fall back to OS-assigned if taken."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", preferred))
            return preferred
    except OSError:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def run_flask(port: int):
    """Run Flask without the reloader (we're embedded)."""
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True)


def wait_for_server(port: int, timeout: float = 10.0) -> bool:
    """Poll until Flask is accepting connections, or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def main():
    port = find_free_port(5000)

    # Start Flask in a daemon thread so it exits when the window closes
    flask_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
    flask_thread.start()

    if not wait_for_server(port):
        print("ERROR: Flask server failed to start", file=sys.stderr)
        sys.exit(1)

    # Open the native window
    webview.create_window(
        title="Pickleball HQ",
        url=f"http://127.0.0.1:{port}",
        width=1280,
        height=860,
        min_size=(900, 600),
        resizable=True,
    )
    webview.start()


if __name__ == "__main__":
    main()
