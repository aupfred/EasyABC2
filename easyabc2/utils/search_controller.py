# easyabc2/utils/search_controller.py

from pathlib import Path
import re
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import QTimer

from easyabc2.utils.easyabc_utils import read_abc_file, normalize_abc_text
from easyabc2.utils.logging_utils import logger

class SearchController:
    def __init__(self):
        logger.debug("[SearchController] Init")
        self.last_query = None
        self.last_options = None
        self.last_editor = None

    # -------------------------
    #  Helpers
    # -------------------------
    @property
    def app(self):
        return QApplication.instance()

    def all_mainwindows(self):
        return self.app.all_mainwindows()
        from easyabc2.ui.main_window import MainWindow
        return [
            w for w in self.app.topLevelWidgets()
            if isinstance(w, MainWindow)
        ]

    def current_mainwindow(self):
        return self.app.current_mainwindow()
        # fenêtre active en priorité
        for w in self.all_mainwindows():
            if w.isActiveWindow():
                return w

        # fallback : première fenêtre
        wins = self.all_mainwindows()
        return wins[0] if wins else None

    def _get_current_editor(self):
        win = self.current_mainwindow()
        if not win:
            return None

        tab = win.tabs.currentWidget()
        if not tab:
            return None

        return tab.editor

    def _compile_pattern(self, query, options):
        flags = 0
        if not options.get("case"):
            flags |= re.IGNORECASE

        if options.get("regex"):
            flags |= re.MULTILINE
            return re.compile(query, flags)

        if options.get("word"):
            query = r"\b" + re.escape(query) + r"\b"
            return re.compile(query, flags)

        return re.compile(re.escape(query), flags)

    # -------------------------
    #  Start search
    # -------------------------
    def start_search(self, query, options):
        self.last_query = query
        self.last_options = options
        self.last_editor = self._get_current_editor()

        if not self.last_editor:
            return

        self.find_next()

    # -------------------------
    #  Find next / previous
    # -------------------------
    def find_next(self):
        if not self.last_editor or not self.last_query:
            return

        pattern = self._compile_pattern(self.last_query, self.last_options)
        doc = self.last_editor.document()
        cursor = self.last_editor.textCursor()

        start = cursor.selectionEnd()
        text = doc.toPlainText()

        match = pattern.search(text, start)
        if not match:
            match = pattern.search(text, 0)
            if not match:
                return

        new_cursor = self.last_editor.textCursor()
        new_cursor.setPosition(match.start())
        new_cursor.setPosition(match.end(), QTextCursor.KeepAnchor)
        self.last_editor.setTextCursor(new_cursor)

    def find_previous(self):
        if not self.last_editor or not self.last_query:
            return

        pattern = self._compile_pattern(self.last_query, self.last_options)
        doc = self.last_editor.document()
        cursor = self.last_editor.textCursor()

        end = cursor.selectionStart()
        text = doc.toPlainText()

        matches = list(pattern.finditer(text))
        prev = None
        for m in matches:
            if m.end() <= end:
                prev = m

        if not prev:
            if matches:
                prev = matches[-1]
            else:
                return

        new_cursor = self.last_editor.textCursor()
        new_cursor.setPosition(prev.start())
        new_cursor.setPosition(prev.end(), QTextCursor.KeepAnchor)
        self.last_editor.setTextCursor(new_cursor)

    # -------------------------
    #  Replace
    # -------------------------
    def replace_one(self, replacement):
        pass
    
    def replace_all_in_tab(self, tab, replacement):
        pass
    
    def replace_all_in_window(self, win, replacement):
        pass
    
    def replace_all_in_all_documents(self, replacement):
        pass
    
    def replace_all_in_folder(self, replacement):
        # This is to be implemented in Main Window
        pass
    
    def replace_current(self, replacement):
        editor = self.last_editor
        if not editor:
            return

        cursor = editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(replacement)

        self.find_next()

    def replace_all(self, replacement):
        editor = self.last_editor
        if not editor:
            return

        pattern = self._compile_pattern(self.last_query, self.last_options)
        text = editor.toPlainText()
        new_text = pattern.sub(replacement, text)
        editor.setPlainText(new_text)

    # -------------------------
    #  Search functions
    # -------------------------
    def search_in_all_documents(self, query, options):
        results = []

        logger.debug(f"[Search Controller] search in all documents {query} {options}")
        i = 0
        for win in self.all_mainwindows():
            logger.debug(f"[Search Controller] search in all documents, win {i}")
            results.extend(self.search_in_window(win, query, options))
            i+=1
        self.last_results = results
        return results

    def search_in_window(self, win, query, options):
        self.last_query = query
        self.last_options = options
        logger.debug(f"[Search Controller] search in current window {win} {query} {options}")
        pattern = self._compile_pattern(query, options)
        results = []
        if win is None:
            win = self.current_mainwindow()

        for i in range(win.tabs.count()):
            tab = win.tabs.widget(i)
            results.extend(self._search_in_tab(win, tab, pattern))

        self.last_results = results
        return results

    def search_in_current_document(self, query, options):
        self.last_query = query
        self.last_options = options
        logger.debug(f"[Search Controller] search in current document {query} {options}")
        pattern = self._compile_pattern(query, options)
        win = self.current_mainwindow()
        tab = win.tabs.currentWidget()
        self.last_results = self._search_in_tab(win, tab, pattern)
        return self.last_results

    def _search_in_tab(self, win, tab, pattern):
        text = tab.editor.document().toPlainText()
        file_path = tab.current_file
        return self._search_in_text(text, pattern, file_path, win, tab)

    def _search_in_text(self, text, pattern, file_path, win=None, tab=None):
        logger.debug(f"[Search Controller] search in text {file_path}, {pattern}, {win}, {tab}")
        results = []

        for m in pattern.finditer(text):
            line = text.count("\n", 0, m.start()) + 1

            results.append({
                "file_path": file_path,
                "window": win,              # None if folder
                "tab": tab,                 # None if folder
                "line": line,
                "start": m.start(),
                "end": m.end(),
                "matched_text": m.group(),
                #"preview": m.group().replace("\n", " "),
            })

        logger.debug(f"[Search Controller] found {results}")
        return results

    def search_in_folder(self, folder, query, options):
        self.last_query = query
        self.last_options = options
        logger.debug(f"[Search Controller] search in folder {folder} {query} {options}")
        pattern = self._compile_pattern(query, options)
        results = []

        for file_path in Path(folder).rglob("*.abc"):
            try:
                text, encoding = read_abc_file(file_path)
                text = normalize_abc_text(text)
                #text = Path(file_path).read_text(encoding="utf-8")
            except Exception:
                continue

            results.extend(self._search_in_text(text, pattern, file_path))

        self.last_results = results
        return results

    # -------------------------
    #  Go to result
    # -------------------------
    def go_to_result(self, result):
        if result["tab"] is not None:
            win = result["window"]
            tab = result["tab"]

            win.show()
            win.raise_()
            win.activateWindow()

            index = win.tabs.indexOf(tab)
            if index != -1:
                win.tabs.setCurrentIndex(index)

            def select():
                editor = tab.editor
                cursor = editor.textCursor()
                cursor.setPosition(result["start"])
                cursor.setPosition(result["end"], QTextCursor.KeepAnchor)
                editor.setTextCursor(cursor)
                editor.setFocus()

            QTimer.singleShot(0, select)
            return

        file_path = result["file_path"]
        win = self.current_mainwindow()

        win.open_file_from_search(file_path, result["start"], result["end"])

    def replace_one(self, result, replacement):
        """
        Public API: performs replace and returns updated results.
        """
        self._replace_one(result, replacement)
        return self.last_results

    def _replace_one(self, result, replacement):
        """
        Internal replace: returns True if replaced, False otherwise.
        Replace result with replacement and adjust results.
        """
        tab = result["tab"]
        editor = tab.editor

        cursor = editor.textCursor()
        cursor.setPosition(result["start"])
        cursor.setPosition(result["end"], QTextCursor.KeepAnchor)
        selected = cursor.selectedText()
        if selected != result["matched_text"]:
            return False
        cursor.insertText(replacement)

        old_len = result["end"] - result["start"]
        new_len = len(replacement)
        delta = new_len - old_len

        if delta != 0:
            file_path = result["file_path"]
            replaced_end = result["end"]

            for r in self.last_results:
                if r["file_path"] == file_path and r["start"] > replaced_end:
                    r["start"] += delta
                    r["end"] += delta

        return True

    def replace_in_tab(self, tab, replacement):
        results = [r for r in self.last_results if r["tab"] is tab]

        count = 0
        for r in results:
            if self._replace_one(r, replacement):
                count += 1

        return count

    def replace_all_in_window(self, replacement, win):
        total = 0
        for i in range(win.tabs.count()):
            tab = win.tabs.widget(i)
            total += self.replace_in_tab(tab, replacement)
        return total

    def replace_all_in_all_documents(self, replacement):
        total = 0
        for win in QApplication.instance().main_windows:
            total += self.replace_all_in_window(replacement, win)
        return total

    def replace_all_in_folder(self, replacement, win):
        return self.replace_all_in_window(replacement, win)
