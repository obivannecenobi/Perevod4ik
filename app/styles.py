"""Application style constants and font initialization."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import logging

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
FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


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
        Desired glow intensity (currently unused).
    width:
        Border width for the glow effect.
    """

    # ``intensity`` is kept for backward compatibility; only ``width``
    # influences the resulting border thickness at the moment.
    selectors = [
        "QTextEdit:focus",
        "QTextEdit:hover",
        "QLineEdit:focus",
        "QLineEdit:hover",
        "QTableView#glossary:focus",
        "QTableView#glossary:hover",
    ]
    selectors.extend([
        "QPushButton:hover",
        "QPushButton:focus",
    ])
    return ",\n".join(selectors) + f" {{\n    border: {width}px solid {color};\n}}"


def _register_font(filename: str) -> str | None:
    """Register *filename* from :data:`FONT_DIR` and return its family.

    If the font cannot be loaded, a warning is logged and ``None`` is
    returned so the caller can fall back to system fonts.
    """

    font_id = QtGui.QFontDatabase.addApplicationFont(str(FONT_DIR / filename))
    if font_id == -1:
        logging.warning("Failed to load %s; falling back to system fonts", filename)
        return None

    families = QtGui.QFontDatabase.applicationFontFamilies(font_id)
    if families:
        return families[0]

    logging.warning("Font %s registered but no families found; using system fonts", filename)
    return None


def init(settings: Any | None = None) -> None:
    """Load bundled fonts and apply user-selected colours."""

    global APP_BACKGROUND, ACCENT_COLOR, TEXT_COLOR, INTER_FONT, HEADER_FONT

    # Register bundled fonts so they are available in font pickers
    if family := _register_font("Inter-VariableFont_opsz,wght.ttf"):
        INTER_FONT = family
    else:
        INTER_FONT = QtGui.QFont().defaultFamily()

    header_family = _register_font("Cattedrale[RUSbypenka220]-Regular.ttf")
    if header_family:
        HEADER_FONT = header_family
    else:
        HEADER_FONT = QtGui.QFont().defaultFamily()

    if settings is not None:
        APP_BACKGROUND = getattr(settings, "app_background", APP_BACKGROUND)
        ACCENT_COLOR = getattr(settings, "accent_color", ACCENT_COLOR)
        TEXT_COLOR = getattr(settings, "text_color", TEXT_COLOR)
        INTER_FONT = getattr(settings, "base_font", INTER_FONT)
        HEADER_FONT = getattr(settings, "header_font", HEADER_FONT)
