# easyabc2/easyabc_app.py
import sys
import locale

from PySide6.QtWidgets import QApplication

from easyabc2.utils.easyabc_utils import get_app_data_dir
from easyabc2.utils.preferences import UserPreferences
from easyabc2.utils.logging_utils import setup_logging, logger
from easyabc2.utils.search_controller import SearchController
from easyabc2.ui.main_window import MainWindow
from easyabc2.ui.search_dialog import SearchDialog
from easyabc2.engines.engines_manager import EngineManager

def init_quickjs_locale():
    # macOS: UTF‑8 recommended
    if sys.platform == "darwin":
        try:
            locale.setlocale(locale.LC_NUMERIC, "en_US.UTF-8")
            locale.setlocale(locale.LC_MONETARY, "en_US.UTF-8")
            return
        except locale.Error:
            # fallback just in case (rare)
            locale.setlocale(locale.LC_NUMERIC, "C")
            locale.setlocale(locale.LC_MONETARY, "C")
            return

    # Linux / Windows : 'C' is preferred
    locale.setlocale(locale.LC_NUMERIC, "C")
    locale.setlocale(locale.LC_MONETARY, "C")

class EasyABCApp(QApplication):
    def __init__(self, argv):
        print("Initialising EasyABCApp")
        super().__init__(argv)
        self.app = self

        # App data
        self.app_data_dir = get_app_data_dir("EasyABC2")

        # Fix locale for quickjs
        init_quickjs_locale()

        # Preferences
        self.prefs = UserPreferences(self.app_data_dir / "preferences.json")

        # Logging
        setup_logging(self.app_data_dir, self.prefs["debug_mode"])
        logger.info("Application started.")

        # Engines
        self.engines = EngineManager(self.prefs)

        # Search
        self.search_controller = SearchController()

        self.search_dialog = SearchDialog()
        self.search_dialog.search_requested.connect(self.on_search)
        #self.search_dialog.next_requested.connect(self.search_controller.find_next)
        #self.search_dialog.previous_requested.connect(self.search_controller.find_previous)
        self.search_dialog.replace_requested.connect(self._on_replace_requested)
        self.search_dialog.replace_all_requested.connect(self._on_replace_all_requested)
        self.search_dialog.replace_all_in_folder_requested.connect(self._on_replace_all_in_folder_requested)
        self.search_dialog.search_all_documents_requested.connect(self.on_search_all_documents)
        self.search_dialog.search_folder_requested.connect(self.on_search_folder)

        # Multi-window management
        self.main_windows = []
        self.window_sessions = {} # {window: {"open_files": [...], "active_file": ...}}

        # Restore or create first window
        self._startup()

    def _startup(self):
        session_files = self.prefs["session_open_files"]

        win = self.create_main_window()
        self.first_window = win

        if session_files:
            for path in session_files:
                win.open_file(path)

    # --- Window management ---

    def register_window(self, win):
        self.main_windows.append(win)

    def unregister_window(self, win):
        if win in self.main_windows:
            self.main_windows.remove(win)
        if win in self.window_sessions:
            del self.window_sessions[win]

        if not self.main_windows:
            self.save_full_session()

    # --- Session management ---
    def register_window_session(self, win, open_files, active_file):
        self.window_sessions[win] = {
            "open_files": open_files,
            "active_file": active_file,
        }

    def save_full_session(self):
        all_open_files = []
        active_file = None

        for session in self.window_sessions.values():
            all_open_files.extend(session["open_files"])
            if session["active_file"]:
                active_file = session["active_file"]

        self.prefs["session_open_files"] = all_open_files
        self.prefs["session_active_file"] = active_file
        self.prefs.save()

    # --- Actions ---
    def open_new_window(self, path=None):
        win = MainWindow(self.app_data_dir)
        self.register_window(win)
        win.show()
        if path:
            win.open_file(path)
        return win

    def create_main_window(self):
        win = MainWindow(self.app_data_dir)
        self.register_window(win)
        win.show()
        return win

    def quit_application(self):
        for win in list(self.main_windows):
            win.close()

    # --- Helpers ---
    def all_mainwindows(self):
        return list(self.main_windows)

    def current_mainwindow(self):
        for w in self.main_windows:
            if w.isActiveWindow():
                return w
        return self.main_windows[0] if self.main_windows else None

    def collect_open_tabs(self):
        result = {}
        for win in self.main_windows:
            for i in range(win.tabs.count()):
                tab = win.tabs.widget(i)
                if tab.file_path:
                    result[tab.file_path] = (win, tab)
        return result

    # --- Find & Replace management ---
    def find_text(self):
        self.search_dialog.set_mode("find")
        self.search_dialog.show()
        self.search_dialog.raise_()
        self.search_dialog.activateWindow()

    def find_text_in_files(self):
        self.search_dialog.set_mode("open_docs")
        self.search_dialog.show()
        self.search_dialog.raise_()
        self.search_dialog.activateWindow()

    def find_text_in_folder(self):
        self.search_dialog.set_mode("folder")
        self.search_dialog.show()
        self.search_dialog.raise_()
        self.search_dialog.activateWindow()

    def replace_text(self):
        self.search_dialog.set_mode("replace")
        self.search_dialog.show()
        self.search_dialog.raise_()
        self.search_dialog.activateWindow()

    def on_search(self, query, options):
        results = self.search_controller.search_in_current_document(query, options)
        self.search_dialog.show_results(results)
        self.search_dialog.show()

    def on_search_all_documents(self, query, options):
        results = self.search_controller.search_in_all_documents(query, options)
        self.search_dialog.show_results(results)
        self.search_dialog.show()

    def on_search_folder(self, query, folder, options):
        if not folder:
            return
        results = self.search_controller.search_in_folder(folder, query, options)
        self.search_dialog.set_mode("folder")
        self.search_dialog.show_results(results)
        self.search_dialog.show()

    def _on_replace_requested(self, result, replacement):
        updated_results = self.search_controller.replace_one(result, replacement)
        self.search_dialog.update_results(updated_results)
        self.search_dialog.next_result()

    def _on_replace_all_requested(self, replacement, scope):
        if scope == "current":
            win = self.current_mainwindow()
            tab = win.tabs.currentWidget()
            self.search_controller.replace_in_tab(tab, replacement)

        elif scope == "open_docs":
            self.search_controller.replace_all_in_all_documents(replacement)

        elif scope == "folder":
            # handled by the other signal
            pass

    def _on_replace_all_in_folder_requested(self, files, replacement):
        open_tabs = self.collect_open_tabs()
        # open_tabs : dict { file_path: (win, tab) }

        already_open = []
        to_open = []

        for f in files:
            if f in open_tabs:
                already_open.append(f)
            else:
                to_open.append(f)

        # 2. Replace in already opened tabs
        for f in already_open:
            win, tab = open_tabs[f]
            self.search_controller.replace_in_tab(tab, replacement)

        # 3. Open new window for the remaining files
        if to_open:
            batch_win = self.create_main_window()

            for f in to_open:
                batch_win.open_file(f)

            # 3. Replace in each tab of the batch window
            for i in range(batch_win.tabs.count()):
                tab = batch_win.tabs.widget(i)
                self.search_controller.replace_in_tab(tab, replacement)
