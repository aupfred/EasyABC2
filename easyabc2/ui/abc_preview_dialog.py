# easyabc2/ui/abc_preview_dialog.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout
from easyabc2.ui.abc_editor import ABCEditor
from pathlib import Path
from easyabc2 import _

class AbcPreviewDialog(QDialog):
    def __init__(self, title: str, path: Path, prefs, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)

        self.path = path

        layout = QVBoxLayout(self)

        # Create an ABC editor to ease the viewing
        self.editor = ABCEditor()
        self.editor.setReadOnly(True)
        #self.highlighter = ABCHighlighter(self.editor.document(), prefs)
        
        layout.addWidget(self.editor)
        
        self._reload_content()

        # --- Buttons ---
        btn_layout = QHBoxLayout()

        btn_reload = QPushButton(_("Reload"))
        btn_reload.clicked.connect(self._reload_content)
        btn_layout.addWidget(btn_reload)

        btn_close = QPushButton(_("Close"))
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _reload_content(self):
        if self.path and self.path.exists():
            content = self.path.read_text(encoding="utf-8")
            self.editor.setPlainText(content)
