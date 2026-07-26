# easyabc2/ui/code_editor.py

from PySide6.QtWidgets import QApplication, QPlainTextEdit, QWidget, QTextEdit
from PySide6.QtGui import QPainter, QColor, QTextFormat, QFont, QTextCursor
from PySide6.QtCore import QRect, QSize, Qt, QTimer, Signal

from easyabc2.syntax.abc_styler2 import ABCHighlighter
from easyabc2.utils.themes import EDITOR_THEMES
from easyabc2.utils.logging_utils import logger

logger.debug("[CodeEditor] Importing…")

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """
    Text editor with line number and API to:
    - get cursor position (abs, line, column)
    - get selected text
    """
    debouncedTextChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        prefs = QApplication.instance().prefs
        prefs.theme_editor_changed.connect(self.update_extra_selections)

        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._line_number_area = LineNumberArea(self)

        #font = QFont("DejaVu Sans Mono")
        font = QFont("Courier New")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(14)
        self.setFont(font)

        # Connections to update margin width
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # Timer to debounce text entry
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_debounced)

        # Connect native QPlainTextEdit signals
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        # Restart timer to avoid to many issue
        self._debounce_timer.start(300)  # 300 ms seems good trade off between responsiveness and performance

    def _emit_debounced(self):
        logger.debug("[Code Editor] Emit text changed")
        # Signal triggered if no new text entry
        self.debouncedTextChanged.emit()
        
    # --- Line number management ---

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor(245, 245, 245))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.darkGray)
                painter.drawText(
                    0,
                    top,
                    self._line_number_area.width() - 4,
                    self.fontMetrics().height(),
                    Qt.AlignRight | Qt.AlignVCenter,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    # --- Highlights ---

    def highlight_current_line(self):
        self.update_extra_selections()

    #def highlight_fieldx_lines(self):
    #    extra = []
    #    logger.debug("[CodeEditor] extra highlight")
#
    #    block = self.document().firstBlock()
    #    while block.isValid():
    #        if block.userState() == 1:  # 1 = bloc X:
    #            sel = QTextEdit.ExtraSelection()
    #            sel.format.setBackground(QColor("#FFF2CC"))
    #            sel.cursor = QTextCursor(block)
    #            sel.cursor.clearSelection()
    #            extra.append(sel)
    #        block = block.next()
#
    #    self.setExtraSelections(extra)
#
    #def update_fieldx_highlighting(self):
    #    self.update_extra_selections()
#
    #def update_extra_selections(self):
    #    selections = []
    #    prefs = QApplication.instance().prefs
    #    theme_name = prefs["editor_theme"]
    #    theme = EDITOR_THEMES.get(theme_name, EDITOR_THEMES["light"])
#
    #    cursor = self.textCursor()
    #    current_block = cursor.block()
#
    #    block = self.document().firstBlock()
    #    while block.isValid():
#
    #        is_current = (block == current_block)
    #        is_x = (block.userState() == 1)
#
    #        if is_current or is_x:
    #            sel = QTextEdit.ExtraSelection()
#
    #            # --- Background management ---
    #            if is_current and is_x:
    #                # Ligne courante + X:
    #                bg = QColor(theme["current_x_bg"])
    #            elif is_x:
    #                bg = QColor(theme["fieldx_bg"])
    #            else:
    #                bg = QColor(theme["current_line_bg"])
#
    #            sel.format.setBackground(bg)
    #            sel.format.setProperty(QTextFormat.FullWidthSelection, True)
#
    #            sel.cursor = QTextCursor(block)
    #            sel.cursor.clearSelection()
#
    #            selections.append(sel)
#
    #        block = block.next()
#
    #    self.setExtraSelections(selections)

    def update_extra_selections(self):
        """Generic highlight: only current line."""
        selections = []

        prefs = QApplication.instance().prefs
        theme = EDITOR_THEMES[prefs["editor_theme"]]

        cursor = self.textCursor()
        block = cursor.block()

        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor(theme["current_line_bg"]))
        sel.format.setProperty(QTextFormat.FullWidthSelection, True)
        sel.cursor = QTextCursor(block)
        sel.cursor.clearSelection()

        selections.append(sel)
        self.setExtraSelections(selections)
        
    # --- API cursor, position, selections... ---

    def cursor_absolute_position(self):
        """
        Return cursor position in number of chars from start of document (int)
        """
        return self.textCursor().position()

    def cursor_line_column(self):
        """
        Return (line, column), 1-based.
        """
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.positionInBlock() + 1
        return line, column

    def selection_range(self):
        """
        Return selection (start, end) absolute positions.
        """
        cursor = self.textCursor()
        return cursor.selectionStart(), cursor.selectionEnd()

    def selected_text(self, normalize_newlines=True):
        """
        Return selected text.
        Qt replace end of lines with U+2029, that can be normalised.
        """
        text = self.textCursor().selectedText()
        if normalize_newlines:
            text = text.replace("\u2029", "\n")
        return text

    def go_to_line(self, line_number: int):
        logger.debug(f"[CodeEditor] go to line: {line_number}")
        if line_number < 0 or line_number >= self.blockCount():
            return  # invalid line

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line_number)
        self.setTextCursor(cursor)

        # Adjust the scroll to have line at the top
        self.verticalScrollBar().setValue(line_number)

    def setCursorPosition(self, pos: int):
        cursor = self.textCursor()
        cursor.setPosition(pos)
        self.setTextCursor(cursor)

    def setCursorLineColumn(self, line: int, column: int = 0):
        block = self.document().findBlockByNumber(line)
        pos = block.position() + column
        self.setCursorPosition(pos)

    #def apply_preferences(self):
    #    self.prefs = QApplication.instance().prefs
    #    self.update_extra_selections()
