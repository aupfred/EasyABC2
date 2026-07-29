# easyabc2/ui/preferences_dialog.py
#from gettext import gettext as _

import os

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication, QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QRadioButton, QColorDialog,
    QDialogButtonBox, QPlainTextEdit
)
from PySide6.QtGui import QColor

from easyabc2.ui.abc_editor import ABCEditor
from easyabc2.engines.midi.fluidsynthplayer import find_fluidsynth_library, load_fluidsynth_from_path, find_soundfont

from easyabc2.utils.easyabc_utils import run_process
from easyabc2.utils.third_party_tools_tester import (
    test_abc2midi, test_midi2abc, test_abc2svg_scripts,
    test_fluidsynth_library, test_soundfont,
    test_xml2abc, test_abc2xml
)
from easyabc2 import _

class PreferencesDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(_("Settings"))
        self.prefs = QApplication.instance().prefs

        self.tabs = QTabWidget()
        self.tab_paths = self._create_paths_tab()
        self.tabs.addTab(self.tab_paths, _("ABC tools paths"))

        self.tab_audio = self._create_audio_tab()
        self.tabs.addTab(self.tab_audio, _("Audio / MIDI"))

        self.tab_follow = self._create_follow_tab()
        self.tabs.addTab(self.tab_follow, _("Follow behavior"))

        self.tab_theme = self._create_theme_tab()
        self.tabs.addTab(self.tab_theme, _("Theme"))

        self.tab_xmlabc = self._create_xmlabc_tab()
        self.tabs.addTab(self.tab_xmlabc, _("XML ↔ ABC (Advanced)"))

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        self.buttons.accepted.connect(self.on_ok)
        self.buttons.rejected.connect(self.reject)
        self.buttons.button(QDialogButtonBox.Apply).clicked.connect(self.on_apply)

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

        self.resize(600, 400)
        QTimer.singleShot(0, self._run_initial_tests)

    # ------------------------------------------------------------
    # Tab Path
    # ------------------------------------------------------------
    def _create_paths_tab(self):
        widget = QWidget()
        grid = QGridLayout()

        def add_path_with_test(row, label, key, is_dir, test_func):
            lbl = QLabel(label)
            txt = QLineEdit(self.prefs[key])

            btn_browse = QPushButton(_("Browse…"))
            btn_test = QPushButton(_("Test…"))
            lbl_status = QLabel("")

            def browse():
                if is_dir:
                    path = QFileDialog.getExistingDirectory(self, _("Choose a directory"))
                else:
                    path, _filter = QFileDialog.getOpenFileName(self, _("Choose a file"))
                if path:
                    txt.setText(path)
                    test()

            def test():
                ok, msg = test_func(txt.text().strip())
                lbl_status.setText(msg)

            btn_browse.clicked.connect(browse)
            btn_test.clicked.connect(test)

            grid.addWidget(lbl, row, 0)
            grid.addWidget(txt, row, 1)
            grid.addWidget(btn_browse, row, 2)
            grid.addWidget(btn_test, row, 3)
            grid.addWidget(lbl_status, row + 1, 1, 1, 3)

            return txt, lbl_status

        self.txt_abc2midi, self.lbl_abc2midi_status = add_path_with_test(
            0, "abc2midi:", "abc2midi_path", False, test_abc2midi
        )

        self.txt_midi2abc, self.lbl_midi2abc_status = add_path_with_test(
            2, "midi2abc:", "midi2abc_path", False, test_midi2abc
        )

        self.txt_abc2svg, self.lbl_abc2svg_status = add_path_with_test(
            4, "abc2svg scripts:", "abc2svg_scripts_path", True, test_abc2svg_scripts
        )

        self.txt_xml2abc, self.lbl_xml2abc_status = add_path_with_test(
            6, "xml2abc.py:", "xml2abc_path", False, test_xml2abc
        )

        self.txt_abc2xml, self.lbl_abc2xml_status = add_path_with_test(
            8, "abc2xml.py:", "abc2xml_path", False, test_abc2xml
        )

        widget.setLayout(grid)
        return widget

    # ------------------------------------------------------------
    # Tab: Audio/MIDI
    # ------------------------------------------------------------
    def _create_audio_tab(self):
        widget = QWidget()
        grid = QGridLayout()
        row = 0

        # MIDI engine selection
        lbl_engine = QLabel(_("MIDI Engine:"))
        self.radio_mplay = QRadioButton("MPlay")
        self.radio_fluidsynth = QRadioButton("FluidSynth")

        #engine = self.prefs.get("midi_engine", "mplay")
        engine = self.prefs["midi_engine"]
        if engine == "fluidsynth":
            self.radio_fluidsynth.setChecked(True)
        else:
            self.radio_mplay.setChecked(True)

        grid.addWidget(lbl_engine, row, 0)
        grid.addWidget(self.radio_mplay, row, 1)
        grid.addWidget(self.radio_fluidsynth, row, 2)
        row += 1

        def add_audio_path_with_test(row, label, key, is_lib, test_func):
            lbl = QLabel(label)
            txt = QLineEdit(self.prefs[key])

            btn_browse = QPushButton(_("Browse…"))
            btn_test = QPushButton(_("Search/Test"))
            lbl_status = QLabel("")

            def browse():
                if is_lib:
                    path = QFileDialog.getExistingDirectory(self, _("Choose path to fluidynth library"))
                else:
                    path, _filter = QFileDialog.getOpenFileName(self, _("Choose a SoundFont"), "", "SoundFont (*.sf2 *.sf3)")
                if path:
                    txt.setText(path)
                    test()

            def test():
                test_func(txt, lbl_status)

            btn_browse.clicked.connect(browse)
            btn_test.clicked.connect(test)

            grid.addWidget(lbl, row, 0)
            grid.addWidget(txt, row, 1)
            grid.addWidget(btn_browse, row, 2)
            grid.addWidget(btn_test, row, 3)
            grid.addWidget(lbl_status, row + 1, 1, 1, 3)

            return txt, lbl_status

        def search_soundfont(txt, lbl_status):
            current = txt.text().strip()
            sf = find_soundfont(current)
            if sf:
                txt.setText(sf)
            ok, msg = test_soundfont(txt.text().strip(),self.txt_fslib.text().strip())
            lbl_status.setText(msg)

        def search_lib(txt, lbl_status):
            current = txt.text().strip()
            lib = find_fluidsynth_library(current)
            if lib:
                txt.setText(lib)
            ok, msg = test_fluidsynth_library(txt.text().strip())
            lbl_status.setText(msg)

        self.txt_fslib, self.lbl_fslib_status = add_audio_path_with_test(
            row,
            _("FluidSynth library:"),
            "fluidsynth_library_path",
            True,
            search_lib
            #test_fluidsynth_library
        )
        
        row += 2

        self.txt_soundfont_audio, self.lbl_soundfont_status = add_audio_path_with_test(
            row,
            _("SoundFont:"),
            "soundfont_path",
            False,
            search_soundfont
        )

        # UI activation logic
        self.radio_mplay.toggled.connect(self._update_audio_ui)
        self.radio_fluidsynth.toggled.connect(self._update_audio_ui)
        self._update_audio_ui()

        widget.setLayout(grid)
        return widget

    def _update_audio_ui(self):
        use_fs = self.radio_fluidsynth.isChecked()
        self.txt_soundfont_audio.setEnabled(use_fs)
        self.txt_fslib.setEnabled(use_fs)

        ok, msg = test_fluidsynth_library(self.txt_fslib.text().strip())
        self.lbl_fslib_status.setText(msg)

        ok, msg = test_soundfont(self.txt_soundfont_audio.text().strip(),self.txt_fslib.text().strip())
        self.lbl_soundfont_status.setText(msg)

    # ------------------------------------------------------------
    # Tab: Follow Notes
    # ------------------------------------------------------------
    def _create_follow_tab(self):
        widget = QWidget()
        vbox = QVBoxLayout()

        # --- Scroll mode ---
        scroll_label = QLabel(_("Scroll Mode:"))
        self.radio_minimal = QRadioButton(_("Minimal"))
        self.radio_center = QRadioButton(_("Center"))

        if self.prefs["scroll_mode"] == "center":
            self.radio_center.setChecked(True)
        else:
            self.radio_minimal.setChecked(True)

        vbox.addWidget(scroll_label)
        vbox.addWidget(self.radio_minimal)
        vbox.addWidget(self.radio_center)

        # --- Color ---
        color_label = QLabel(_("Color on follow:"))
        self.btn_color = QPushButton(_("Choose color…"))
        self.btn_color.clicked.connect(self.choose_color)

        self.current_color = QColor(self.prefs["follow_color"])

        vbox.addWidget(color_label)
        vbox.addWidget(self.btn_color)

        widget.setLayout(vbox)
        return widget

    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self, _("Choose color…"))
        if color.isValid():
            self.current_color = color

    def _create_theme_tab(self):
        widget = QWidget()
        vbox = QVBoxLayout()

        label = QLabel(_("Editor theme:"))

        self.radio_light = QRadioButton("Light")
        self.radio_dark = QRadioButton("Dark")
        self.radio_solarized = QRadioButton("Solarized")
        self.radio_easyabc2 = QRadioButton("EasyABC2")

        theme = self.prefs["editor_theme"]
        if theme == "dark":
            self.radio_dark.setChecked(True)
        elif theme == "solarized":
            self.radio_solarized.setChecked(True)
        elif theme == "easyabc2":
            self.radio_easyabc2.setChecked(True)
        else:
            self.radio_light.setChecked(True)

        vbox.addWidget(label)
        vbox.addWidget(self.radio_light)
        vbox.addWidget(self.radio_dark)
        vbox.addWidget(self.radio_solarized)
        vbox.addWidget(self.radio_easyabc2)

        #self.preview = QPlainTextEdit()
        #self.preview = CodeEditor(self.prefs)
        self.preview = ABCEditor()
        self.preview.setReadOnly(True)
        self.preview.setPlainText('''X:1
T:Preview
M:4/4
K:C
C D E F | G A B c |
"Am" C2 {abc} !trill! G4
w: Ceci est un aperçu du thème
    ''')
        #self.preview_highlighter = ABCHighlighter(self.preview.document(), self.prefs)
        self.radio_light.toggled.connect(self.update_preview_theme)
        self.radio_dark.toggled.connect(self.update_preview_theme)
        self.radio_solarized.toggled.connect(self.update_preview_theme)
        self.radio_easyabc2.toggled.connect(self.update_preview_theme)


        vbox.addWidget(self.preview)

        widget.setLayout(vbox)
        return widget

    def update_preview_theme(self):
        if self.radio_dark.isChecked():
            self.prefs["editor_theme"] = "dark"
        elif self.radio_solarized.isChecked():
            self.prefs["editor_theme"] = "solarized"
        elif self.radio_easyabc2.isChecked():
            self.prefs["editor_theme"] = "easyabc2"
        else:
            self.prefs["editor_theme"] = "light"

        # Rebuild formats in the preview highlighter
        #self.preview_highlighter._build_formats()
        #self.preview_highlighter.rehighlight()
        self.preview.preview_theme(self.prefs)

    def _create_xmlabc_tab(self):
        widget = QWidget()
        grid = QGridLayout()
        row = 0

        # -------------------------
        # xml2abc extra options
        # -------------------------
        lbl_xml2abc = QLabel(_("<b>xml2abc extra options</b>"))
        grid.addWidget(lbl_xml2abc, row, 0, 1, 2)
        row += 1

        grid.addWidget(QLabel(_("Additional command-line options:")), row, 0)
        self.txt_xml2abc_extra = QLineEdit(self.prefs["xml2abc_extra_options"])
        grid.addWidget(self.txt_xml2abc_extra, row, 1)
        row += 1

        btn_xml2abc_help = QPushButton(_("Show xml2abc help…"))
        btn_xml2abc_help.clicked.connect(self._load_xml2abc_help)
        grid.addWidget(btn_xml2abc_help, row, 0, 1, 2)
        row += 1

        self.txt_xml2abc_help = QPlainTextEdit()
        self.txt_xml2abc_help.setReadOnly(True)
        self.txt_xml2abc_help.setPlaceholderText(_("xml2abc help will appear here…"))
        grid.addWidget(self.txt_xml2abc_help, row, 0, 1, 2)
        row += 1

        # -------------------------
        # abc2xml extra options
        # -------------------------
        lbl_abc2xml = QLabel(_("<b>abc2xml extra options</b>"))
        grid.addWidget(lbl_abc2xml, row, 0, 1, 2)
        row += 1

        grid.addWidget(QLabel(_("Additional command-line options:")), row, 0)
        self.txt_abc2xml_extra = QLineEdit(self.prefs["abc2xml_extra_options"])
        grid.addWidget(self.txt_abc2xml_extra, row, 1)
        row += 1

        btn_abc2xml_help = QPushButton(_("Show abc2xml help…"))
        btn_abc2xml_help.clicked.connect(self._load_abc2xml_help)
        grid.addWidget(btn_abc2xml_help, row, 0, 1, 2)
        row += 1

        self.txt_abc2xml_help = QPlainTextEdit()
        self.txt_abc2xml_help.setReadOnly(True)
        self.txt_abc2xml_help.setPlaceholderText(_("abc2xml help will appear here…"))
        grid.addWidget(self.txt_abc2xml_help, row, 0, 1, 2)
        row += 1

        widget.setLayout(grid)
        return widget

    def _load_xml2abc_help(self):
        path = self.prefs["xml2abc_path"]
        if not path:
            self.txt_xml2abc_help.setPlainText(_("No xml2abc path configured."))
            return

        stdout, stderr, code = run_process(["python", path, "-h"])
        help_text = stdout if stdout else stderr
        self.txt_xml2abc_help.setPlainText(help_text)


    def _load_abc2xml_help(self):
        path = self.prefs["abc2xml_path"]
        if not path:
            self.txt_abc2xml_help.setPlainText(_("No abc2xml path configured."))
            return

        stdout, stderr, code = run_process(["python", path, "-h"])
        help_text = stdout if stdout else stderr
        self.txt_abc2xml_help.setPlainText(help_text)

    # ------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------
    def on_apply(self):
        self._save_to_prefs()
        self.prefs.save()

    def on_ok(self):
        self._save_to_prefs()
        self.prefs.save()
        self.accept()

    # ------------------------------------------------------------
    # Save prefs
    # ------------------------------------------------------------
    def _save_to_prefs(self):
        self.prefs["abc2midi_path"] = self.txt_abc2midi.text()
        self.prefs["midi2abc_path"] = self.txt_midi2abc.text()
        self.prefs["abc2svg_scripts_path"] = self.txt_abc2svg.text()
        self.prefs["xml2abc_path"] = self.txt_xml2abc.text()
        self.prefs["abc2xml_path"] = self.txt_abc2xml.text()

        self.prefs["scroll_mode"] = "center" if self.radio_center.isChecked() else "minimal"
        self.prefs["follow_color"] = self.current_color.name()

        self.prefs["xml2abc_extra_options"] = self.txt_xml2abc_extra.text()
        self.prefs["abc2xml_extra_options"] = self.txt_abc2xml_extra.text()

        self.prefs["midi_engine"] = "fluidsynth" if self.radio_fluidsynth.isChecked() else "mplay"
        self.prefs["soundfont_path"] = self.txt_soundfont_audio.text()
        self.prefs["fluidsynth_library_path"] = self.txt_fslib.text()

    def _run_initial_tests(self):
        # Paths tab
        if self.prefs["abc2midi_path"]:
            ok, msg = test_abc2midi(self.prefs["abc2midi_path"])
            self.lbl_abc2midi_status.setText(msg)

        if self.prefs["midi2abc_path"]:
            ok, msg = test_midi2abc(self.prefs["midi2abc_path"])
            self.lbl_midi2abc_status.setText(msg)

        if self.prefs["abc2svg_scripts_path"]:
            ok, msg = test_abc2svg_scripts(self.prefs["abc2svg_scripts_path"])
            self.lbl_abc2svg_status.setText(msg)

        if self.prefs["xml2abc_path"]:
            ok, msg = test_xml2abc(self.prefs["xml2abc_path"])
            self.lbl_xml2abc_status.setText(msg)

        if self.prefs["abc2xml_path"]:
            ok, msg = test_abc2xml(self.prefs["abc2xml_path"])
            self.lbl_abc2xml_status.setText(msg)

        # Audio tab (only if FluidSynth is selected)
        if self.prefs["midi_engine"] == "fluidsynth":
            if self.prefs["fluidsynth_library_path"]:
                ok, msg = test_fluidsynth_library(self.prefs["fluidsynth_library_path"])
                self.lbl_fslib_status.setText(msg)

                if self.prefs["soundfont_path"]:
                    ok, msg = test_soundfont(self.prefs["soundfont_path"],self.prefs["fluidsynth_library_path"])
                    self.lbl_soundfont_status.setText(msg)
