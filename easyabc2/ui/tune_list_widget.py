# easyabc2/ui/tune_list_widget.py

from PySide6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QAbstractItemView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from easyabc2.models.abc_document import TuneInfo
from easyabc2.utils.logging_utils import logger
from easyabc2 import _

logger.debug("[TuneListWidget] Importing…")

class TuneListWidget(QWidget):
    tuneSelected = Signal(TuneInfo)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tunes: list[TuneInfo] = []
        self.suppress_callback = False
        self.row_items = {}
        
        self.icon_current = QIcon(":/icons/tune-current.svg")
        self.icon_playing = QIcon(":/icons/tune-playing.svg")
        self.icon_empty = QIcon()

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["X", _("Title"), _("Order")])
        self.table.setColumnHidden(2, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.table.itemSelectionChanged.connect(self._on_item_selected)

    def set_tunes(self, tunes: list[TuneInfo]):
        self.tunes = tunes
        self._refresh_table()

    def get_tunes(self):
        return self.tunes

    def _refresh_table(self):
        self.table.blockSignals(True)
        self.table.clearContents()
        self.table.setRowCount(0)

        for order, tune in enumerate(self.tunes):
            row = self.table.rowCount()
            self.table.insertRow(row)

            item_index = QTableWidgetItem(str(tune.index))
            item_title = QTableWidgetItem(tune.title)
            self.row_items[tune.index] = item_title # saved appart to ease the change of icons
            item_order = QTableWidgetItem()
            item_order.setData(Qt.DisplayRole, order)

            item_index.setTextAlignment(Qt.AlignCenter)
            item_order.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row, 0, item_index)
            self.table.setItem(row, 1, item_title)
            self.table.setItem(row, 2, item_order)

        self.table.sortItems(2, Qt.AscendingOrder)
        self.table.blockSignals(False)

    def select_tune(self, index: int):
        self.suppress_callback = True
        try:
            for row, tune in enumerate(self.tunes):
                if tune.index == index:
                    self.table.selectRow(row)
                    break
        finally:
            self.suppress_callback = False

    def update_icons(self, current_tune, audio_tune):
        for tune in self.tunes:
            item = self.row_items.get(tune.index)
            if not item:
                continue

            if tune == audio_tune:
                item.setIcon(self.icon_playing)
            elif tune == current_tune:
                item.setIcon(self.icon_current)
            else:
                item.setIcon(self.icon_empty)

    def _on_item_selected(self):
        if self.suppress_callback:
            return
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        #tune = self.tunes[int(self.table.item(row, 2).text())]
        order = self.table.item(row, 2).data(Qt.DisplayRole)
        tune = self.tunes[order]

        logger.info(f"[TuneListWidget] Clicked Tune {self.table.item(row, 0).text()}")
        logger.debug(f"[TuneListWidget] Clicked row: {row}")
        logger.debug(f"[TuneListWidget] TuneList item: {self.table.item(row, 0).text()}")
        logger.debug(f"[TuneListWidget] TuneList item: {self.table.item(row, 1).text()}")
        logger.debug(f"[TuneListWidget] TuneList item: {self.table.item(row, 2).text()}")
        logger.debug(f"[TuneListWidget] TuneInfo: {tune}")

        self.tuneSelected.emit(tune)
