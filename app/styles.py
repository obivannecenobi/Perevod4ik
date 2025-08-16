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

    selectors = [
        "QTextEdit:focus",
        "QTextEdit:hover",
        "QLineEdit:focus",
        "QLineEdit:hover",
        "QPushButton:focus",
        "QPushButton:hover",
        "QTableView#glossary:focus",
        "QTableView#glossary:hover",
    ]
    return ",\n".join(selectors) + f" {{\n    border: 1px solid {color};\n}}"


def neon_glow_rule(color: str, intensity: int, width: int) -> str:
    """Return a QSS snippet that highlights widgets on focus/hover.

    Qt's style engine lacks native drop-shadow effects.  A simple way to
    provide a visual highlight is to increase the border thickness, which
    we use here to emulate a glow.

    Parameters
    ----------
    color:
        Hex representation of the glow colour.
    intensity:
        Desired glow intensity (reserved for future use).
    width:
        Border width for the glow effect.
    """

    selectors = [
        "QTextEdit:focus",
        "QTextEdit:hover",
        "QLineEdit:focus",
        "QLineEdit:hover",
        "QPushButton:focus",
        "QPushButton:hover",
        "QTableView#glossary:focus",
        "QTableView#glossary:hover",
    ]
    return ",\n".join(selectors) + f" {{\n    border: {width}px solid {color};\n}}"


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
