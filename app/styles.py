"""Application style constants and font initialization."""

from __future__ import annotations

from PyQt6 import QtGui
from pathlib import Path
from typing import Any

# Color palette (dark theme)
APP_BACKGROUND = "#212121"
FIELD_BACKGROUND = "#303030"
GLOSSARY_BACKGROUND = "#181818"
TEXT_COLOR = "#FFFFFF"
ACCENT_COLOR = "#00E5FF"

# Font family names are populated at runtime in :func:`init`.
INTER_FONT = "Inter"
HEADER_FONT = "Cattedrale"

# Directory containing bundled font files
FONT_DIR = Path(__file__).resolve().parent / "fonts"


def focus_hover_rule(color: str) -> str:
    """Return a QSS snippet highlighting widgets on focus/hover."""

    return f"""
QTextEdit:focus,
QTextEdit:hover,
QLineEdit:focus,
QLineEdit:hover,
QTableWidget#glossary:focus,
QTableWidget#glossary:hover {{
    border: 1px solid {color};
}}
""".strip()


def neon_glow_rule(color: str, intensity: int) -> str:
    """Return a QSS snippet that adds an outer "neon" glow.

    Parameters
    ----------
    color:
        Hex representation of the glow colour.
    intensity:
        Blur radius of the glow in pixels.
    """

    return f"""
QTextEdit:focus,
QTextEdit:hover,
QLineEdit:focus,
QLineEdit:hover,
QTableWidget#glossary:focus,
QTableWidget#glossary:hover {{
    border: 1px solid {color};
    box-shadow: 0 0 {intensity}px {color};
}}
""".strip()


def init(settings: Any | None = None) -> None:
    """Load bundled fonts and apply user-selected colours."""

    if settings is not None:
        global APP_BACKGROUND, ACCENT_COLOR, TEXT_COLOR
        APP_BACKGROUND = getattr(settings, "app_background", APP_BACKGROUND)
        ACCENT_COLOR = getattr(settings, "accent_color", ACCENT_COLOR)
        TEXT_COLOR = getattr(settings, "text_color", TEXT_COLOR)

    inter_id = QtGui.QFontDatabase.addApplicationFont(
        str(FONT_DIR / "Inter-VariableFont_opsz,wght.ttf")
    )
    if inter_id != -1:
        families = QtGui.QFontDatabase.applicationFontFamilies(inter_id)
        if families:
            global INTER_FONT
            INTER_FONT = families[0]

    catt_id = QtGui.QFontDatabase.addApplicationFont(
        str(FONT_DIR / "Cattedrale[RUSbypenka220]-Regular.ttf")
    )
    if catt_id != -1:
        families = QtGui.QFontDatabase.applicationFontFamilies(catt_id)
        if families:
            global HEADER_FONT
            HEADER_FONT = families[0]

