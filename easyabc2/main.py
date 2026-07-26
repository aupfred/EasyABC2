# easyabc2/main.py
import sys
import locale

from PySide6.QtWidgets import QApplication
from easyabc2.utils.easyabc_utils import get_app_data_dir
from easyabc2.utils.preferences import UserPreferences
from easyabc2.utils.logging_utils import setup_logging, logger
from easyabc2.utils.search_controller import SearchController
from easyabc2.ui.main_window import MainWindow
from easyabc2.engines.engines_manager import EngineManager

def main():
    # Qt application
    app = QApplication(sys.argv)
    app.main_windows = []  # initialisation de la liste

    # Fix locale for quickjs
    locale.setlocale(locale.LC_NUMERIC, 'en_US.UTF-8')
    locale.setlocale(locale.LC_MONETARY, 'en_US.UTF-8')

    # Application data directory
    app_data_dir = get_app_data_dir("EasyABC2b")

    # Load preferences
    prefs = UserPreferences(app_data_dir / "preferences.json")

    # Setup logging (rotation, debug mode, etc.)
    setup_logging(app_data_dir, prefs["debug_mode"])
    logger.info("Application started.")
    
    engines = EngineManager(prefs)

    # Create main window with injected dependencies
    # to enable multi windows, prefs and engines are created once.
    # They can be called by importing QApplication from PySide6.QtWidgets
    # Then add: 
    # self.prefs = QApplication.instance().prefs
    # self.engines = QApplication.instance().engines
    app.prefs = prefs
    app.engines = engines
    app.search_controller = SearchController()
    # window = MainWindow(app_data_dir, prefs, engines)
    app.window = MainWindow(app_data_dir)  # first window
    app.window.show()
    #window = MainWindow(app_data_dir)
    #window.show()

    return sys.exit(app.exec())

if __name__ == "__main__":
    main()
