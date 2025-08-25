import importlib
import os
import subprocess
import sys
import traceback

REQUIRED_PACKAGES = {
    "PyQt6": "PyQt6",
    "googleapiclient": "google-api-python-client",
    "docx": "python-docx",
}

def ensure_packages() -> None:
    """Install required packages if they are missing."""
    for module, package in REQUIRED_PACKAGES.items():
        if importlib.util.find_spec(module) is None:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def configure_qt_platform() -> None:
    """Set QT_QPA_PLATFORM based on current system."""
    plat = sys.platform
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        del os.environ["QT_QPA_PLATFORM"]
    if "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "windows" if plat.startswith("win") else "xcb"

if __name__ == "__main__":
    ensure_packages()
    configure_qt_platform()
    try:
        from app.main import main
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
