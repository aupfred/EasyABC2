# easyabc2/ui/play_range_selector_widget.py

from PySide6.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel
from PySide6.QtCore import Qt, Signal

from easyabc2 import _

class ClickableLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
        
class RangeSelectorWidget(QWidget):
    startClicked = Signal()
    endClicked = Signal()
    startToggled = Signal(bool)
    endToggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Start
        self.chk_start = QCheckBox()
        self.lbl_start = ClickableLabel(_("Start: 0"))
        self.lbl_start.setStyleSheet("padding: 2px;")

        # End
        self.chk_end = QCheckBox()
        self.lbl_end = ClickableLabel(_("End: 0"))
        self.lbl_end.setStyleSheet("padding: 2px;")

        layout.addWidget(self.chk_start)
        layout.addWidget(self.lbl_start)
        layout.addSpacing(10)
        layout.addWidget(self.chk_end)
        layout.addWidget(self.lbl_end)

        # Signals
        self.lbl_start.clicked.connect(self.startClicked)
        self.lbl_end.clicked.connect(self.endClicked)
        self.chk_start.toggled.connect(self.startToggled)
        self.chk_end.toggled.connect(self.endToggled)

    def set_start_value(self, tick):
        self.lbl_start.setText(_("Start: '{tick}'").format(tick=tick))

    def set_end_value(self, tick):
        self.lbl_end.setText(_("End: '{tick}'").format(tick=tick))

