#!/usr/bin/env python3
"""One-command launcher for OHM Email Intelligence Agent.

Starts:
1. FastAPI backend on http://localhost:8000
2. Vite development server on http://localhost:5173
3. Opens browser automatically
"""

import subprocess
import sys
import time
import webbrowser
import signal
import os
from pathlib import Path


def main():
    """Main launcher function."""
    project_root = Path(__file__).parent
    frontend_dir = project_root / "frontend"

    print("=" * 60)
    print("OHM Email Intelligence Agent - Launcher")
    print("=" * 60)
    print()
    print("Starting servers...")
    print("  • Backend:  http://localhost:8000")
    print("  • Frontend: http://localhost:5173")
    print("  • API Docs: http://localhost:8000/docs")
    print()

    # Process list to manage
    processes = []

    try:
        # Check if frontend dependencies are installed
        if not (frontend_dir / "node_modules").exists():
            print("Installing frontend dependencies...")
            subprocess.run(
                ["npm", "install"],
                cwd=str(frontend_dir),
                check=True,
                capture_output=True
            )
            print("[OK] Frontend dependencies installed")
            print()

        # Start FastAPI backend
        print("Starting FastAPI backend...")
        backend_process = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "src.api.app:app",
                "--host", "127.0.0.1",
                "--port", "8000",
                "--reload"
            ],
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(("Backend", backend_process))
        print("[OK] Backend started (PID: {})".format(backend_process.pid))

        # Start Vite frontend dev server
        print("Starting Vite development server...")
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(frontend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(("Frontend", frontend_process))
        print("[OK] Frontend started (PID: {})".format(frontend_process.pid))

        # Wait for servers to start
        print()
        print("Waiting for servers to start...")
        time.sleep(4)

        # Open browser
        print("Opening browser...")
        try:
            webbrowser.open("http://localhost:5173")
            print("✓ Browser opened to http://localhost:5173")
        except Exception as e:
            print(f"[WARN] Could not open browser automatically: {e}")
            print("  Please open http://localhost:5173 manually")

        print()
        print("=" * 60)
        print("[OK] All servers running!")
        print("=" * 60)
        print()
        print("API Documentation: http://localhost:8000/docs")
        print("Frontend:          http://localhost:5173")
        print()
        print("Press Ctrl+C to stop all servers")
        print()

        # Keep running until interrupted
        while True:
            time.sleep(1)

            # Check if processes are still running
            for name, process in processes:
                if process.poll() is not None:
                    print(f"[WARN] {name} process ended unexpectedly!")
                    raise KeyboardInterrupt()

    except KeyboardInterrupt:
        print()
        print()
        print("Shutting down...")

        # Terminate all processes
        for name, process in reversed(processes):
            try:
                print(f"Stopping {name}...", end=" ", flush=True)
                process.terminate()
                try:
                    process.wait(timeout=5)
                    print("[OK]")
                except subprocess.TimeoutExpired:
                    print("(force killing)", end=" ", flush=True)
                    process.kill()
                    process.wait()
                    print("[OK]")
            except Exception as e:
                print(f"[ERROR] ({e})")

        print()
        print("Goodbye!")
        sys.exit(0)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("\nCleaning up...")

        # Kill any remaining processes
        for name, process in processes:
            try:
                process.kill()
            except:
                pass

        sys.exit(1)


if __name__ == "__main__":
    # Handle signals properly on Windows
    if sys.platform == "win32":
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    main()
