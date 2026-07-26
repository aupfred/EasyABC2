import sys, os
#from .dummy import DummyMidiPlayer
from easyabc2.engines.midi.base import MidiPlayer, DummyMidiPlayer
from easyabc2.utils.logging_utils import logger

logger.debug("[Midi] Importing…")

try:
    from easyabc2.engines.midi.fluidsynthplayer import FluidSynthPlayer
except Exception:
    print("No FluidSynth")
    logger.debug("[Midi] No FluidSynth Player")
    FluidSynthPlayer = None
from easyabc2.engines.midi.fluidsynthplayer import FluidSynthPlayer
try:
    from easyabc2.engines.midi.mplay import MPlaySMFPlayer
    #from .mplay import MPlaySMFPlayer
except Exception:
    logger.debug("[Midi] No MPlay SMF Player")
    MPlaySMFPlayer = None

def create_midi_player(preferences):
    """
    Return MIDI player based on OS and User settings.
    """
    #return MPlaySMFPlayer()
    logger.debug("[Midi] Create MIDI Player")
    sf2 = preferences["soundfont_path"]
    logger.debug(f"[Midi] soundfont {sf2}")

    # 1) In case soundfont chosen → FluidSynth first
    if sf2 and FluidSynthPlayer:
        logger.debug("[Midi] try fluidsynth MIDI Player")
        try:
            return FluidSynthPlayer(sf2)
        except Exception:
            logger.error("[Midi] Create exception: No FluidSynth Player")
            pass

    # 2) On macOS → MPlay (using native OS capacity)
    if sys.platform == "darwin" and MPlaySMFPlayer:
        try:
            return MPlaySMFPlayer()
        except Exception:
            logger.error("[Midi] Create exception: No MPlay SMF Player")
            pass

    # 4) Fallback → Dummy
    return DummyMidiPlayer()

def create_midi_player(preferences):
    """
    Create MIDI player based on user preferences and platform.
    """

    engine = preferences["midi_engine"]

    # MPlay selected
    if engine == "mplay":
        if MPlaySMFPlayer:
            try:
                return MPlaySMFPlayer()
            except Exception:
                pass
        return DummyMidiPlayer()

    # FluidSynth selected
    if engine == "fluidsynth":
        sf2 = preferences["soundfont_path"]
        lib = preferences["fluidsynth_library_path"]

        # Missing library
        if not lib or not os.path.exists(lib):
            return DummyMidiPlayer()

        # Missing soundfont
        if not sf2 or not os.path.exists(sf2):
            return DummyMidiPlayer()

        if FluidSynthPlayer:
            try:
                return FluidSynthPlayer(preferences)
            except Exception:
                pass

        return DummyMidiPlayer()

    # Unknown engine → fallback
    return DummyMidiPlayer()
