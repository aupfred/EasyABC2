# easyabc2/ui/startup_assistant.py

import sys

from PySide6.QtWidgets import QMessageBox

from easyabc2.utils.easyabc_utils import run_process
from easyabc2.utils.third_party_tools_tester import (
    test_abc2midi, test_midi2abc, test_abc2svg_scripts,
    fluidsynth_service_active, fluidsynth_service_is_compatible, stop_fluidsynth_service
)
from easyabc2.ui.preferences_dialog import PreferencesDialog
from easyabc2.utils.logging_utils import logger
from easyabc2 import _

class StartupResult:
    def __init__(self):
        self.abc_tools_ok = False
        self.midi_backend = None
        self.fluidsynth_was_stopped = False
        self.needs_assistant = False

class StartupAssistant:
    """
    Ensure EasyABC2 is properly configured before real start.
    - Mandatory: abc2midi / midi2abc / abc2svg
    - Optional: MIDI backend : mplay (using external synth) / fluidsynth (lib)
    - Mandatory on Linux: FluidSynth daemon (management)
    - Mandatory if mplay: Port MIDI available for mplay
    """

    def __init__(self, prefs, parent):
        self.prefs = prefs
        self.parent = parent
        self.result = StartupResult()

    # ------------------------------------------------------------
    # ABC/MIDI tools
    # ------------------------------------------------------------
    def check_abc_tools(self):
        logger.debug("[StartupAssistant] verification of mandatory abc tools")
        missing = []

        ok, msg = test_abc2midi(self.prefs["abc2midi_path"])
        if not ok:
            logger.error("[StartupAssistant] Missing abc2midi")
            missing.append("abc2midi")

        ok, msg = test_midi2abc(self.prefs["midi2abc_path"])
        if not ok:
            logger.error("[StartupAssistant] Missing midi2abc")
            missing.append("midi2abc")

        ok, msg = test_abc2svg_scripts(self.prefs["abc2svg_scripts_path"])
        if not ok:
            logger.error("[StartupAssistant] Missing abc2svg")
            missing.append("abc2svg")

        if missing:
            QMessageBox.warning(
                None,
                _("Missing tools"),
                _("Some mandatory ABC/MIDI tools are not configured:\n") +
                "\n".join(missing) +
                _("\n\nPlease configure them in Preferences.")
            )
            self.result.needs_assistant = True
            return False

        return True

    def ensure_abc_tools(self):
        """
        Loop as abc2midi / midi2abc / abc2svg are mandatory,
        While not valid open PreferencesDialog.
        """
        while True:
            logger.debug("[StartupAssistant] Ensure ABC Tools")
            if self.check_abc_tools():
                self.result.abc_tools_ok = True
                return

            dlg = PreferencesDialog(None)
            dlg.exec()
        pass

    # ------------------------------------------------------------
    # FluidSynth daemon (Linux only)
    # ------------------------------------------------------------
    def stop_service(self):
        logger.warning("[StartupAssistant] Stop FluidSynth service")
        stop_fluidsynth_service()
        self.result.fluidsynth_was_stopped = True

    # ------------------------------------------------------------
    # Port MIDI (Linux only)
    # ------------------------------------------------------------
    def mplay_has_midi_port(self):
        if sys.platform.startswith("linux"):
            stdout, stderr, rc = run_process(["aconnect", "-l"])
            return "client" in stdout.lower()
        return True  # macOS / Windows: always OK

    # ------------------------------------------------------------
    # MIDI backend decision
    # ------------------------------------------------------------
    def decide_midi_backend(self):
        engine = self.prefs["midi_engine"]

        # MPlay
        if engine == "mplay":
            if not self.mplay_has_midi_port():
                logger.warning("[StartupAssistant] No MIDI Ports available")
                QMessageBox.warning(
                    None,
                    _("No MIDI ports available"),
                    _("MPlay is selected but no MIDI output port is available.\n"
                      "Please install TiMidity++ instead.")
                )
                return "dummy"
            return "mplay"

        # FluidSynth
        if engine == "fluidsynth":
            # Linux only: check daemon
            if sys.platform.startswith("linux"):
                if self.prefs["stop_fluidsynth_at_startup"]:
                    logger.debug("[StartupAssistant] Stop FluidSynth service if active")
                    if self.service_active():
                        self.stop_service()
                    return "fluidsynth"

                if self.service_active():
                    logger.warning("[StartupAssistant] FluidSynth service is active")
                    reply = QMessageBox.question(
                        self.parent,
                        _("FluidSynth active"),
                        _("A FluidSynth server is currently running.\n"
                          "EasyABC2 cannot use its internal synthesizer while this server is active.\n\n"
                          "Do you want to temporarily stop the FluidSynth server?\n"
                          "It will be automatically restored when EasyABC2 closes.")
                    )

                    if reply == QMessageBox.Yes:
                        self.stop_service()
                        return "fluidsynth"

                    if fluidsynth_service_is_compatible():
                        return "mplay"

                    logger.warning("[StartupAssistant] No engine available")
                    QMessageBox.warning(
                        self.parent,
                        _("FluidSynth server incompatible"),
                        _("The running FluidSynth server is not compatible with EasyABC2.\n"
                          "MPlay and the internal FluidSynth engine cannot work while this server is active.\n\n"
                          "Please stop or reconfigure the FluidSynth server or install Timidity++.")
                    )
                    return "dummy"

            # macOS / Windows : pas de daemon
            return "fluidsynth"

        # fallback
        if engine == "dummy":
            logger.warning("[StartupAssistant] MIDI Engine never configured")
            QMessageBox.warning(
                self.parent,
                _("No MIDI Player configured"),
                _("Playback of music is not available.\n"
                  "Please configure the Audio engine if you want to play music.")
            )
        return "dummy"

    # ------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------
    def run(self):
        # 1. ABC tools
        #self.result.abc_tools_ok = self.check_abc_tools()
        self.ensure_abc_tools()

        # 2. MIDI backend
        self.result.midi_backend = self.decide_midi_backend()
        logger.debug(f"[StartupAssistant] Configured engine: {self.prefs["midi_engine"]}, Detected: {self.result.midi_backend}")
        if self.result.midi_backend != self.prefs["midi_engine"]:
            QMessageBox.warning(
                self.parent,
                _("MIDI Player configuration change"),
                _("The configuration of MIDI Player will change.\n"
                  "Please check in the preference dialog the new Audio engine.")
            )
        return self.result

    # ------------------------------------------------------------
    # Assistant UI (si outils manquants)
    # ------------------------------------------------------------
    def show_configuration_assistant(self):
        QMessageBox.information(
            None,
            _("Configuration required"),
            _("EasyABC2 cannot start because mandatory tools are missing.\n"
              "Please open Preferences and configure the required paths.")
        )
