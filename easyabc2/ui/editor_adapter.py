from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import QTextCursor

class QtEditorAdapter:
    def __init__(self, editor: QPlainTextEdit):
        self.editor = editor

    # --- Whole text ---
    def GetText(self):
        return self.editor.toPlainText()

    def GetTextLength(self):
        return len(self.editor.toPlainText())

    # --- Position / selection ---
    def GetCurrentPos(self):
        return self.editor.textCursor().position()

    def SetCurrentPos(self, pos):
        cursor = self.editor.textCursor()
        cursor.setPosition(pos)
        self.editor.setTextCursor(cursor)

    def GetSelection(self):
        cursor = self.editor.textCursor()
        return cursor.selectionStart(), cursor.selectionEnd()

    def SetSelection(self, start, end):
        cursor = self.editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        self.editor.setTextCursor(cursor)

    # --- Lines ---
    def GetCurrentLine(self):
        return self.editor.textCursor().blockNumber()

    def GetLine(self, line_no):
        block = self.editor.document().findBlockByNumber(line_no)
        return block.text()

    def GetLineCount(self):
        return self.editor.document().blockCount()

    def PositionFromLine(self, line_no):
        block = self.editor.document().findBlockByNumber(line_no)
        return block.position()

    def GetLineEndPosition(self, line_no):
        block = self.editor.document().findBlockByNumber(line_no)
        return block.position() + block.length() - 1
    
    def LineFromPosition(self, pos):
        block = self.editor.document().findBlock(pos)
        return block.blockNumber()

    # --- Replace ---
    def Replace(self, start, end, text):
        cursor = self.editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        cursor.insertText(text)

    def ReplaceSelection(self, text):
        cursor = self.editor.textCursor()
        cursor.insertText(text)

    def AddText(self, text):
        cursor = self.editor.textCursor()
        cursor.insertText(text)

    # --- Utils ---
    def GetTextRange(self, start, end):
        cursor = self.editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        return cursor.selectedText()
    
    def BeginUndoAction(self):
        pass

    def EndUndoAction(self):
        pass
