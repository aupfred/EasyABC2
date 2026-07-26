# easyabc2/utils/preferences.py
from PySide6.QtCore import QObject, Signal

import json
import os

from easyabc2.utils.easyabc_utils import THIRD_PARTY_DIR

class UserPreferences(QObject):
    theme_follow_changed = Signal()
    theme_editor_changed = Signal()
    scroll_mode_changed = Signal()
    abc2svg_path_changed = Signal()
    abc2midi_tools_path_changed = Signal()
    audio_player_changed = Signal()

    DEFAULTS = {
        "debug_mode": True,
        "abc2svg_scripts_path": str(THIRD_PARTY_DIR / "abc2svg"),
        "abc2midi_path": str(THIRD_PARTY_DIR / "abcmidi" / "abc2midi"),
        "midi2abc_path": str(THIRD_PARTY_DIR / "abcmidi" / "midi2abc"),
        "xml2abc_path": "",
        "abc2xml_path": "",
        "scroll_mode": "minimal",  # "minimal" ou "center"
        "follow_color": "#ff0000",
        "follow_theme": "light",
        "editor_theme": "light",
        "xml2abc_extra_options": "",
        "abc2xml_extra_options": "",
        "midi_engine": "mplay",
        "fluidsynth_library_path": "",
        "soundfont_path": "soundfonts/FluidR3_GM.sf2",
        "fluidsynth_gain": 1.0,
        "fluidsynth_buffer": 2048,
        "fluidsynth_driver": "",
        "fluidsynth_reverb_room": 0.2,
        "fluidsynth_reverb_damp": 0.0,
        "fluidsynth_reverb_width": 0.5,
        "fluidsynth_reverb_level": 0.9,
        "fluidsynth_chorus_nr": 3,
        "fluidsynth_chorus_level": 1.2,
        "fluidsynth_chorus_speed": 0.3,
        "fluidsynth_chorus_depth": 8.0,
        "fluidsynth_chorus_type": 0,
        "recent_files": [],
        "last_opened_file": "",
        "restore_last_file": True,
        "window_geometry": None,
        "window_state": None,
        "session_open_files": [],
        "session_active_file": None,
    }

    def __init__(self, filepath="preferences.json"):
        super().__init__()
        self.filepath = filepath
        self.data = dict(self.DEFAULTS)
        self.load()

        self._pending_changes = {
            "theme_follow": False,
            "theme_editor": False,
            "scroll_mode": False,
            "abc2svg": False,
            "abc2midi": False,
            "midi2abc": False,
            "audio_player": False,
        }

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.data.update(json.load(f))
            except Exception:
                pass  # fallback default values

    def save(self):
        # make sure that all prefs are in json (typically to avoid to have a path as a Path)
        safe_data = self._make_json_safe(self.data)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(safe_data, f, indent=4)
            
        # Once saved emit signals to propagate changes
        if self._pending_changes["theme_follow"]:
            self.theme_follow_changed.emit()

        if self._pending_changes["theme_editor"]:
            self.theme_editor_changed.emit()

        if self._pending_changes["scroll_mode"]:
            self.scroll_mode_changed.emit()

        if self._pending_changes["abc2svg"]:
            self.abc2svg_path_changed.emit()

        if self._pending_changes["abc2midi"]:
            self.abc2midi_tools_path_changed.emit()

        if self._pending_changes["audio_player"]:
            self.audio_player_changed.emit()

        # Flags reset
        for key in self._pending_changes:
            self._pending_changes[key] = False

    # To access: prefs["scroll_mode"]
    def __getitem__(self, key):
        return self.data.get(key, self.DEFAULTS.get(key))

    def __setitem__(self, key, value):
        #self.data[key] = value
        old = self.data.get(key)
        if old == value:
            return

        self.data[key] = value

        if key == "follow_theme":
            self._pending_changes["theme_follow"] = True

        elif key == "editor_theme":
            self._pending_changes["theme_editor"] = True

        elif key == "scroll_mode":
            self._pending_changes["scroll_mode"] = True

        elif key == "abc2svg_scripts_path":
            self._pending_changes["abc2svg"] = True

        elif key in ("abc2midi_path", "midi2abc_path"):
            self._pending_changes["abc2midi"] = True

        elif key in (
            "midi_engine",
            "soundfont_path",
            "fluidsynth_library_path",
            "fluidsynth_gain",
            "fluidsynth_buffer",
            "fluidsynth_driver",
            "fluidsynth_reverb_room",
            "fluidsynth_reverb_damp",
            "fluidsynth_reverb_width",
            "fluidsynth_reverb_level",
            "fluidsynth_chorus_nr",
            "fluidsynth_chorus_level",
            "fluidsynth_chorus_speed",
            "fluidsynth_chorus_depth",
            "fluidsynth_chorus_type",
        ):
            self._pending_changes["audio_player"] = True

    def _make_json_safe(self, obj, key=None):
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj

        if isinstance(obj, list):
            return [self._make_json_safe(v, key) for v in obj]

        if isinstance(obj, dict):
            return {k: self._make_json_safe(v, k) for k, v in obj.items()}

        if hasattr(obj, "__fspath__"):
            return str(obj)

        if key in self.DEFAULTS:
            logger.warning(f"Invalid preference '{key}' replaced by default value.")
            return self.DEFAULTS[key]

        logger.warning(f"Non-serializable preference value converted to string: {obj!r}")
        return str(obj)
