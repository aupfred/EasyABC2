# easyabc2/ui/abc_editor.py

#from PySide6.QtWidgets import QApplication, QPlainTextEdit, QWidget, QTextEdit
#from PySide6.QtGui import QPainter, QColor, QTextFormat, QFont, QTextCursor
#from PySide6.QtCore import QRect, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import QApplication, QTextEdit
from PySide6.QtGui import QColor, QTextFormat, QTextCursor
from PySide6.QtCore import Signal

from easyabc2.ui.code_editor import CodeEditor
from easyabc2.syntax.abc_styler2 import ABCHighlighter
from easyabc2.utils.themes import EDITOR_THEMES
from easyabc2.utils.logging_utils import logger

class ABCEditor(CodeEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("[ABCEditor] Initializing...")

        prefs = QApplication.instance().prefs
        self.highlighter = ABCHighlighter(self.document(), prefs)

        prefs.theme_editor_changed.connect(self._rebuild_highlighter)

        self.document().contentsChanged.connect(self.update_fieldx_highlighting)


    def _rebuild_highlighter(self):
        logger.debug("[ABCEditor] Rebuild highlighter...")
        prefs = QApplication.instance().prefs
        self.highlighter = ABCHighlighter(self.document(), prefs)
        self.highlighter.rehighlight()

    def preview_theme(self, prefs):
        logger.debug("[ABCEditor] Preview theme...")
        #prefs = QApplication.instance().prefs
        self.highlighter = ABCHighlighter(self.document(), prefs)
        self.highlighter.rehighlight()

    def highlight_fieldx_lines(self):
        logger.debug("[ABCEditor] highlight_fieldx_lines...")
        extra = []

        block = self.document().firstBlock()
        while block.isValid():
            if block.userState() == 1:  # 1 = bloc X:
                sel = QTextEdit.ExtraSelection()
                sel.format.setBackground(QColor("#FFF2CC"))
                sel.cursor = QTextCursor(block)
                sel.cursor.clearSelection()
                extra.append(sel)
            block = block.next()

        self.setExtraSelections(extra)

    def update_fieldx_highlighting(self):
        logger.debug("[ABCEditor] update_fieldx_highlighting...")
        self.update_extra_selections()

    def update_extra_selections(self):
        logger.debug("[ABCEditor] update_extra_selections...")
        """ABC-specific highlight: current line + X: lines."""
        selections = []
        prefs = QApplication.instance().prefs
        theme = EDITOR_THEMES[prefs["editor_theme"]]

        cursor = self.textCursor()
        current_block = cursor.block()

        block = self.document().firstBlock()
        while block.isValid():

            is_current = (block == current_block)
            is_x = (block.userState() == 1)

            if is_current or is_x:
                sel = QTextEdit.ExtraSelection()

                if is_current and is_x:
                    bg = QColor(theme["current_x_bg"])
                elif is_x:
                    bg = QColor(theme["fieldx_bg"])
                else:
                    bg = QColor(theme["current_line_bg"])

                sel.format.setBackground(bg)
                sel.format.setProperty(QTextFormat.FullWidthSelection, True)
                sel.cursor = QTextCursor(block)
                sel.cursor.clearSelection()
                selections.append(sel)

            block = block.next()

        self.setExtraSelections(selections)
