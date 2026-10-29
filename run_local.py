import os
import sys
import time
import subprocess
import argparse

# Force UTF-8 encoding across Windows processes
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable

child_env = os.environ.copy()
child_env["PYTHONUTF8"] = "1"
child_env["PYTHONIOENCODING"] = "utf-8"


def start_backend(host="127.0.0.1", port=8000):
    print(f"[Backend] Starting FastAPI on http://{host}:{port} ...")
    cmd = [
        PYTHON_EXE,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--host",
        host,
        "--port",
        str(port)
    ]
    return subprocess.Popen(cmd, cwd=ROOT_DIR, env=child_env)


def start_frontend(port=8501):
    print(f"[Frontend] Starting Streamlit UI on http://localhost:{port} ...")
    cmd = [
        PYTHON_EXE,
        "-m",
        "streamlit",
        "run",
        os.path.join(ROOT_DIR, "frontend", "app.py"),
        "--server.port",
        str(port),
        "--server.headless",
        "true"
    ]
    return subprocess.Popen(cmd, cwd=ROOT_DIR, env=child_env)


def main():
    parser = argparse.ArgumentParser(description="MM-Chatbot Local Application Launcher")
    parser.add_argument("--backend-only", action="store_true", help="Run only the FastAPI backend")
    parser.add_argument("--frontend-only", action="store_true", help="Run only the Streamlit frontend")
    parser.add_argument("--backend-port", type=int, default=8000, help="Port for FastAPI backend (default: 8000)")
    parser.add_argument("--frontend-port", type=int, default=8501, help="Port for Streamlit frontend (default: 8501)")
    args = parser.parse_args()

    os.makedirs(os.path.join(ROOT_DIR, "storage", "audio"), exist_ok=True)
    os.makedirs(os.path.join(ROOT_DIR, "storage", "generated"), exist_ok=True)

    processes = []

    try:
        if args.backend_only:
            proc = start_backend(port=args.backend_port)
            processes.append(proc)
            proc.wait()
        elif args.frontend_only:
            proc = start_frontend(port=args.frontend_port)
            processes.append(proc)
            proc.wait()
        else:
            backend_proc = start_backend(port=args.backend_port)
            processes.append(backend_proc)

            time.sleep(2)

            frontend_proc = start_frontend(port=args.frontend_port)
            processes.append(frontend_proc)

            print("\n=======================================================")
            print(">> MM-Chatbot is RUNNING LOCALLY!")
            print(f">> 1. Web Chatbot (HTML/JS Glassmorphism): http://127.0.0.1:{args.backend_port}")
            print(f">> 2. Streamlit Studio & RAG Workspace:    http://localhost:{args.frontend_port}")
            print(f">> 3. Interactive API Docs (Swagger):      http://127.0.0.1:{args.backend_port}/docs")
            print(">> Press Ctrl+C in this terminal to stop.")
            print("=======================================================\n")

            while True:
                time.sleep(2)
                dead = [p for p in processes if p.poll() is not None]
                if len(dead) == len(processes):
                    print("All server processes have terminated.")
                    break

    except KeyboardInterrupt:
        print("\nStopping MM-Chatbot servers...")
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("Shutdown complete.")


if __name__ == "__main__":
    main()
