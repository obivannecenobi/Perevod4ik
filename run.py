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


def configure_qt_platform() -> None:
    """Configure Qt backend based on environment and system platform."""
    platform = os.environ.get("QT_QPA_PLATFORM")
    if platform == "offscreen":
        del os.environ["QT_QPA_PLATFORM"]
        platform = None
    if platform is None:
        os.environ["QT_QPA_PLATFORM"] = "windows" if sys.platform.startswith("win") else "xcb"

if __name__ == "__main__":
    ensure_packages()
    configure_qt_platform()
    try:
        from app.main import main
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
