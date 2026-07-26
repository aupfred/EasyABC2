# easyabc2/engines/abc2midi_engine.py

import os
import re
from pathlib import Path

from easyabc2.utils.easyabc_utils import get_output_from_process
from easyabc2.utils.logging_utils import logger

logger.debug("[ABC2MIDIEngine] Importing…")

class Abc2MidiEngine:
    def __init__(self, prefs):
        self.prefs = prefs  # UserPreferences

    def _add_abc2midi_options(self, cmd, add_follow_score_markers: bool):
        # Todo: management of additionnal options
        # e.g.: if self.prefs["nofermatas"]: cmd.append("-NFER")
        if add_follow_score_markers:
            cmd.append("-EA")
        return cmd

    def abc_to_midi(self, abc_code: str, midi_file_name: str, add_follow_score_markers: bool):
        abc2midi_path = self.prefs["abc2midi_path"]
        cmd = [abc2midi_path, "-", "-o", midi_file_name]
        cmd = self._add_abc2midi_options(cmd, add_follow_score_markers)

        input_abc = abc_code + os.linesep * 2
        stdout, stderr, code = get_output_from_process(cmd, input_text=input_abc)

        if code != 0:
            raise RuntimeError(stderr or f"abc2midi exited with code {code}")

        if stdout:
            stdout = re.sub(r'(?m)(writing MIDI file .*\r?\n?)', '', stdout)

        return midi_file_name

    def build_follow_data(self, abc_code: str, mid_path: Path):
        self.abc_to_midi(abc_code, str(mid_path), add_follow_score_markers=True)

        midi2abc_path = self.prefs["midi2abc_path"]
        mftext, stderr, code = get_output_from_process(
            [midi2abc_path, str(mid_path), "-mftext"]
        )
        if code != 0 or not mftext.strip():
            raise RuntimeError(stderr or "mftext vide")

        return mftext

    def apply_preferences(self, prefs):
        self.prefs = prefs