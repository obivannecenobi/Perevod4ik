"""Application style constants and font initialization."""

from __future__ import annotations

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


def init() -> None:
    """Load bundled fonts and expose their family names.

    The application ships with custom fonts (Inter and Cattedrale).  They are
    added to the Qt font database when the UI is initialised so that widgets can
    reference them by family name.  If loading fails, the default family names
    declared above are kept.
    """

    font_db = QtGui.QFontDatabase()

    inter_id = font_db.addApplicationFont("Inter-VariableFont_opsz,wght.ttf")
    if inter_id != -1:
        families = font_db.applicationFontFamilies(inter_id)
        if families:
            global INTER_FONT
            INTER_FONT = families[0]

    catt_id = font_db.addApplicationFont("Cattedrale[RUSbypenka220]-Regular.ttf")
    if catt_id != -1:
        families = font_db.applicationFontFamilies(catt_id)
        if families:
            global HEADER_FONT
            HEADER_FONT = families[0]

