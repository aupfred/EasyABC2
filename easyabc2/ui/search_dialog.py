# easyabc2/ui/widgets/search_dialog.py

from pathlib import Path
import re

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QListWidget, QListWidgetItem, QWidget,
    QComboBox, QFileDialog, 
)
from PySide6.QtCore import Qt, Signal, QTimer

from easyabc2.utils.logging_utils import logger
from easyabc2 import _, n_

class SearchDialog(QDialog):
    search_requested = Signal(str, dict)
    next_requested = Signal()
    previous_requested = Signal()
    replace_requested = Signal(object, str)        # (result, replacement)
    replace_all_requested = Signal(str, str)       # (replacement, scope)
    replace_all_in_folder_requested = Signal(list, str)  # (files, replacement)
    search_all_documents_requested = Signal(str, dict)
    search_folder_requested = Signal(str, str, dict)
    search_fields_requested = Signal(str, dict)

    def __init__(self, parent=None):
        logger.debug("[Search Dialog] Init...")
        super().__init__(parent)
        self.setWindowTitle(_("Search"))
        self.setWindowModality(Qt.NonModal)
        self.setMinimumWidth(500)
        self.mode = "find"   # "find", "replace"
        self.real_result_count = 0
        self.current_result_index = -1

        layout = QVBoxLayout(self)

        # --- Search field ---
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel(_("Find:")))
        self.search_edit = QLineEdit()
        search_row.addWidget(self.search_edit)
        layout.addLayout(search_row)

        # --- Replace field ---
        self.replace_row = QHBoxLayout()
        self.replace_row.addWidget(QLabel(_("Replace:")))
        self.replace_edit = QLineEdit()
        self.replace_row.addWidget(self.replace_edit)
        layout.addLayout(self.replace_row)

        # --- Options ---
        options_row = QHBoxLayout()
        self.case_cb = QCheckBox(_("Case sensitive"))
        self.word_cb = QCheckBox(_("Whole word"))
        self.regex_cb = QCheckBox(_("Regex"))
        options_row.addWidget(self.case_cb)
        options_row.addWidget(self.word_cb)
        options_row.addWidget(self.regex_cb)
        layout.addLayout(options_row)

        # --- ABC fields ---
        fields_row = QHBoxLayout()
        self.cb_title = QCheckBox(_("T: Title"))
        self.cb_composer = QCheckBox(_("C: Composer"))
        self.cb_rythm = QCheckBox(_("R: Rhythm"))
        self.cb_key = QCheckBox(_("K: Key"))
        self.cb_meter = QCheckBox(_("M: Meter"))
        self.cb_length = QCheckBox(_("L: Length"))
        self.cb_tempo = QCheckBox(_("Q: Tempo"))

        fields_row.addWidget(self.cb_title)
        fields_row.addWidget(self.cb_composer)
        fields_row.addWidget(self.cb_rythm)
        fields_row.addWidget(self.cb_key)
        fields_row.addWidget(self.cb_meter)
        fields_row.addWidget(self.cb_length)
        fields_row.addWidget(self.cb_tempo)

        layout.addLayout(fields_row)

        # --- Regexp preview ---
        regexp_row = QHBoxLayout()
        self.regexp_label = QLabel(_("Regexp:"))
        self.regexp_preview = QLineEdit()
        self.regexp_preview.setReadOnly(True)
        regexp_row.addWidget(self.regexp_label)
        regexp_row.addWidget(self.regexp_preview)
        layout.addLayout(regexp_row)

        # --- Scope ---
        scope_row = QHBoxLayout()
        scope_row.addWidget(QLabel(_("Scope:")))
        self.scope_combo = QComboBox()
        self.scope_combo.addItem(_("Current document"), "current")
        self.scope_combo.addItem(_("All open documents"), "open_docs")
        self.scope_combo.addItem(_("Folder…"), "folder")
        scope_row.addWidget(self.scope_combo)
        layout.addLayout(scope_row)

        # --- Folder ---
        self.folder_row = QHBoxLayout()
        self.folder_label = QLabel(_("Find in folder:"))
        self.folder_row.addWidget(self.folder_label)
        def browse():
            path = QFileDialog.getExistingDirectory(self, _("Choose a directory"))
            if path:
                self.folder_path.setText(path)

        self.folder_path = QLineEdit()
        self.folder_row.addWidget(self.folder_path)
        self.folder_btn = QPushButton(_("Browse…"))
        self.folder_btn.clicked.connect(browse)
        self.folder_row.addWidget(self.folder_btn)
        layout.addLayout(self.folder_row)

        # --- Buttons ---
        btn_row = QHBoxLayout()
        self.btn_find = QPushButton(_("Find"))
        self.btn_next = QPushButton(_("Next"))
        self.btn_prev = QPushButton(_("Previous"))
        self.btn_replace = QPushButton(_("Replace"))
        self.btn_replace_all = QPushButton(_("Replace All"))

        btn_row.addWidget(self.btn_find)
        btn_row.addWidget(self.btn_next)
        btn_row.addWidget(self.btn_prev)
        btn_row.addWidget(self.btn_replace)
        btn_row.addWidget(self.btn_replace_all)
        layout.addLayout(btn_row)

        # --- Global search ---
        #global_row = QHBoxLayout()
        #self.btn_search_all_docs = QPushButton("Search in all documents")
        #self.btn_search_folder = QPushButton("Search in folder…")
        #global_row.addWidget(self.btn_search_all_docs)
        #global_row.addWidget(self.btn_search_folder)
        #layout.addLayout(global_row)

        # --- Results list ---
        self.results_count_label = QLabel(_("0 result"))
        layout.addWidget(self.results_count_label)
        self.results_list = QListWidget()
        self.results_list.setMinimumHeight(60)   # 3–4 lines
        self.results_list.setMaximumHeight(250)  # ~10 lines
        layout.addWidget(self.results_list)

        self.btn_find.setDefault(True)
        self.btn_find.setAutoDefault(True)
        self.btn_replace.setDefault(False)
        self.btn_replace.setAutoDefault(False)
        self.folder_btn.setDefault(False)
        self.folder_btn.setAutoDefault(False)
        self.btn_next.setDefault(False)
        self.btn_prev.setDefault(False)

        # --- Connections ---
        self.scope_combo.currentIndexChanged.connect(self._on_search_options_changed)
        self.btn_find.clicked.connect(self._emit_search)
        self.btn_next.clicked.connect(self.next_result)
        self.btn_prev.clicked.connect(self.previous_result)
        self.btn_replace.clicked.connect(self._emit_replace)
        self.btn_replace_all.clicked.connect(self._emit_replace_all)
        #self.btn_search_all_docs.clicked.connect(self._emit_search_all_docs)
        #self.btn_search_folder.clicked.connect(self._emit_search_folder)
        self.results_list.itemClicked.connect(self._on_result_selected)

        self.search_edit.textChanged.connect(self.update_regexp_preview)
        self.case_cb.stateChanged.connect(self.update_regexp_preview)
        self.word_cb.stateChanged.connect(self.update_regexp_preview)
        self.regex_cb.stateChanged.connect(self.update_regexp_preview)

        self.cb_title.stateChanged.connect(self.update_regexp_preview)
        self.cb_composer.stateChanged.connect(self.update_regexp_preview)
        self.cb_rythm.stateChanged.connect(self.update_regexp_preview)
        self.cb_key.stateChanged.connect(self.update_regexp_preview)
        self.cb_meter.stateChanged.connect(self.update_regexp_preview)
        self.cb_length.stateChanged.connect(self.update_regexp_preview)
        self.cb_tempo.stateChanged.connect(self.update_regexp_preview)
        
        self._update_action_buttons()

    def _options(self):
        fields_selected = bool(self.selected_fields())
        regex_mode = self.regex_cb.isChecked() or fields_selected

        return {
            "case": self.case_cb.isChecked(),
            "word": self.word_cb.isChecked() and not regex_mode,
            "regex": regex_mode,
        }

    def _on_search_options_changed(self):
        self.results_list.clear()
        self.real_result_count = 0
        self.current_result_index = -1
        self._update_visibility()

    def set_mode(self, mode):
        if mode not in ("find", "replace", "open_docs", "folder"):
            logger.error("[Search Dialog] Mode not allowed")
            return

        self.mode = mode

        if mode == "find":
            scope = "current"
        elif mode == "open_docs":
            scope = "open_docs"
        elif mode == "folder":
            scope = "folder"
        else:
            scope = None  # replace will be managed later on

        if scope is not None:
            index = self.scope_combo.findData(scope)
            if index >= 0:
                self.scope_combo.setCurrentIndex(index)

        self._update_visibility()

    def build_field_regexp(self):
        fields = self.selected_fields()
        query = self.search_edit.text()

        if not fields:
            return ""

        # (T|C|R)
        prefix = "(" + "|".join(fields) + ")"

        # Whole word ?
        if self.word_cb.isChecked():
            q = r"\b" + re.escape(query) + r"\b"
        else:
            q = re.escape(query)

        # Final regexp
        return rf"^{prefix}:\s*.*{q}"

    def update_regexp_preview(self):
        self._on_search_options_changed()
        if self.mode == "replace":
            self.regexp_preview.clear()
            return

        #regexp = self.build_field_regexp()
        #self.regexp_preview.setText(regexp)
        fields_selected = bool(self.selected_fields())

        # Si des champs ABC sont cochés → forcer regex
        self.regex_cb.setEnabled(not fields_selected)
        if fields_selected:
            self.regex_cb.setChecked(True)

        regexp = self.build_field_regexp()
        self.regexp_preview.setText(regexp)

    def selected_fields(self):
        fields = []
        if self.cb_title.isChecked(): fields.append("T")
        if self.cb_composer.isChecked(): fields.append("C")
        if self.cb_rythm.isChecked(): fields.append("R")
        if self.cb_key.isChecked(): fields.append("K")
        if self.cb_meter.isChecked(): fields.append("M")
        if self.cb_length.isChecked(): fields.append("L")
        if self.cb_tempo.isChecked(): fields.append("Q")
        return fields

    def _emit_search(self):
        self.show_results(None, True)
        #QApplication.processEvents()
        def emit():
            regexp = self.regexp_preview.text() or self.search_edit.text()
            options = self._options()
            scope = self.scope_combo.currentData()

            if scope == "current":
                self.search_requested.emit(regexp, options)

            elif scope == "open_docs":
                self.search_all_documents_requested.emit(regexp, options)

            elif scope == "folder":
                folder = self.folder_path.text()
                self.search_folder_requested.emit(regexp, folder, options)

        QTimer.singleShot(20, emit)
        #QApplication.processEvents()

    def _emit_replace(self):
        count = self.results_list.count()
        if count == 0:
            return
        item = self.results_list.currentItem()
        if not item:
            return

        result = item.data(Qt.UserRole)
        if result is None:
            return
        
        replacement = self.replace_edit.text()
        logger.debug(f"[Search Dialog] replace request for: {result} replace: {replacement}")
        self.replace_requested.emit(result, replacement)

    def _emit_replace_all(self):
        self.replace_all_requested.emit(self.replace_edit.text())

    def _emit_replace_all(self):
        replacement = self.replace_edit.text()
        scope = self.scope_combo.currentData()

        logger.debug(f"[Search Dialog] replace all request: scope={scope}, replacement={replacement}")

        if scope in ("current", "open_docs"):
            # MainWindow to forward request to search controller
            self.replace_all_requested.emit(replacement, scope)
            return

        if scope == "folder":
            # MainWindow to open files and request replacement in window self.current_results
            files = sorted({r["file_path"] for r in self.current_results})

            if not files:
                return

            logger.debug(f"[Search Dialog] replace all in folder: {files}")
            self.replace_all_in_folder_requested.emit(files, replacement)
            return

    def _emit_search_all_docs(self):
        self.show_results(None, True)
        regexp = self.regexp_preview.text() or self.search_edit.text()
        self.search_all_documents_requested.emit(regexp, self._options())

    def _emit_search_folder(self):
        self.show_results(None, True)
        regexp = self.regexp_preview.text() or self.search_edit.text()
        self.search_folder_requested.emit(regexp, self._options())

    def _is_current_selection_valid(self):
        if self.current_result_index < 0:
            logger.debug("no selection")
            return False

        item = self.results_list.item(self.current_result_index)
        if not item:
            logger.debug("no item")
            return False

        result = item.data(Qt.UserRole)
        if not result:
            logger.debug("no result")
            return False

        tab = result["tab"]
        editor = tab.editor
        cursor = editor.textCursor()
        
        if cursor.selectionStart() != result["start"]:
            logger.debug("not start")
            return False
        if cursor.selectionEnd() != result["end"]:
            logger.debug("not end")
            return False

        selected_text = cursor.selectedText()
        expected_text = result["matched_text"]
        test = selected_text == expected_text
        
        return selected_text == expected_text

    def _update_visibility(self):
        # Replace UI only in mode replace
        is_replace = (self.mode == "replace")
        self._set_layout_visible(self.replace_row, is_replace)
        self.btn_replace.setVisible(is_replace)
        self.btn_replace_all.setVisible(is_replace)

        # Folder row visible only if scope = folder
        scope = self.scope_combo.currentData()
        is_folder = (scope == "folder")

        self.folder_label.setEnabled(is_folder)
        self.folder_path.setEnabled(is_folder)
        self.folder_btn.setEnabled(is_folder)

        self.adjustSize()
        self._update_action_buttons()

    def _update_action_buttons(self):
        is_replace = (self.mode == "replace")
        real_count = self.real_result_count
        selection_valid = self._is_current_selection_valid()
        self.results_count_label.setText(
            n_("%d result", "%d results", real_count) % real_count
        )

        # Replace One
        self.btn_replace.setEnabled(
            is_replace and real_count >= 1 and self.current_result_index >= 0 and selection_valid
        )

        # Replace All
        self.btn_replace_all.setEnabled(
            is_replace and real_count >= 2
        )

        # Navigation
        self.btn_prev.setEnabled(real_count >= 2 and self.current_result_index > 0)
        self.btn_next.setEnabled(real_count >= 2 and self.current_result_index < real_count - 1)

    def _set_layout_visible(self, layout, visible):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setVisible(visible)

    def _on_result_selected(self, item):
        if item is None:
            return
        row = self.results_list.row(item)
        if row != -1:
            self.current_result_index = row
        result = item.data(Qt.UserRole)
        if result is None:
            self._update_action_buttons()
            return
        logger.debug(f"[Search Dialog] selected result: {result}")
        controller = QApplication.instance().search_controller
        controller.go_to_result(result)
        self.raise_()
        self.activateWindow()
        QTimer.singleShot(0, self._update_action_buttons)
        #self._update_action_buttons()
        #self._update_action_buttons()

    def show_results(self, results, searching = False):
        self.results_list.blockSignals(True)
        self.results_list.clear()

        if searching:
            self.real_result_count = 0
            item = QListWidgetItem(_("Searching..."))
            item.setFlags(Qt.NoItemFlags)
            self.results_list.addItem(item)
            self.current_result_index = -1
            self._update_action_buttons()
            return

        if not results:
            self.real_result_count = 0
            item = QListWidgetItem(_("No result found"))
            item.setFlags(Qt.NoItemFlags)
            self.results_list.addItem(item)
            self.current_result_index = -1
            self._update_action_buttons()
            return

        self.real_result_count = len(results)

        for r in results:
            file_path = r["file_path"]
            line = r["line"]
            preview = r["matched_text"].replace("\n", " ")

            if r["tab"] is not None:
                win = r["window"]
                tab = r["tab"]
                index = win.tabs.indexOf(tab)
                title = win.tabs.tabText(index)

                if not title:
                    title = Path(file_path).name

            else:
                title = Path(file_path).name

            text = _("[{file}] line {line}: {preview}").format(
                file=title,
                line=line,
                preview=preview
            )

            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, r)
            self.results_list.addItem(item)

        self.current_result_index = -1
        if self.mode == "find":
            if results:
                self.current_result_index = 0
                self.results_list.setCurrentRow(0)
                self.results_list.blockSignals(False)
                QTimer.singleShot(0, self._activate_current_result)
        else:
            self.results_list.clearSelection()
            self.results_list.blockSignals(False)
        self._update_action_buttons()

    def next_result(self):
        count = self.results_list.count()
        if count == 0:
            return

        if self.current_result_index < count - 1:
            self.current_result_index += 1
            self.results_list.setCurrentRow(self.current_result_index)
            self._activate_current_result()
            QTimer.singleShot(0, self._update_action_buttons)
            #self._update_action_buttons()

    def previous_result(self):
        if self.current_result_index > 0:
            self.current_result_index -= 1
            self.results_list.setCurrentRow(self.current_result_index)
            self._activate_current_result()
            QTimer.singleShot(0, self._update_action_buttons)
            #self._update_action_buttons()

    def _activate_current_result(self):
        item = self.results_list.currentItem()
        if not item:
            return

        self._on_result_selected(item)
        #result = item.data(Qt.UserRole)
        #if result:
        #    self.search_controller.go_to_result(result)

    def on_replace_done(self):
        self.next_result()

    def update_results(self, results):
        if self.results_list.count() != len(results):
            logger.error("[Search Dialog] new result is not according to existing resetting list")
            self.show_results(results)
            return

        for i in range(len(results)):
            item = self.results_list.item(i)
            r = results[i]
            item.setData(Qt.UserRole, r)

    #def _on_search_options_changed(self):
    #    self.results_list.clear()
    #    self.current_result_index = -1
#
    #    # Désactiver les boutons
    #    self.btn_replace.setEnabled(False)
    #    self.btn_replace_all.setEnabled(False)
#
    #    # Effacer l’affichage du compteur
    #    self.lbl_count.setText("0 result")
