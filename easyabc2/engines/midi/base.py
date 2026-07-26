# easyabc2/engines/midi/base.py

class MidiPlayer:
    """
    Abstract Class to build MIDI players for easyabc.
    Unified API to be used by MPlay, FluidSynth, Dummy, etc.
    """

    def __init__(self):
        self.on_loaded = []
        self.on_paused = []
        self.on_resume = []
        self.on_stopped = []
        self.loop_enabled = False
        self.current_title = None

    def set_loop(self,enabled):
        self.loop_enabled = enabled

    def set_title(self,title):
        self.current_title = title

    def extract_midi_title(path):
        with open(path, "rb") as f:
            data = f.read()

        i = 0
        while i < len(data) - 3:
            if data[i] == 0xFF and data[i+1] == 0x03:
                length = data[i+2]
                title_bytes = data[i+3:i+3+length]
                try:
                    return title_bytes.decode("latin1")
                except:
                    return title_bytes.decode("utf-8", errors="ignore")
            i += 1

        return None

    # --- Functions to be implemented ---

    def load(self, path: str) -> bool:
        """Load MIDI file. Return True if OK."""
        raise NotImplementedError

    def play(self):
        """Start or resume playback."""
        raise NotImplementedError

    def pause(self):
        """Pause playback."""
        raise NotImplementedError

    def stop(self):
        """Stop playback."""
        raise NotImplementedError

    def seek(self, ms_or_ticks: int):
        """Shift to position."""
        raise NotImplementedError

    def tell(self) -> int:
        """Return playback position (ms ou ticks)."""
        raise NotImplementedError

    def length(self) -> int:
        """Return tune duration."""
        raise NotImplementedError

    @property
    def is_loaded(self) -> bool:
        """True if a MIDI file is loaded and ready to play."""
        raise NotImplementedError

    @property
    def is_playing(self) -> bool:
        """True if playback is currently running."""
        raise NotImplementedError

    @property
    def is_paused(self) -> bool:
        """True if playback is paused."""
        raise NotImplementedError

    @property
    def is_active(self) -> bool:
        """True if the player is currently reserved for a tune."""
        return self.is_playing or self.is_paused

    @property
    def unit_is_midi_tick(self) -> bool:
        """True if tell()/seek() in MIDI ticks."""
        return False

    @property
    def supports_tempo_change_while_playing(self) -> bool:
        return False

    @property
    def player_type(self):
        return "to_be_modified"

    # --- Helpers for callbacks ---

    def _emit_loaded(self):
        for cb in self.on_loaded:
            cb()

    def _emit_paused(self):
        for cb in self.on_paused:
            cb()

    def _emit_resumed(self):
        for cb in self.on_resume:
            cb()

    def _emit_stopped(self):
        for cb in self.on_stopped:
            cb()

class DummyMidiPlayer(MidiPlayer):
    def play(self): pass
    def pause(self): pass
    def stop(self): pass
    def seek(self, pos): pass
    def is_playing(self): return False

    @property
    def player_type(self):
        return "dummy"