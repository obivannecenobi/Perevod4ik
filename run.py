import importlib
import os
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
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        print(
            "GUI не будет показан, удалите QT_QPA_PLATFORM или установите в windows"
        )
    ensure_packages()
    try:
        from app.main import main
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
