import importlib
import subprocess
import sys
import traceback

REQUIRED_PACKAGES = {
    "PyQt6": "PyQt6",
    "googleapiclient": "google-api-python-client",
}

def ensure_packages() -> None:
    """Install required packages if they are missing."""
    for module, package in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(module)
        except Exception:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == "__main__":
    ensure_packages()
    try:
        from app.main import main
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
