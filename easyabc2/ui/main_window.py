# easyabc2/ui/main_window.py

import sys
import locale
import json
import os
import subprocess

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QListWidget, QTabWidget,
    QMessageBox, QFileDialog, QInputDialog, QMenu,
    QSlider, QWidgetAction, QWidget, QHBoxLayout, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QByteArray, QPoint
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QAction, QIcon, QTextCursor
#from PySide6.QtPrintSupport import QPrinter, QPrintDialog

from easyabc2.utils.easyabc_utils import get_app_data_dir, get_temp_dir, save_temp_abc, save_temp_svg, get_temp_dir_for_tab
from easyabc2.utils.preferences import UserPreferences
#from easyabc2.utils.search_controller import SearchController
from easyabc2.ui.tune_list_widget import TuneListWidget
from easyabc2.ui.preferences_dialog import PreferencesDialog
from easyabc2.ui.document_tab import DocumentTab
from easyabc2.ui.play_range_selector_widget import RangeSelectorWidget
#from easyabc2.ui.search_dialog import SearchDialog
from easyabc2.models.abc_document import AbcDocument, TuneInfo
import easyabc2.resources.icons_rc
from easyabc2.utils.logging_utils import logger
from easyabc2 import _

logger.debug("[MainWindow] Importing MainWindow…")

class MainWindow(QMainWindow):
    def __init__(self, app_data_dir):
        super().__init__()

        self.app_data_dir = app_data_dir
        self.temp_dir = get_temp_dir(self.app_data_dir)

        # 1) Build manin widgets
        self._create_central_widgets()

        # 2) Build actions
        self._create_actions()

        # 3) Build menus
        self._create_menus()

        # 4) Build toolbar
        self._create_toolbar()

        # 5) Connect signals
        self._connect_signals()

        # 6) Initial size
        self.resize(1200, 800)
        
        self._finalize_startup()

    @property
    def app(self):
        return QApplication.instance()
    @property
    def prefs(self):
        return QApplication.instance().prefs
    @property
    def engines(self):
        return QApplication.instance().engines
    @property
    def search_controller(self):
        return QApplication.instance().search_controller
    @property
    def search_dialog(self):
        return self.app.search_dialog

    def _create_central_widgets(self):
        # Dock: TuneList
        self.tunelist_dock = QDockWidget(_("List of tunes"), self)
        self.tunelist_dock.setObjectName("TuneListDock")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tunelist_dock)
        
        # Dock: ABC Assist
        self.assist_dock = QDockWidget(_("ABC Assist"), self)
        self.assist_dock.setObjectName("AssistDock")
        self.assist_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # ABC Assist on the left under TuneList
        self.addDockWidget(Qt.LeftDockWidgetArea, self.assist_dock)
        self.splitDockWidget(self.tunelist_dock, self.assist_dock, Qt.Vertical)

        # Central widget using tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.icon_playing = QIcon(":/icons/tune-playing.svg")   # 🔊
        self.icon_modified = QIcon(":/icons/tab-modified.svg")
        self.icon_normal = QIcon()
        
        self.lbl_warning = QLabel()
        self.lbl_warning.setVisible(False)
        self.lbl_warning.setStyleSheet("color: orange; font-weight: bold;")
        self.lbl_warning.setText(_("⚠ ABC warnings"))
        self.lbl_warning.setContentsMargins(8, 0, 8, 0)
        self.lbl_warning.mousePressEvent = lambda e: self._show_active_tab_warnings()
        self.statusBar().addPermanentWidget(self.lbl_warning)


    def _create_actions(self):
        # --- File menu ---
        self.act_new = QAction(_("New"), self)
        self.act_new.setIcon(QIcon(":/icons/file-new-abc.svg"))
        self.act_new.setShortcut("Ctrl+N")
        self.act_new.triggered.connect(self.new_file)

        self.act_open = QAction(_("Open"), self)
        self.act_open.setIcon(QIcon(":/icons/file-open-abc.svg"))
        self.act_open.setShortcut("Ctrl+O")
        self.act_open.triggered.connect(self.open_file_dialog)

        self.act_save = QAction(_("Save"), self)
        self.act_save.setIcon(QIcon(":/icons/file-save-abc.svg"))

        self.act_save.setShortcut("Ctrl+S")
        self.act_save.triggered.connect(self.save_file)

        self.act_save_as = QAction(_("Save as…"), self)
        self.act_save_as.triggered.connect(self.save_file_as)

        self.act_print = QAction(_("Print…"), self)
        self.act_print.setShortcut("Ctrl+P")
        self.act_print.triggered.connect(self._print)

        self.act_exporttunepdf = QAction(_("Export tune to PDF"), self)
        self.act_exporttunepdf.setShortcut("Ctrl+P")
        self.act_exporttunepdf.triggered.connect(self._export_tune_to_pdf)

        self.act_quit = QAction(_("Quit"), self)
        self.act_quit.setShortcut("Ctrl+Q")
        self.act_quit.triggered.connect(self.on_quit)

        # --- Edit menu ---
        self.act_undo = QAction(_("Undo"), self)
        self.act_undo.setShortcut("Ctrl+Z")
        self.act_undo.triggered.connect(self._undo)

        self.act_redo = QAction(_("Redo"), self)
        self.act_redo.setShortcut("Ctrl+Y")
        self.act_redo.triggered.connect(self._redo)

        self.act_cut = QAction(_("Cut"), self)
        self.act_cut.setShortcut("Ctrl+X")
        self.act_cut.triggered.connect(self._cut)

        self.act_copy = QAction(_("Copy"), self)
        self.act_copy.setShortcut("Ctrl+C")
        self.act_copy.triggered.connect(self._copy)

        self.act_paste = QAction(_("Cut"), self)
        self.act_paste.setShortcut("Ctrl+V")
        self.act_paste.triggered.connect(self._paste)

        self.act_find = QAction(_("Find…"), self)
        self.act_find.setShortcut("Ctrl+F")
        self.act_find.triggered.connect(self.app.find_text)

        self.act_findinfiles = QAction(_("Find in opened files…"), self)
        self.act_findinfiles.setShortcut("Shift+Ctrl+F")
        self.act_findinfiles.triggered.connect(self.app.find_text_in_files)

        self.act_findinopenfiles = QAction(_("Find in folder…"), self)
        #self.act_findinopenfiles.setShortcut("Ctrl+F")
        self.act_findinopenfiles.triggered.connect(self.app.find_text_in_folder)

        self.act_replace = QAction(_("Replace…"), self)
        self.act_replace.setShortcut("Alt+Ctrl+F")
        self.act_replace.triggered.connect(self.app.replace_text)

        # --- Player ---
        # Play
        self.act_play = QAction(_("Play"), self)
        self.act_play.setIcon(QIcon(":/icons/player-start.svg"))
        self.act_play.triggered.connect(self.play_tune)
        
        # Stop
        self.act_stop = QAction(_("Stop"), self)
        self.act_stop.setIcon(QIcon(":/icons/player-stop.svg"))
        self.act_stop.triggered.connect(self.stop_tune)
        
        self.act_loop = QAction("Loop", self)
        self.act_loop.setCheckable(True)
        self.act_loop.setIcon(QIcon(":/icons/player-loop.svg"))

        self.act_loop.toggled.connect(self._toggle_loop)

        # --- Preferences ---
        self.act_preferences = QAction(_("Settings…"), self)
        self.act_preferences.setShortcut("Ctrl+,")
        self.act_preferences.triggered.connect(self.open_preferences)

        # --- Development ---
        self.act_open_tmpdir = QAction(_("Open temporary folder of current tab"), self)
        self.act_open_tmpdir.triggered.connect(self.open_in_explorer)
        self.act_show_abc_extract = QAction(_("Show ABC extract"), self)
        self.act_show_abc_extract.triggered.connect(self.show_extracted_abc)
        self.act_show_svg = QAction(_("Show generated SVG"), self)
        self.act_show_svg.triggered.connect(self.show_svg)
        self.act_show_html = QAction(_("Show final HTML"), self)
        self.act_show_html.triggered.connect(self.show_html)
        self.act_show_mftext = QAction(_("Show mftext"), self)
        self.act_show_mftext.triggered.connect(self.show_mftext)
        self.act_show_midi = QAction(_("Show MIDI"), self)
        self.act_show_midi.triggered.connect(self.show_midi)

    def _create_menus(self):
        self.menubar = self.menuBar()

        # --- File menu ---
        self.menu_file = self.menubar.addMenu(_("File"))
        self.menu_file.addAction(self.act_new)
        self.menu_file.addAction(self.act_open)
        self.menu_file.addAction(self.act_save)
        self.menu_file.addAction(self.act_save_as)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.act_print)
        self.menu_file.addAction(self.act_exporttunepdf)
        self.menu_file.addSeparator()
        self.recent_menu = self.menu_file.addMenu(_("Open Recent"))
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.act_quit)

        # --- Edit menu ---
        self.menu_edit = self.menubar.addMenu(_("Edit"))
        self.menu_edit.addAction(self.act_undo)
        self.menu_edit.addAction(self.act_redo)
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.act_cut)
        self.menu_edit.addAction(self.act_copy)
        self.menu_edit.addAction(self.act_paste)
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.act_find)
        self.menu_edit.addAction(self.act_findinfiles)
        self.menu_edit.addAction(self.act_findinopenfiles)
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.act_replace)

        # --- Settings menu ---
        self.menu_prefs = self.menubar.addMenu(_("Preferences"))
        self.menu_prefs.addAction(self.act_preferences)

        # --- Development menu ---
        self.menu_dev = self.menubar.addMenu(_("Development"))
        self.menu_dev.addAction(self.act_open_tmpdir)
        self.menu_dev.addAction(self.act_show_abc_extract)
        self.menu_dev.addAction(self.act_show_svg)
        self.menu_dev.addAction(self.act_show_html)
        self.menu_dev.addAction(self.act_show_mftext)
        self.menu_dev.addAction(self.act_show_midi)

    def _create_toolbar(self):
        self.toolbar = self.addToolBar("Main")
        self.toolbar.setObjectName("MainToolbar")

        # --- Usual actions ---
        self.toolbar.addAction(self.act_new)
        self.toolbar.addAction(self.act_open)
        self.toolbar.addAction(self.act_save)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.act_play)
        self.toolbar.addAction(self.act_stop)

        self.toolbar.addAction(self.act_loop)

        self.toolbar.addSeparator()

        # ============================
        #  TEMPO : [ slider ]
        # ============================
        tempo_widget = QWidget()
        tempo_layout = QHBoxLayout(tempo_widget)
        tempo_layout.setContentsMargins(0, 0, 0, 0)

        tempo_label = QLabel(_("Tempo:"))
        self.slider_tempo = QSlider(Qt.Horizontal)
        self.slider_tempo.setRange(50, 200)   # 0.5x → 2.0x
        self.slider_tempo.setValue(100)
        self.slider_tempo.setFixedWidth(120)

        tempo_layout.addWidget(tempo_label)
        tempo_layout.addWidget(self.slider_tempo)
        tempo_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        tempo_action = QWidgetAction(self)
        tempo_action.setDefaultWidget(tempo_widget)
        self.toolbar.addAction(tempo_action)

        # ============================
        #  POSITION : [ slider ]
        # ============================
        self.pos_widget = QWidget()
        self.pos_layout = QHBoxLayout(self.pos_widget)
        self.pos_layout.setContentsMargins(0, 0, 0, 0)
        self.pos_layout.setSpacing(4)

        self.pos_label = QLabel(_("Position:"))
        self.pos_label.setMinimumWidth(60)
        self.pos_label.setMaximumWidth(120)
        #self.pos_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.pos_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.slider_position = QSlider(Qt.Horizontal)
        #self.slider_position = PlayPositionSlider(Qt.Horizontal)
        self.slider_position.setRange(0, 100)
        #self.slider_position.setFixedWidth(200)
        self.slider_position.setMinimumWidth(100)
        self.slider_position.setMaximumWidth(160)
        self.slider_position.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.pos_layout.addWidget(self.pos_label)
        self.pos_layout.addWidget(self.slider_position)
        self.pos_widget.setFixedWidth(220)
        self.pos_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.pos_action = QWidgetAction(self)
        self.pos_action.setDefaultWidget(self.pos_widget)
        self.toolbar.addAction(self.pos_action)
        
        self.range_widget = RangeSelectorWidget()
        range_action = QWidgetAction(self)
        range_action.setDefaultWidget(self.range_widget)
        self.toolbar.addAction(range_action)

    def _connect_signals(self):
        #self.editor.textChanged.connect(self.update_svg)
        #self.tune_list.on_tune_selected = self.on_tune_selected
        self.slider_tempo.valueChanged.connect(self._change_tempo)

        self.range_widget.startClicked.connect(self._open_start_menu)
        self.range_widget.endClicked.connect(self._open_end_menu)

        self.range_widget.startToggled.connect(self._toggle_start_enabled)
        self.range_widget.endToggled.connect(self._toggle_end_enabled)
        
        # signals prefs.theme_follow_changed, prefs.theme_editor_changed, prefs.scroll_mode_changed not used in main_window
        self.prefs.abc2svg_path_changed.connect(self._update_abc2svg)
        self.prefs.abc2midi_tools_path_changed.connect(self._update_abc2midi_tools)
        self.prefs.audio_player_changed.connect(self._update_audio_player)

    def _finalize_startup(self):
        self._update_recent_files_menu()
        geo = self.prefs["window_geometry"]
        state = self.prefs["window_state"]

        if geo:
            self.restoreGeometry(QByteArray.fromBase64(geo.encode()))

        if state:
            self.restoreState(QByteArray.fromBase64(state.encode()))

        open_files = self.prefs["session_open_files"]
        active_file = self.prefs["session_active_file"]

        valid_files = [p for p in open_files if os.path.exists(p)]
        missing_files = len(valid_files) != len(open_files)

        for path in valid_files:
            self.open_file(path)

        if not valid_files:
            self.new_file()

        if active_file:
            index = self.find_tab_by_path(active_file)
            if index != -1:
                self.tabs.setCurrentIndex(index)

        # Warn if missing files
        if missing_files:
            QMessageBox.warning(
                self,
                _("Missing files"),
                _("Some files from the previous session no longer exist. They were replaced by a new empty document.")
            )
            
        self.prefs["session_open_files"] = []
        self.prefs["session_active_file"] = None
        self.prefs.save()

    def _update_recent_files_menu(self):
        self.recent_menu.clear()

        recent = self.prefs["recent_files"]

        if not recent:
            action = QAction(_("(No recent files)"), self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
            return

        for path in recent:
            action = QAction(path, self)
            action.triggered.connect(lambda checked, p=path: self.open_file(p))
            self.recent_menu.addAction(action)

        # Reset Recent files list
        self.recent_menu.addSeparator()
        clear_action = QAction(_("Clear Recent Files"), self)
        clear_action.triggered.connect(self._clear_recent_files)
        self.recent_menu.addAction(clear_action)

    def _clear_recent_files(self):
        self.prefs["recent_files"] = []
        self.prefs.save()
        self._update_recent_files_menu()

    def new_file(self):
        #tab = DocumentTab(self.temp_dir, self.prefs, self.engines)
        tab = DocumentTab(self.temp_dir)
        self.tabs.addTab(tab, _("Untitled"))

        self.tabs.setCurrentWidget(tab)
        #tab.textChanged.connect(self.on_document_changed)
        tab.textChanged.connect(lambda t=tab: self.on_document_changed(t))
        tab.cursorMoved.connect(self.on_cursor_moved)
        tab.playPositionChanged.connect(self._on_tick)
        tab.tuneStopped.connect(lambda: self._update_tune_stopped(tab))
        tab.warningsChanged.connect(self._on_tab_warnings_changed)

        self.range_widget.set_start_value(tab.play_start_tick)
        self.range_widget.set_end_value(tab.play_end_tick)
        self.prefs["last_opened_file"] = ""
        self.prefs.save()
        #tab.noteClicked.connect(self.on_note_clicked_in_svg)

    def open_file_dialog(self):
        path, _filter = QFileDialog.getOpenFileName(
            self, _("Open ABC File"), "", _("ABC Files (*.abc)")
        )
        if path:
            self.open_file(path)

    def open_file(self, path):
        path = str(path)
        if not path or not os.path.exists(path):
            QMessageBox.warning(
                self,
                _("File not found"),
                _("The file '{file}' does not exist.").format(file=path)
            )
            return None

        existing_index = self.find_tab_by_path(path)
        if existing_index != -1:
            self.tabs.setCurrentIndex(existing_index)
            return self.tabs.widget(existing_index)

        #tab = DocumentTab(self.temp_dir, self.prefs, self.engines)
        tab = DocumentTab(self.temp_dir)
        filename = os.path.basename(path)
        self.tabs.addTab(tab, filename)
        self.tabs.setCurrentWidget(tab)

        tab.load_file(path)

        #tab.textChanged.connect(self.on_document_changed)
        tab.textChanged.connect(lambda t=tab: self.on_document_changed(t))
        tab.cursorMoved.connect(self.on_cursor_moved)
        tab.playPositionChanged.connect(self._on_tick)
        tab.tuneStopped.connect(lambda: self._update_tune_stopped(tab))
        tab.warningsChanged.connect(self._on_tab_warnings_changed)

        self.range_widget.set_start_value(tab.play_start_tick)
        self.range_widget.set_end_value(tab.play_end_tick)

        self._add_to_recent_files(path)
        return tab

    def _add_to_recent_files(self, path):
        recent = self.prefs["recent_files"]

        # Remove if already present
        recent = [p for p in recent if p != path]

        # Add as last
        recent.insert(0, path)

        # Limit to 10
        recent = recent[:10]

        self.prefs["recent_files"] = recent
        self.prefs.save()

        self._update_recent_files_menu()

    def save_file(self):
        tab = self.tabs.currentWidget()
        if not tab:
            return

        self._save_file_of_tab(tab)
        return
        if not tab.current_file:
            return self.save_file_as()

        tab.save()
        self._update_tab_title(tab)
        self.update_window_title()

    def _save_file_of_tab(self, tab):
        if not tab.current_file:
            # fallback: save as, show tab with untitled and retrieve initial current tab
            current = self.tabs.currentWidget()
            index = self.tabs.indexOf(tab)
            self.tabs.setCurrentIndex(index)
            self.save_file_as()
            self.tabs.setCurrentWidget(current)
            return

        tab.save()
        self._update_tab_title(tab)
        self.update_window_title()
        return

    def save_file_as(self):
        tab = self.tabs.currentWidget()
        if not tab:
            return

        path, _filter = QFileDialog.getSaveFileName(self, _("Save As"), "", "ABC Files (*.abc)")
        if path:
            tab.save_as(path)
            self._update_tab_title(tab)
            self.update_window_title()
            self._add_to_recent_files(path)

    def _maybe_save_tab(self,tab):
        if not tab.is_modified():
            return True

        index = self.tabs.indexOf(tab)
        if index != -1:
            self.tabs.setCurrentIndex(index)

        ret = QMessageBox.question(
            self,
            _("Unsaved changes"),
            #f"The document '{tab.current_file or 'Untitled'}' has unsaved changes.\nSave before closing?",
            _("The document '{filename}' has unsaved changes.\nSave before closing?").format(filename=tab.current_file or _("Untitled")),
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )

        if ret == QMessageBox.Cancel:
            return False
        elif ret == QMessageBox.Yes:
            return self.save_file()
        else:
            return True

    def _update_tab_title(self, tab):
        index = self.tabs.indexOf(tab)
        if index < 0:
            return

        if tab.current_file:
            title = os.path.basename(tab.current_file)
        else:
            title = _("Untitled")

        if tab.is_modified():
            title += " *"

        if tab.audio_tune is not None:
            self.tabs.setTabIcon(index, self.icon_playing)
        else:
            self.tabs.setTabIcon(index, self.icon_modified if tab.is_modified() else self.icon_normal)

        self.tabs.setTabText(index, title)

    def _undo(self):
        tab = self.tabs.currentWidget()
        if tab:
            tab.editor.undo()

    def _redo(self):
        tab = self.tabs.currentWidget()
        if tab:
            tab.editor.redo()

    def _cut(self):
        tab = self.tabs.currentWidget()
        if tab:
            tab.editor.cut()

    def _copy(self):
        tab = self.tabs.currentWidget()
        if tab:
            tab.editor.copy()

    def _paste(self):
        tab = self.tabs.currentWidget()
        if tab:
            tab.editor.paste()

    def _on_tab_warnings_changed(self, has_warnings):
        if self.tabs.currentWidget() is self.sender():
            self.lbl_warning.setVisible(has_warnings)

    def _show_active_tab_warnings(self):
        tab = self.tabs.currentWidget()
        if not tab:
            return

        duplicates = tab.abc_document.duplicate_indexes
        if not duplicates:
            return

        msg = "Duplicate X: fields detected:\n\n"
        for index, lines in duplicates.items():
            msg += f"X:{index} → " + ", ".join(str(l+1) for l in lines) + "\n"

        QMessageBox.information(self, "ABC Warnings", msg)

    def on_document_changed(self, tab):
        #tab = self.tabs.currentWidget()
        if not tab:
            return

        self._update_tab_title(tab)
        self.update_window_title()
        self._update_playback_toolbar_editability()
        
        #if self.engines.midi_player.is_playing or self.engines.midi_player.is_paused:
        #    return
        if tab is self.tabs.currentWidget():
            logger.debug(f"[MainWindow] update start: start enabled {tab.play_start_enabled} at position {tab.play_start_tick}")
            logger.debug(f"[MainWindow] update end: end enabled {tab.play_end_enabled} at position {tab.play_end_tick}")
            self.range_widget.chk_start.setChecked(tab.play_start_enabled)
            self.range_widget.chk_end.setChecked(tab.play_end_enabled)
            self.range_widget.set_start_value(tab.play_start_tick)
            self.range_widget.set_end_value(tab.play_end_tick)
            self._update_play_position_slider(tab)
        #self._update_playback_toolbar_editability()

    def on_cursor_moved(self, line: int, pos_abs: int):
        tab = self.tabs.currentWidget()
        logger.debug(f"[MainWindow] cursor moved: {pos_abs}")

        if not tab or not tab.abc_document:
            return

        doc = tab.abc_document

        tune = doc.tune_at_line(line)
        if not tune:
            return

        # Update SVG only if new tune
        if tune.index != tab.current_tune_index:
            tab.current_tune_index = tune.index
            # synchro TuneList
            self.tune_list.select_tune(tune.index)

            abc_for_render = doc.get_tune_abc(tune)
            save_temp_abc(abc_for_render,tab.temp_dir)
            svg = tab.update_svg(abc_for_render)
            save_temp_svg(svg,tab.temp_dir)
            self.range_widget.set_start_value(tab.play_start_tick)
            self.range_widget.set_end_value(tab.play_end_tick)
            self._update_play_position_slider(tab)

        cursor = tab.editor.textCursor()

        if cursor.hasSelection():
            abs_start = cursor.selectionStart()
            abs_end   = cursor.selectionEnd()

            rel_start = doc.absolute_to_relative(abs_start, tune)
            rel_end   = doc.absolute_to_relative(abs_end, tune)

            # All notes with offset included in range
            active = [o for o in tab.note_offsets if rel_start <= o <= rel_end]

        else:
            # No selection → single note
            pos_rel = doc.absolute_to_relative(pos_abs, tune)

            # fallback: Previous note
            note = max((o for o in tab.note_offsets if o <= pos_rel), default=None)
            active = [note] if note is not None else []
        
        if not tab.follow_engine.playing:
            tab.follow_engine.set_active_notes(active)

    def on_tab_changed(self, index):
        tab = self.tabs.widget(index)
        if not tab:
            # No active document → clear TuneList
            self.clear_docks()
            return

        self.update_window_title()
        if hasattr(tab, "tune_list"):
            self.tunelist_dock.setWidget(tab.tune_list)
            self.tunelist_dock.widget().setMinimumHeight(200)
        else:
            self.tunelist_dock.setWidget(None)
        if hasattr(tab, "assist_panel"):
            # Update doc with widget from DocumentTab
            self.assist_dock.setWidget(tab.assist_panel)
            self.assist_dock.widget().setMinimumHeight(200)

            tab.assist_panel.update_assist()
        else:
            self.assist_dock.setWidget(None)
        self.range_widget.set_start_value(tab.play_start_tick)
        self.range_widget.set_end_value(tab.play_end_tick)
        self._update_play_position_slider(tab)
        self._update_playback_toolbar_editability()

        # Update warning indicator for the active tab
        has_warnings = bool(tab.abc_document.duplicate_indexes)
        self.lbl_warning.setVisible(has_warnings)

    def close_tab(self, index):
        logger.info("[MainWindow] Close_tab")
        tab = self.tabs.widget(index)
        if not self._maybe_stop_playback(tab):
            return
        if not self._maybe_save_tab(tab):
            return  # cancel tab close
        self.tabs.removeTab(index)
        tab.deleteLater()
        tab = self.tabs.currentWidget()
        if not tab:
            self.clear_docks()
            self.new_file()
            return
            
        if tab.current_file and os.path.exists(tab.current_file):
            self.prefs["last_opened_file"] = tab.current_file
            self.prefs.save()

    def _maybe_stop_playback(self, tab):
        if not tab:
            return False

        if tab.audio_tune is not None:
            ret = QMessageBox.question(
                self,
                _("Playback in progress"),
                _("A tune is currently playing.\nStop playback and close?"),
                QMessageBox.Yes | QMessageBox.No
            )

            if ret == QMessageBox.No:
                return False

            # Stop playback
            self.engines.midi_player.stop()
        return True

    def play_tune(self):
        logger.info("[MainWindow] Play Tune")
        tab = self.tabs.currentWidget()
        if not tab:
            return

        tab.play()
        self.act_play.setIcon(QIcon(":/icons/player-pause.svg"))
        self.act_play.triggered.disconnect()
        self.act_play.triggered.connect(self.pause_tune)
        self._update_tab_title(tab)
        self.update_window_title()
        self.update_position_label_for_playback()

    def pause_tune(self):
        logger.info("[MainWindow] Pause Tune")
        if not self.engines.midi_player:
            return

        self.engines.midi_player.pause()
        self.act_play.setIcon(QIcon(":/icons/player-start.svg"))
        self.act_play.triggered.disconnect()
        self.act_play.triggered.connect(self.resume_tune)
        self.update_window_title()
        self.update_position_label_for_playback()

    def resume_tune(self):
        logger.info("[MainWindow] Resume Tune")
        if not self.engines.midi_player:
            return

        self.engines.midi_player.play()
        self.act_play.setIcon(QIcon(":/icons/player-pause.svg"))
        self.act_play.triggered.disconnect()
        self.act_play.triggered.connect(self.pause_tune)
        self.update_window_title()
        self.update_position_label_for_playback()

    def stop_tune(self):
        logger.info("[MainWindow] Stop Tune")
        if not self.engines.midi_player:
            return

        self.engines.midi_player.stop()
        self.act_play.setIcon(QIcon(":/icons/player-start.svg"))
        self.act_play.triggered.disconnect()
        self.act_play.triggered.connect(self.play_tune)
        self.update_window_title()
        self.update_position_label_for_playback()

    def _update_tune_stopped(self, tab):
        self.act_play.setIcon(QIcon(":/icons/player-start.svg"))
        self.act_play.triggered.disconnect()
        self.act_play.triggered.connect(self.play_tune)
        self._update_tab_title(tab)
        self.on_document_changed(tab)
        self.update_window_title()
        self.update_position_label_for_playback()
        
    def _on_tick(self, pos, length):
        tab = self.tabs.currentWidget()
        if not tab:
            return

        self.slider_position.blockSignals(True)
        self.slider_position.setRange(0, length)
        self.slider_position.setValue(pos)
        self.slider_position.blockSignals(False)

        logger.debug(f"[MainWindow] Position: {pos}, Length: {length}")

    def on_tune_selected(self, tune):
        tab = self.tabs.currentWidget()
        if tab:
            tab.goto_line(tune.start_line)
            tab.editor.setFocus()
            self._update_playback_toolbar_editability()

    def open_preferences(self):
        dlg = PreferencesDialog(self)
        if dlg.exec():
            self.apply_preferences()

    def apply_preferences(self):
        #self.engines.apply_preferences(self.prefs)

        #for i in range(self.tabs.count()):
        #    tab = self.tabs.widget(i)
        #    tab.apply_preferences()
        pass

    def _update_abc2svg(self):
        self.engines.new_abc2svg_prefs(self.prefs)
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            tab.rebuild_svg()
    
    def _update_abc2midi_tools(self):
        self.engines.new_abc2midi_tools_prefs(self.prefs)
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            tab.rebuild_midi()
    
    def _update_audio_player(self):
        if not self.engines.midi_player:
            return

        self.engines.midi_player.stop()        
        self.engines.new_midi_player_prefs(self.prefs)

    def open_in_explorer(self):
        tab = self.tabs.currentWidget()
        if not tab or not getattr(tab, "temp_dir", None):
            return

        path = tab.temp_dir
        if not os.path.isdir(path):
            return

        #import subprocess, sys
        if sys.platform == "darwin":
            subprocess.call(["open", path])
        elif sys.platform == "win32":
            subprocess.call(["explorer", path])
        else:
            subprocess.call(["xdg-open", path])

    def show_extracted_abc(self):
        from easyabc2.ui.abc_preview_dialog import AbcPreviewDialog

        tab = self.tabs.currentWidget()
        path = tab.temp_dir / "current_tune.abc"

        if not path.exists():
            QMessageBox.warning(self, "Debug ABC", _("No ABC extract available."))
            return

        dlg = AbcPreviewDialog(_("ABC extract (header + tune)"), path, self.prefs, self)
        dlg.setModal(False)
        dlg.show()

    def show_svg(self):
        from easyabc2.ui.txt_preview_dialog import TxtPreviewDialog

        tab = self.tabs.currentWidget()
        path = tab.temp_dir / "current_tune.svg"
        if not path.exists():
            QMessageBox.warning(self, "Debug SVG", _("No SVG generated."))
            return

        dlg = TxtPreviewDialog(_("Generated SVG"), path, self.prefs, self)
        dlg.setModal(False)
        dlg.show()

    def show_html(self):
        tab = self.tabs.currentWidget()
        if not tab:
            return

        def display(html):
            from easyabc2.ui.txt_preview_dialog import TxtPreviewDialog
            tab = self.tabs.currentWidget()
            path = tab.temp_dir / "current_html.html"
            path.write_text(html, encoding="utf-8")

            dlg = TxtPreviewDialog(_("Final HTML (ScoreView)"), path, self.prefs, self)
            dlg.setModal(False)
            dlg.show()

        tab.score_view.get_svg_html(display)

    def show_mftext(self):
        pass

    def show_midi(self):
        pass

    def _export_tune_to_pdf(self):
        file, _filter = QFileDialog.getSaveFileName(self, _("Export tune to PDF"), "", "PDF (*.pdf)")
        if file:
            tab = self.tabs.currentWidget()
            tab.export_tune_to_pdf(file)
        #pass
    
    def _print(self):
        #printer = QPrinter()
        #dialog = QPrintDialog(printer, self)
        #if dialog.exec():
        #    tab = self.tabs.currentWidget()
        #    tab.print(printer)
        #
        # No direct printing towards pdf available in pyside6
        # Need to export to temp.pdf and then one of the option:
        # Windows: os.startfile("temp.pdf", "print")
        # mac: subprocess.run(["open", "-a", "Preview", "temp.pdf"])
        # Linux: subprocess.run(["lpr", "temp.pdf"])
        QMessageBox.information(self, _("Print"), _("For now to print save to PDF and then print via PDF viewer"))
        pass

    def on_quit(self):
        self.close()

    def closeEvent(self, event):
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if not self._maybe_save_tab(tab):
                event.ignore()
                return

        open_files = []
        active_file = None
        current_index = self.tabs.currentIndex()
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab.current_file:
                open_files.append(tab.current_file)
                logger.debug(f"[MainWindow] list {tab.current_file}")
                if i == current_index :
                    active_file = tab.current_file
                    logger.debug(f"[MainWindow] active {active_file}")

        self.prefs["window_geometry"] = self.saveGeometry().toBase64().data().decode()
        self.prefs["window_state"] = self.saveState().toBase64().data().decode()
        self.prefs["session_open_files"] = open_files
        self.prefs["session_active_file"] = active_file
        self.prefs.save()

        app = QApplication.instance()
        if self in app.main_windows:
            app.main_windows.remove(self)
        event.accept()

    def closeEvent(self, event):

        audio_tab = None
        modified_tabs = []
        open_files = []
        active_file = None

        current_index = self.tabs.currentIndex()

        # --- 1. detect current tabs state ---
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)

            if tab.audio_tune is not None:
                audio_tab = tab

            if tab.is_modified():
                modified_tabs.append(tab)

            if tab.current_file:
                open_files.append(tab.current_file)
                if i == current_index:
                    active_file = tab.current_file

        # --- 2. Playback check ---
        if audio_tab is not None:
            tune = audio_tab.audio_tune.title
            filename = audio_tab.current_file or _("Untitled")

            ret = QMessageBox.question(
                self,
                _("Playback in progress"),
                _("The tune '{tune}' in document '{file}' is currently playing.\n"
                  "Stop playback and close the window?").format(
                    tune=tune, file=filename
                ),
                QMessageBox.Yes | QMessageBox.No
            )

            if ret == QMessageBox.No:
                event.ignore()
                return

            self.engines.midi_player.stop()

        # --- 3. Save check ---
        if modified_tabs:
            filenames = [
                tab.current_file or _("Untitled")
                for tab in modified_tabs
            ]
            file_list = "\n".join(f"• {name}" for name in filenames)

            msg = _(
                "The following documents have unsaved changes:\n\n"
                "{files}\n\n"
                "Save all before closing?"
            ).format(files=file_list)

            ret = QMessageBox.question(
                self,
                _("Unsaved changes"),
                msg,
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )

            if ret == QMessageBox.Cancel:
                event.ignore()
                return

            if ret == QMessageBox.Yes:
                for tab in modified_tabs:
                    self._save_file_of_tab(tab)

        # --- 4. Save session ---
        self.prefs["window_geometry"] = self.saveGeometry().toBase64().data().decode()
        self.prefs["window_state"] = self.saveState().toBase64().data().decode()
        self.prefs["session_open_files"] = open_files
        self.prefs["session_active_file"] = active_file
        self.prefs.save()

        # --- 5. Close window ---
        event.accept()
        QApplication.instance().main_windows.remove(self)

    def save_all_tabs(self):
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab.is_modified():
                self._save_file_of_tab(tab)

    def _save_tab(self, tab):
        index = self.tabs.indexOf(tab)
        if index != -1:
            self.tabs.setCurrentIndex(index)
        return self.save_file()

    def open_file_from_search(self, path, start, end):
        tab = self.open_file(path)

        def select():
            editor = tab.editor
            cursor = editor.textCursor()
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.KeepAnchor)
            editor.setTextCursor(cursor)
            editor.setFocus()

        QTimer.singleShot(0, select)

        self.show()
        self.raise_()
        self.activateWindow()

        return tab

    def clear_docks(self):
        self.tunelist_dock.setWidget(None)
        self.assist_dock.setWidget(None)

    def find_tab_by_path(self, path):
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab.current_file == path:
                return i
        return -1

    #def update_dev_menu_state(self):
    #    self.menu_show_abc.Enable(self.current_files["abc"] is not None)
    #    self.menu_show_svg.Enable(self.current_files["svg"] is not None)
    #    self.menu_show_mid.Enable(self.current_files["mid"] is not None)
    #    self.menu_show_mftext.Enable(self.current_files["mftext"] is not None)

    def _update_range_editability(self, tab):
        editable = self.is_range_editable()

        # Checkboxes
        self.range_widget.start_checkbox.setEnabled(editable)
        self.range_widget.end_checkbox.setEnabled(editable)

        # Labels (grayed out)
        color = "#000000" if editable else "#555555"
        self.range_widget.start_label.setStyleSheet(f"color: {color};")
        self.range_widget.end_label.setStyleSheet(f"color: {color};")

        # Sliders
        self.range_widget.start_slider.setEnabled(editable)
        self.range_widget.end_slider.setEnabled(editable)

    def _update_playback_toolbar_editability(self):
        logger.debug("[Main Window] Update editability")
        editable = self.is_range_editable()
        logger.debug(f"[Main Window] Playback editable: {editable}")

        self.slider_tempo.setEnabled(editable)
        self.slider_position.setEnabled(editable)
        # Checkboxes
        self.range_widget.chk_start.setDisabled(not editable)
        self.range_widget.chk_end.setDisabled(not editable)

        # Labels (grayed out)
        color = "#000000" if editable else "#555555"
        self.range_widget.lbl_start.setStyleSheet(f"color: {color};")
        self.range_widget.lbl_end.setStyleSheet(f"color: {color};")

        # Sliders
        #self.range_widget.start_slider.setEnabled(editable)
        #self.range_widget.end_slider.setEnabled(editable)

    def is_range_editable(self):
        tab = self.tabs.currentWidget()
        if not tab:
            logger.error("[Main Window] Not editable because no tab")
            return False
        
        return tab.is_playback_available()

    def update_position_label_for_playback(self):
        player = self.engines.midi_player

        if not player.is_active:
            self.pos_label.setText("Position :")
            return

        audio_title = player.current_title or _("Playing")

        prefix = "⏸" if player.is_paused else "▶"
        title = f"{prefix} {audio_title}"

        container_width = self.pos_widget.width()
        slider_min = self.slider_position.minimumWidth()
        spacing = self.pos_layout.spacing()
        available = max(20, container_width - slider_min - spacing)

        fm = self.pos_label.fontMetrics()
        short_title = fm.elidedText(title, Qt.ElideRight, available)

        self.pos_label.setText(f"{short_title}")

    def _change_tempo(self):
        pass
    
    def _open_start_menu(self):
        tab = self.tabs.currentWidget()
        if not tab:
            return

        if (self.engines.midi_player.is_playing or self.engines.midi_player.is_paused) and (tab.current_tune != tab.audio_tune or tab.audio_tune is None) :
            return

        menu = QMenu(self)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, tab.max_tick)
        slider.setValue(tab.play_start_tick)
        slider.setFixedWidth(200)

        act = QWidgetAction(menu)
        act.setDefaultWidget(slider)
        menu.addAction(act)

        slider.valueChanged.connect(lambda v: self._update_start_tick(tab, v))

        menu.exec_(self.range_widget.lbl_start.mapToGlobal(QPoint(0, self.range_widget.lbl_start.height())))

    def _open_end_menu(self):
        tab = self.tabs.currentWidget()
        if not tab:
            return

        if (self.engines.midi_player.is_playing or self.engines.midi_player.is_paused) and (tab.current_tune != tab.audio_tune or tab.audio_tune is None) :
            return
        menu = QMenu(self)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, tab.max_tick)
        slider.setValue(tab.play_end_tick)
        slider.setFixedWidth(200)

        act = QWidgetAction(menu)
        act.setDefaultWidget(slider)
        menu.addAction(act)

        slider.valueChanged.connect(lambda v: self._update_end_tick(tab, v))

        menu.exec_(self.range_widget.lbl_end.mapToGlobal(QPoint(0, self.range_widget.lbl_end.height())))

    def _update_start_tick(self, tab, tick):
        tab.update_start_tick(tick)
        self.range_widget.set_start_value(tab.play_start_tick)
        self.range_widget.set_end_value(tab.play_end_tick)
        if not self.range_widget.chk_start.isChecked():
            self.range_widget.chk_start.blockSignals(True)
            self.range_widget.chk_start.setChecked(True)
            self.range_widget.chk_start.blockSignals(False)
        self._update_play_position_slider(tab)

    def _update_end_tick(self, tab, tick):
        tab.update_end_tick(tick)
        self.range_widget.set_start_value(tab.play_start_tick)
        self.range_widget.set_end_value(tab.play_end_tick)
        if not self.range_widget.chk_end.isChecked():
            self.range_widget.chk_end.blockSignals(True)
            self.range_widget.chk_end.setChecked(True)
            self.range_widget.chk_end.blockSignals(False)
        self._update_play_position_slider(tab)

    def _update_play_position_slider(self, tab):
        self.slider_position.blockSignals(True)
        self.slider_position.setValue(tab.play_start_tick)
        self.slider_position.blockSignals(False)
        pass

    def _toggle_start_enabled(self, enabled):
        tab = self.tabs.currentWidget()
        tab.enable_start(enabled)

    def _toggle_end_enabled(self, enabled):
        tab = self.tabs.currentWidget()
        tab.enable_end(enabled)

    def _toggle_loop(self, enabled):
        if self.engines.midi_player:
            self.engines.midi_player.set_loop(enabled)

        tab = self.tabs.currentWidget()
        tab.set_loop(enabled)

    def update_window_title(self):
        player = self.engines.midi_player

        tab = self.tabs.currentWidget()
        if not tab:
            self.setWindowTitle(f"EasyABC2")
            return

        doc_name = tab.current_file if tab.current_file else _("Untitled")
        modified = "*" if tab.is_modified() else ""
        doc_part = f"{doc_name}{modified}"

        if not player.is_active:
            self.setWindowTitle(f"EasyABC2 — {doc_part}")
            return

        audio_title = player.current_title or _("Playing")

        prefix = "⏸" if player.is_paused else "▶"
        suffix = _("(other window or tab)") if tab.audio_tune is None else ""
        space = " " if suffix else ""

        self.setWindowTitle(f"EasyABC2 — {doc_part} — {prefix} {audio_title}{space}{suffix}")

    def _show_active_tab_warnings(self):
        tab = self.tabs.currentWidget()
        if not tab:
            return

        duplicates = tab.abc_document.duplicate_indexes
        if not duplicates:
            return

        msg = "Duplicate X: fields detected:\n\n"
        for index, lines in duplicates.items():
            msg += f"X:{index} → " + ", ".join(str(l+1) for l in lines) + "\n"

        QMessageBox.information(self, "ABC Warnings", msg)

def main():
    app = QApplication(sys.argv)

    # -- Mandatory otherwise quickjs might use , as separator for decimal
    locale.setlocale(locale.LC_NUMERIC, 'en_US.UTF-8')
    locale.setlocale(locale.LC_MONETARY, 'en_US.UTF-8')
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
