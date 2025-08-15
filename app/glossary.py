from __future__ import annotations

"""Model-backed glossary table for efficient editing and persistence."""

from typing import List, Tuple

from PyQt6 import QtCore

from .services.glossary import Glossary


class GlossaryTableModel(QtCore.QAbstractTableModel):
    """Table model storing glossary entries.

    The model proxies a :class:`~app.services.glossary.Glossary` instance and
    persists changes to disk.  It is optimised for large numbers of rows by
    using Qt's model/view architecture and only creating items on demand.
    """

    def __init__(self, glossary: Glossary | None = None, parent=None) -> None:
        super().__init__(parent)
        self._glossary: Glossary | None = None
        self._rows: List[Tuple[str, str]] = []
        if glossary is not None:
            self.set_glossary(glossary)

    # ------------------------------------------------------------------
    # Qt model API
    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:  # noqa: D401
        return len(self._rows)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:  # noqa: D401
        return 2

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.ItemDataRole.DisplayRole):
        if role != QtCore.Qt.ItemDataRole.DisplayRole or orientation != QtCore.Qt.Orientation.Horizontal:
            return None
        return ["Source", "Target"][section]

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole):  # noqa: D401
        if not index.isValid() or index.row() >= len(self._rows):
            return None
        src, dst = self._rows[index.row()]
        if role in (QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.EditRole):
            return src if index.column() == 0 else dst
        return None

    def flags(self, index: QtCore.QModelIndex):  # noqa: D401
        if not index.isValid():
            return QtCore.Qt.ItemFlag.ItemIsEnabled
        return (
            QtCore.Qt.ItemFlag.ItemIsSelectable
            | QtCore.Qt.ItemFlag.ItemIsEnabled
            | QtCore.Qt.ItemFlag.ItemIsEditable
        )

    def setData(self, index: QtCore.QModelIndex, value, role: int = QtCore.Qt.ItemDataRole.EditRole):  # noqa: D401
        if role != QtCore.Qt.ItemDataRole.EditRole or not index.isValid():
            return False
        row, col = index.row(), index.column()
        src, dst = self._rows[row]
        text = str(value).strip()
        if col == 0:
            src = text
        else:
            dst = text
        self._rows[row] = (src, dst)
        if self._glossary is not None and src:
            self._glossary.add(src, dst)
            self._glossary.save()
        self.dataChanged.emit(index, index, [role])
        return True

    def insertRows(self, row: int, count: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()):
        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            self._rows.insert(row, ("", ""))
        self.endInsertRows()
        return True

    def removeRows(self, row: int, count: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        removed = self._rows[row : row + count]
        del self._rows[row : row + count]
        self.endRemoveRows()
        if self._glossary is not None:
            for src, _ in removed:
                if src:
                    self._glossary.remove(src)
            self._glossary.save()
        return True

    # ------------------------------------------------------------------
    # Convenience helpers
    def set_glossary(self, glossary: Glossary | None) -> None:
        """Populate the model from *glossary* entries."""

        self.beginResetModel()
        self._glossary = glossary
        if glossary is not None:
            self._rows = [(src, dst) for src, dst in glossary.entries.items()]
        else:
            self._rows = []
        self.endResetModel()

    def add_pair(self) -> None:
        self.insertRows(len(self._rows), 1)

    def remove_pair(self, row: int) -> None:
        if 0 <= row < len(self._rows):
            self.removeRows(row, 1)

    def glossary_entries(self) -> dict[str, str]:
        if self._glossary is not None:
            return dict(self._glossary.entries)
        return {src: dst for src, dst in self._rows if src}
