"""Application style constants and font initialization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6 import QtGui

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


def _register_font(filename: str) -> str | None:
    """Register *filename* from :data:`FONT_DIR` and return its family."""

    font_id = QtGui.QFontDatabase.addApplicationFont(str(FONT_DIR / filename))
    if font_id != -1:
        families = QtGui.QFontDatabase.applicationFontFamilies(font_id)
        if families:
            return families[0]
    return None


def init(settings: Any | None = None) -> None:
    """Load bundled fonts and apply user-selected colours."""

    global APP_BACKGROUND, ACCENT_COLOR, TEXT_COLOR, INTER_FONT, HEADER_FONT

    if settings is not None:
        APP_BACKGROUND = getattr(settings, "app_background", APP_BACKGROUND)
        ACCENT_COLOR = getattr(settings, "accent_color", ACCENT_COLOR)
        TEXT_COLOR = getattr(settings, "text_color", TEXT_COLOR)

    # Register the Inter font for main text
    if family := _register_font("Inter-VariableFont_opsz,wght.ttf"):
        INTER_FONT = family

    # Register the Cattedrale font for headers
    family = _register_font("Cattedrale[RUSbypenka220]-Regular.ttf")
    if not family:
        raise RuntimeError("Failed to load Cattedrale[RUSbypenka220]-Regular.ttf")
    HEADER_FONT = family
