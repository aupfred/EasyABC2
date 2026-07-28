# easyabc2/ui/preferences_dialog.py
#from gettext import gettext as _

import os

from PySide6.QtWidgets import (
    QApplication, QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QRadioButton, QColorDialog,
    QDialogButtonBox, QPlainTextEdit
)
from PySide6.QtGui import QColor

from easyabc2.ui.abc_editor import ABCEditor
from easyabc2.engines.midi.fluidsynthplayer import find_fluidsynth_library, load_fluidsynth_from_path

from easyabc2.utils.easyabc_utils import run_process
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

    # ------------------------------------------------------------
    # Tab Path
    # ------------------------------------------------------------
    def _create_paths_tab(self):
        widget = QWidget()
        grid = QGridLayout()

        def add_path(row, label, key):
            lbl = QLabel(label)
            txt = QLineEdit(self.prefs[key])
            btn = QPushButton(_("Browse…"))

            def browse():
                path, _filter = QFileDialog.getOpenFileName(self, _("Choose a file"))
                if path:
                    txt.setText(path)

            btn.clicked.connect(browse)

            grid.addWidget(lbl, row, 0)
            grid.addWidget(txt, row, 1)
            grid.addWidget(btn, row, 2)

            return txt

        def add_dir(row, label, key):
            lbl = QLabel(_(label))
            txt = QLineEdit(self.prefs[key])
            btn = QPushButton(_("Browse…"))

            def browse():
                path = QFileDialog.getExistingDirectory(self, _("Choose a directory"))
                if path:
                    txt.setText(path)

            btn.clicked.connect(browse)

            grid.addWidget(lbl, row, 0)
            grid.addWidget(txt, row, 1)
            grid.addWidget(btn, row, 2)

            return txt

        self.txt_abc2midi = add_path(0, "abc2midi:", "abc2midi_path")
        self.txt_midi2abc = add_path(1, "midi2abc:", "midi2abc_path")
        self.txt_abc2svg = add_dir(2, "abc2svg scripts:", "abc2svg_scripts_path")
        self.txt_soundfont = add_path(3, "SoundFont:", "soundfont_path")
        self.txt_xml2abc = add_path(4, "xml2abc.py:", "xml2abc_path")
        self.txt_abc2xml = add_path(5, "abc2xml.py:", "abc2xml_path")

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

        # SoundFont path
        lbl_sf = QLabel(_("SoundFont:"))
        self.txt_soundfont_audio = QLineEdit(self.prefs["soundfont_path"])
        btn_sf = QPushButton(_("Browse…"))

        def browse_sf():
            path, _filter = QFileDialog.getOpenFileName(self, _("Choose a SoundFont"), "", "SoundFont (*.sf2 *.sf3)")
            if path:
                self.txt_soundfont_audio.setText(path)

        btn_sf.clicked.connect(browse_sf)

        grid.addWidget(lbl_sf, row, 0)
        grid.addWidget(self.txt_soundfont_audio, row, 1)
        grid.addWidget(btn_sf, row, 2)
        row += 1

        # FluidSynth library path
        lbl_lib = QLabel(_("FluidSynth library:"))
        self.txt_fslib = QLineEdit(self.prefs["fluidsynth_library_path"])

        btn_lib_browse = QPushButton(_("Browse…"))
        btn_lib_search = QPushButton(_("Search/Test"))

        def browse_lib():
            path, _filter = QFileDialog.getOpenFileName(self, _("Choose FluidSynth library"))
            if path:
                self.txt_fslib.setText(path)

        btn_lib_browse.clicked.connect(browse_lib)

        def search_lib():
            current = self.txt_fslib.text().strip()
            lib = find_fluidsynth_library(current)
            if lib:
                self.txt_fslib.setText(lib)
                self._update_fslib_status()
            else:
                self.lbl_fslib_status.setText(_("No library found. For instance, on Debian you might find it in /usr/lib/x86_64-linux-gnu/libfluidsynth.so.3"))

        btn_lib_search.clicked.connect(search_lib)

        grid.addWidget(lbl_lib, row, 0)
        grid.addWidget(self.txt_fslib, row, 1)
        grid.addWidget(btn_lib_browse, row, 2)
        grid.addWidget(btn_lib_search, row, 3)
        row += 1

        # Library status
        self.lbl_fslib_status = QLabel("")
        grid.addWidget(self.lbl_fslib_status, row, 1, 1, 3)
        row += 1

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
        self._update_fslib_status()

    def _update_fslib_status(self):
        path = self.txt_fslib.text().strip()
        if not path:
            self.lbl_fslib_status.setText(_("No library configured"))
            return
        if not os.path.exists(path):
            self.lbl_fslib_status.setText(_("Invalid path.  For instance, on Debian you might find it in /usr/lib/x86_64-linux-gnu/libfluidsynth.so.3"))
            return

        try:
            F = load_fluidsynth_from_path(path)
            from ctypes import c_int, byref
            x, y, z = c_int(), c_int(), c_int()
            try:
                F.fluid_version(byref(x), byref(y), byref(z))
                version = f"{x.value}.{y.value}.{z.value}"
            except:
                version = None
            if version:
                self.lbl_fslib_status.setText(_("OK — FluidSynth version: ") + version)
            else:
                self.lbl_fslib_status.setText(_("Library loaded, but version unknown"))
        except Exception as e:
            self.lbl_fslib_status.setText(_("Found library but cannot load: ") + str(e))

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
        self.prefs["soundfont_path"] = self.txt_soundfont.text()
        self.prefs["xml2abc_path"] = self.txt_xml2abc.text()
        self.prefs["abc2xml_path"] = self.txt_abc2xml.text()

        self.prefs["scroll_mode"] = "center" if self.radio_center.isChecked() else "minimal"
        self.prefs["follow_color"] = self.current_color.name()

        self.prefs["xml2abc_extra_options"] = self.txt_xml2abc_extra.text()
        self.prefs["abc2xml_extra_options"] = self.txt_abc2xml_extra.text()

        self.prefs["midi_engine"] = "fluidsynth" if self.radio_fluidsynth.isChecked() else "mplay"
        self.prefs["soundfont_path"] = self.txt_soundfont_audio.text()
        self.prefs["fluidsynth_library_path"] = self.txt_fslib.text()
