# easyabc2/engines/midi/mplay.py

# MIDI player in Python to enable playing on Mac without the need to install fluidsynth

import os
import sys

from easyabc2.engines.midi.base import MidiPlayer
from easyabc2.engines.midi.smf_ext import SMFExt

if sys.platform == "darwin":
    from easyabc2.third_party.mplay.darwinmidi import midiDevice
elif sys.platform == 'win32':
    from easyabc2.third_party.mplay.win32midi import midiDevice
else:
    raise ImportError("MPlaySMFPlayer is only supported on macOS")

from easyabc2.utils.logging_utils import logger

logger.debug("[MPLay] Importing…")

class MPlaySMFPlayer(MidiPlayer):
    """
    MIDI Player based on mplay (CoreMIDI), reworked for easyabc2 on Qt.
    """

    def __init__(self):
        super().__init__()
        logger.debug("[MPLay] initPlay")

        self.device = midiDevice()
        self.midi_file = None

        self._is_play_started = False
        self._is_paused = False
        self._playback_rate = 1.0

    @property
    def player_type(self):
        return "mplay"
    
    # ------------------------------------------------------------
    # Load
    # ------------------------------------------------------------

    def load(self, path: str) -> bool:
        if not os.path.exists(path):
            return False

        try:
            self.device = midiDevice()
            self.midi_file = SMFExt()
            self.midi_file.read(path)
            self._emit_loaded()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------
    # Player functions
    # ------------------------------------------------------------

    def play(self):
        if not self.midi_file:
            return

        if not self._is_play_started:
            logger.debug("[MPLay] Play")
            # First play
            self.midi_file.play(self.device, wait=False)
            self._is_play_started = True
            self._is_paused = False
        else:
            logger.debug("[MPLay] Pause")
            # Resume after pause
            self.pause()  # setsong(action='pause') toggle

    def idle(self):
        if not self.midi_file:
            return

        if self.is_playing:
            delta=self.midi_file.play(self.device, wait=False)
            logger.debug(f"[MPLay] delta: {delta}")
            if delta ==0:
                self._is_play_started = False
                self._is_paused = False
            else:    
                self.is_really_playing = True

    def pause(self):
        if not self.midi_file:
            return

        self.midi_file.setsong(action="pause")
        self._is_paused = not self._is_paused

    def stop(self):
        if not self.midi_file:
            return

        self.midi_file.setsong(action="exit")
        self.device = midiDevice()
        self._is_play_started = False
        self._is_paused = False
        self._emit_stopped()

    # ------------------------------------------------------------
    # Position
    # ------------------------------------------------------------

    def seek(self, time):
        """time = ticks"""
        if not self.midi_file:
            return

        if time < 0 or time > self.length():
            logger.error(f"[MPlay] Seek time is not valid: 0 < {time} < {self.duration_in_ticks}")
            return

        self.midi_file.setsong(goto=time)

    def tell(self):
        if not self.midi_file:
            return 0

        return self.midi_file.getsongposition()

    def length(self):
        if not self.midi_file:
            return 0

        # Length in ticks
        # MPlay returns higher ticks than MIDI file. About 960 ticks
        return self.midi_file.playing_time - 960

    # ------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------

    @property
    def is_playing(self):
        return self._is_play_started and not self._is_paused

    @property
    def is_paused(self):
        return self._is_paused

    @property
    def unit_is_midi_tick(self):
        return True

    @property
    def supports_tempo_change_while_playing(self):
        return True

    @property
    def playback_rate(self):
        return self._playback_rate

    @playback_rate.setter
    def playback_rate(self, value):
        self._playback_rate = value
        if self.midi_file:
            self.midi_file.setsong(multibpm=value)
