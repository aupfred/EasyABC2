# easyabc2/ui/txt_preview_dialog.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout
from easyabc2.ui.code_editor import CodeEditor, ABCHighlighter
from easyabc2 import _
from pathlib import Path

class TxtPreviewDialog(QDialog):
    def __init__(self, title: str, path: Path, prefs, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)

        self.path = path

        layout = QVBoxLayout(self)

        self.editor = CodeEditor()
        self.editor.setReadOnly(True)
        
        layout.addWidget(self.editor)
        
        self.reload_content()

        # --- Boutons ---
        btn_layout = QHBoxLayout()

        btn_reload = QPushButton(_("Reload"))
        btn_reload.clicked.connect(self.reload_content)
        btn_layout.addWidget(btn_reload)

        btn_close = QPushButton(_("Close"))
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def reload_content(self):
        if self.path and self.path.exists():
            content = self.path.read_text(encoding="utf-8")
            self.editor.setPlainText(content)
