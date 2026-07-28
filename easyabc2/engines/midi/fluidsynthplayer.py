# easyabc2/engines/midi/fluidsynthplayer.py

from __future__ import unicode_literals
import re
import os
import io
import os.path
import time
import sys
import glob
from ctypes import c_int, byref, CDLL, c_void_p, c_char_p, c_double
from ctypes.util import find_library

from easyabc2.engines.midi.base import MidiPlayer
from easyabc2.engines.midi.fluidsynth import Synth, Player
from easyabc2.utils.logging_utils import logger

logger.debug("[FluidSynthPlayer] Importing…")

def find_fluidsynth_library(user_path=None):
    """
    Returns a valid FluidSynth library path.
    Never overwrites a valid user path.
    Provides OS-specific fallbacks.
    """

    # --- 1. User path takes priority ---
    if user_path:
        up = user_path.strip()
        if os.path.exists(up):
            try:
                CDLL(up)
                return up
            except Exception:
                logger.error(f"[FluidSynth] User path invalid: {up}")

    # --- 2. OS-specific known locations ---
    candidates = []

    if sys.platform == "darwin":
        candidates += [
            "/Library/Frameworks/FluidSynth.framework/FluidSynth",
            "/opt/homebrew/lib/libfluidsynth.dylib",
            "/usr/local/lib/libfluidsynth.dylib",
        ]

    elif sys.platform.startswith("linux"):
        candidates += [
            "/usr/lib/x86_64-linux-gnu/libfluidsynth.so",
            "/usr/lib/x86_64-linux-gnu/libfluidsynth.so.3",
        ]

    elif sys.platform.startswith("win"):
        candidates += [
            "C:\\Windows\\System32\\fluidsynth.dll",
            "C:\\Program Files\\Fluidsynth\\fluidsynth.dll",
        ]

    # --- 3. Test candidates ---
    for c in candidates:
        if os.path.exists(c):
            try:
                CDLL(c)
                return c
            except Exception:
                pass

    # --- 4. Fallback: find_library ---
    lib = (
        find_library("fluidsynth")
        or find_library("libfluidsynth")
        or find_library("libfluidsynth-2")
    )

    if lib:
        try:
            CDLL(lib)
            return lib
        except Exception:
            pass

    # --- 5. Final failure ---
    return None

def load_fluidsynth_from_path(lib):
    try:
        F=CDLL(lib)
        logger.debug(f"[FluidSynthPlayer] Loaded library: {lib}")
        try:
            x, y, z = c_int (), c_int (), c_int ()
            F.fluid_version (byref (x), byref (y), byref (z))
            logger.debug(f"{lib} loaded, version: {x.value}.{y.value}.{z.value}")
        except:
            logger.error("[FluidSynth] Cannot read version (maybe FluidSynth 1.x?)")

        # --- settings ---
        # new_fluid_settings()
        F.new_fluid_settings.argtypes = []
        F.new_fluid_settings.restype = c_void_p

        F.fluid_settings_setnum.argtypes = [c_void_p, c_char_p, c_double]
        F.fluid_settings_setnum.restype = c_int

        F.fluid_settings_setint.argtypes = [c_void_p, c_char_p, c_int]
        F.fluid_settings_setint.restype = c_int

        F.fluid_settings_setstr.argtypes = [c_void_p, c_char_p, c_char_p]
        F.fluid_settings_setstr.restype = c_int

        F.fluid_settings_getint.argtypes = [c_void_p, c_char_p, c_void_p]
        F.fluid_settings_getint.restype = c_int

        # new_fluid_audio_driver(settings, synth)
        F.new_fluid_audio_driver.argtypes = [c_void_p, c_void_p]
        F.new_fluid_audio_driver.restype = c_void_p

        # --- synth ---
        # new_fluid_synth(settings)
        F.new_fluid_synth.argtypes = [c_void_p]
        F.new_fluid_synth.restype = c_void_p

        # fluid_synth_sfload(synth, filename, update)
        F.fluid_synth_sfload.argtypes = [c_void_p, c_char_p, c_int]
        F.fluid_synth_sfload.restype = c_int

        F.fluid_synth_sfunload.argtypes = [c_void_p, c_int, c_int]
        F.fluid_synth_sfunload.restype = c_int

        F.fluid_synth_program_select.argtypes = [c_void_p, c_int, c_int, c_int, c_int]
        F.fluid_synth_program_select.restype = c_int

        F.fluid_synth_set_reverb.argtypes = [c_void_p, c_double, c_double, c_double, c_double]
        F.fluid_synth_set_reverb.restype = c_int

        F.fluid_synth_set_chorus.argtypes = [c_void_p, c_int, c_double, c_double, c_double, c_int]
        F.fluid_synth_set_chorus.restype = c_int

        F.fluid_synth_cc.argtypes = [c_void_p, c_int, c_int, c_int]
        F.fluid_synth_cc.restype = c_int

        F.fluid_synth_count_midi_channels.argtypes = [c_void_p]
        F.fluid_synth_count_midi_channels.restype = c_int

        # fluid_synth_all_notes_off(synth, chan)
        F.fluid_synth_all_notes_off.argtypes = [c_void_p, c_int]
        F.fluid_synth_all_notes_off.restype = c_int
        
        F.fluid_synth_system_reset.argtypes = [c_void_p]
        F.fluid_synth_system_reset.restype = c_int

        # --- player ---
        # new_fluid_player(synth)
        F.new_fluid_player.argtypes = [c_void_p]
        F.new_fluid_player.restype = c_void_p

        # fluid_player_add(player, filename)
        F.fluid_player_add.argtypes = [c_void_p, c_char_p]
        F.fluid_player_add.restype = c_int

        # fluid_player_play(player)
        F.fluid_player_play.argtypes = [c_void_p]
        F.fluid_player_play.restype = c_int

        # fluid_player_seek(player, ticks)
        F.fluid_player_seek.argtypes = [c_void_p, c_int]
        F.fluid_player_seek.restype = c_int

        F.fluid_player_stop.argtypes = [c_void_p]
        F.fluid_player_stop.restype = c_int

        F.fluid_player_join.argtypes = [c_void_p]
        F.fluid_player_join.restype = c_int

        F.fluid_player_get_status.argtypes = [c_void_p]
        F.fluid_player_get_status.restype = c_int

        # fluid_player_get_current_tick(player)
        F.fluid_player_get_current_tick.argtypes = [c_void_p]
        F.fluid_player_get_current_tick.restype = c_int

        F.fluid_player_get_total_ticks.argtypes = [c_void_p]
        F.fluid_player_get_total_ticks.restype = c_int

        # --- file renderer ---
        F.new_fluid_file_renderer.argtypes = [c_void_p]
        F.new_fluid_file_renderer.restype = c_void_p  # tu avais déjà restype

        F.fluid_file_set_encoding_quality.argtypes = [c_void_p, c_double]
        F.fluid_file_set_encoding_quality.restype = c_int

        F.fluid_file_renderer_process_block.argtypes = [c_void_p]
        F.fluid_file_renderer_process_block.restype = c_int  # déjà restype

        F.delete_fluid_file_renderer.argtypes = [c_void_p]
        F.delete_fluid_file_renderer.restype = None

        # --- delete functions ---
        F.delete_fluid_audio_driver.argtypes = [c_void_p]
        F.delete_fluid_audio_driver.restype = None

        F.delete_fluid_synth.argtypes = [c_void_p]
        F.delete_fluid_synth.restype = None

        F.delete_fluid_settings.argtypes = [c_void_p]
        F.delete_fluid_settings.restype = None

        F.delete_fluid_player.argtypes = [c_void_p]
        F.delete_fluid_player.restype = None
        return F
    except Exception as e:
        raise ImportError(f"Error while loading FluidSynth: {e}")

class FluidSynthPlayer(MidiPlayer):
    def __init__(self, prefs):
        super(FluidSynthPlayer, self).__init__()
        self.prefs = prefs
        self.library_path = prefs["fluidsynth_library_path"]
        self.soundfont_path = prefs["soundfont_path"]

        logger.debug("[FluidSynthPlayer] load fluidsynth library…")
        self._load_library()
        logger.debug("[FluidSynthPlayer] create Synth…")
        self._create_synth()
        logger.debug("[FluidSynthPlayer] load soundfont…")
        self._load_soundfont()
        logger.debug("[FluidSynthPlayer] apply options…")
        self._apply_options()
        logger.debug("[FluidSynthPlayer] create player…")
        self._create_player()
        self._initialize_status()
        logger.debug("[FluidSynthPlayer] FluidSynthPlayer init OK")

    @property
    def player_type(self):
        return "fluidsynth"
    
    def set_soundfont(self, sf2_path, load_on_play=False):         # load another sound font
        if self.is_playing or load_on_play:
            self.pending_soundfont = sf2_path
        else:
            self.soundfont_path = sf2_path
            if self.sfid >= 0:
                self.fs.sfunload(self.sfid, 1)
            self.sfid = self.fs.sfload(sf2_path)
            if self.sfid < 0:
                return 0     # not a sf2 file
            self.fs.program_select(0, self.sfid, 0, 0)
            return 1

    def load(self, path):          # load a midi file
        self.reset()              # reset the player, empty the playlist
        self.pause_time = 0       # resume playing at time == 0
        if os.path.exists(path):
            #path = str(path)
            success = self.p.add(path)           # add file to playlist
            return True
        return False

    def reset(self):              # the only way to empty the playlist ...
        self.p.delete()           # delete player
        self.F.fluid_synth_system_reset(self.fs.synth)
        self.p = Player(self.F, self.fs)   # make a new one
        #self.set_loop_midi_playback(self.loop_midi_playback)

    def play(self):
        if self.is_playing:
            return
        if self.pending_soundfont:
            if self.pending_soundfont != self.soundfont_path and os.path.exists(self.pending_soundfont):
                self.set_soundfont(self.pending_soundfont)
            self.pending_soundfont = None

        self.p.play(self.pause_time)
        self.pause_time = 0
        self.duration_in_ticks = self.p.get_length()

    def pause(self):
        if self.is_playing:
            self.pause_time = self.p.stop()

    def stop(self):
        if self.is_playing:
            self.p.stop()
        self.pause_time = 0

    def seek(self, time):         # go to time (in midi ticks)
        if time > self.duration_in_ticks or time < 0:
            return
        ticks = self.p.seek(time)
        self.pause_time = time
        return ticks

    def tell(self):
        ticks = self.p.get_ticks() # get play position in midi ticks
        return ticks

    def render_to_file(self, midi_path, output_path):
        fs = Synth(self.F, gain=1.0, bsize=2048)
        soundfont_path = self.pending_soundfont
        if not soundfont_path:
            soundfont_path = self.soundfont_path
        sfid = fs.sfload(soundfont_path)
        if sfid < 0:
            return 0     # not a sf2 file
        fs.program_select(0, sfid, 0, 0)
        player = Player(self.F, fs)   # make a new one
        #midi_path = str(midi_path)
        player.add(midi_path)
        player.play()
        sfnm = str(output_path)
        player.set_render_mode (sfnm, 'oga')  # vorbis file with name sfnm
        samples = player.renderLoop()
        logger.debug(samples)
        player.delete()
        fs.delete()

    def dispose(self):             # free some memory
        self.p.delete()
        self.fs.delete()

    @property
    def is_playing(self):
        return self.p.get_status() == 1 and not self.is_paused  # 0 = ready, 1 = playing, 2 = finished

    @property
    def is_finished(self):
        return self.p.get_status() == 2  # 0 = ready, 1 = playing, 2 = finished

    @property
    def is_paused(self):
        return self.pause_time > 0

    def set_gain(self, gain):  # gain between 0.0 and 1.0
        self.p.set_gain(gain)

    def length(self):
        self.duration_in_ticks = self.p.get_length()
        return self.duration_in_ticks

    @property
    def unit_is_midi_tick(self):
        return True

    @property
    def loop_midi_playback(self):
        return self._loop_midi_playback

    def set_loop_midi_playback(self, value):
        self._loop_midi_playback = value
        if value:
            self.p.set_loop()
        elif self.is_playing:
            self.p.set_loop(0)
        else:
            self.p.set_loop(1)

    def idle(self):
        pass

    def apply_preferences(self, prefs):
        """
        Update player configuration based on new preferences.
        Recreate synth only if library changed.
        """
        lib_changed = prefs["fluidsynth_library_path"] != self.library_path

        self.prefs = prefs

        if lib_changed:
            self._recreate_full_engine()
            return

        sf2_changed = prefs["soundfont_path"] != self.soundfont_path
        if sf2_changed:
            self._reload_soundfont()

        self._apply_options()
        self.reset()

    def _load_library(self):
        self.F = load_fluidsynth_from_path(self.library_path)

    def _create_synth(self):
        self.fs = Synth(self.F, gain=1.0, bsize=2048)
        driver = None
        if sys.platform.startswith('linux'):
            driver = 'pulseaudio'
        if sys.platform == "darwin":
            driver = 'coreaudio'
        elif sys.platform.startswith("win"):
            driver = 'dsound'
        logger.debug("[FluidSynthPlayer] Synth.start()…")
        self.fs.start(driver)  # set default output driver and start clock

    def _load_soundfont(self):
        self.sfid = self.fs.sfload(self.soundfont_path)
        logger.debug("FS: program_select()…")
        self.fs.program_select(0, self.sfid, 0, 0)

    def _create_player(self):
            self.p = Player(self.F, self.fs)   # make a new player

    def _initialize_status(self):
        self.duration_in_ticks = 0   # length of midi file
        self.pause_time = 0        # time in midi ticks where player stopped
        self.pending_soundfont = None
        self._loop_midi_playback = 0

    def _recreate_full_engine(self):
        self.library_path = self.prefs["fluidsynth_library_path"]
        self.soundfont_path = self.prefs["soundfont_path"]

        self._load_library()
        self._create_synth()
        self._load_soundfont()
        self._apply_options()
        self.reset()
        self._initialize_status()

    def _reload_soundfont(self):
        self.soundfont_path = self.prefs["soundfont_path"]
        self.fs.sfunload(self.sfid, 1)
        self.sfid = self.fs.sfload(self.soundfont_path)

    def _apply_options(self):
        # Example future options
        gain = self.prefs["fluidsynth_gain"] #default 1.0
        self.fs.set_gain(gain)

        # Reverb
        room = self.prefs["fluidsynth_reverb_room"] #default 0.2
        damp = self.prefs["fluidsynth_reverb_damp"] #default 0.0
        width = self.prefs["fluidsynth_reverb_width"] #default 0.5
        level = self.prefs["fluidsynth_reverb_level"] #default 0.9
        self.fs.set_reverb(room, damp, width, level)

        # Chorus
        nr = self.prefs["fluidsynth_chorus_nr"] #default 3
        level = self.prefs["fluidsynth_chorus_level"] #default 1.2
        speed = self.prefs["fluidsynth_chorus_speed"] #default 0.3
        depth = self.prefs["fluidsynth_chorus_depth"] #default 8.0
        typ = self.prefs["fluidsynth_chorus_type"] #default 0
        self.fs.set_chorus(nr, level, speed, depth, typ)
