# easyabc2/engines/midi/fluidsynth.py

"""
FluidSynth wrapper for EasyABC2.
Based on the original Python bindings by Willem Vree (LGPL),
adapted and simplified for EasyABC2.

Original reference:
third_party/fluidsynth/fluidsynth.py
"""
from ctypes import c_double, c_int, c_char_p, byref
import time

from easyabc2.utils.logging_utils import logger

logger.debug("[FluidSynth] Importing…")

revModels = ['Model 1','Model 2', 'Model 3','Model 4','Model 5']
# room size (0.0-1.2), damping (0.0-1.0), width (0.0-100.0), level (0.0-1.0)
revmods = { revModels [0]: (0.2, 0.0, 0.5, 0.9), revModels [1]: (0.4, 0.2, 0.5, 0.8),
            revModels [2]: (0.6, 0.4, 0.5, 0.7), revModels [3]: (0.8, 0.7, 0.5, 0.6),
            revModels [4]: (0.8, 0.0, 0.5, 0.5)}

# Modernized version of bs() from Willem Vree's original wrapper.
# Accepts Path, str, and converts everything to UTF‑8 bytes.
def bs (reeks):
    #return reeks.encode ('utf-8') if python3 or type (reeks) == unicode else reeks
    return str(reeks).encode("utf-8")

class Synth:            # interface for the FluidSynth synthesizer
    def __init__(self, F, gain=0.2, samplerate=44100, bsize=64):
        self.F = F
        print("FS: Synth.new_fluid_settings()…")
        #st = getFnObj ('new_fluid_settings')
        st = self.F.new_fluid_settings()
        print("FS: Synth.new_fluid_settings_setnum1()…")
        self.F.fluid_settings_setnum (st, b"synth.gain", c_double (gain))
        print("FS: Synth.new_fluid_settings_setnum2()…")
        self.F.fluid_settings_setnum (st, b"synth.sample-rate", c_double (samplerate))
        print("FS: Synth.new_fluid_settings_setint1()…")
        self.F.fluid_settings_setint (st, b"audio.period-size", bsize)
        print("FS: Synth.new_fluid_settings_setint2()…")
        self.F.fluid_settings_setint (st, b"audio.periods", 2)
        self.settings = st
        #self.synth = getFnObj ('new_fluid_synth', st)
        print("FS: Synth.new_fluid_synth()…")
        self.synth = self.F.new_fluid_synth(st)
        self.audio_driver = None

    def start (self, driver=None):   # initialize the audio driver
        if driver is not None:
            assert (driver in ['alsa', 'oss', 'jack', 'portaudio', 'sndmgr', 'coreaudio', 'dsound', 'pulseaudio']) 
            self.F.fluid_settings_setstr (self.settings, b"audio.driver", driver.encode())
        #self.audio_driver = getFnObj ('new_fluid_audio_driver', self.settings, self.synth)
        self.audio_driver = self.F.new_fluid_audio_driver(self.settings, self.synth)
        if not self.audio_driver:   # API returns 0 on error (not None)
            self.audio_driver = None
        else:   # print some info
            psize = c_int ()    # integer for parameter passing by reference
            self.F.fluid_settings_getint (self.settings, b"audio.period-size", byref (psize))
            nper = c_int ()
            self.F.fluid_settings_getint (self.settings, b"audio.periods", byref (nper))
            logger.info(f"[FluidSynth] audio.period-size: {psize.value}, audio.periods: {nper.value}, latency: {nper.value * psize.value * 1000 / 44100}msec")

    def delete (self):              # release all memory
        if self.audio_driver is not None:
            self.F.delete_fluid_audio_driver (self.audio_driver)
        self.F.delete_fluid_synth (self.synth)
        self.F.delete_fluid_settings (self.settings)
        self.settings = self.synth = self.audio_driver = None

    def sfload (self, filename, update_midi_preset=0):  # load soundfont
        return self.F.fluid_synth_sfload (self.synth, bs(filename), update_midi_preset)

    def sfunload (self, sfid, update_midi_preset=0):    # clear soundfont
        return self.F.fluid_synth_sfunload (self.synth, sfid, update_midi_preset)

    def program_select (self, chan, sfid, bank, preset):
        return self.F.fluid_synth_program_select (self.synth, chan, sfid, bank, preset)

    def set_reverb (self, roomsize, damping, width, level):     # change reverb model parameters
        return self.F.fluid_synth_set_reverb (self.synth, c_double (roomsize), c_double (damping), c_double (width), c_double (level))

    def set_chorus (self, nr, level, speed, depth_ms, type):    # change chorus model pararmeters
        return self.F.fluid_synth_set_chorus (self.synth, nr, c_double (level), c_double (speed), c_double (depth_ms), type)

    def set_reverb_level (self, level):                     # set the amount of reverb (0-127) on all midi channels
        n = self.F.fluid_synth_count_midi_channels (self.synth)
        for chan in range (n):
            self.F.fluid_synth_cc (self.synth, chan, 91, level); # midi control change #91 == reverb level

    def set_chorus_level (self, level):                     # set the amount of chorus (0-127) on all midi channels
        n = self.F.fluid_synth_count_midi_channels (self.synth)
        for chan in range (n):
            self.F.fluid_synth_cc (self.synth, chan, 93, level); # midi control change #93 == chorus level

    def set_gain (self, gain):
        self.F.fluid_settings_setnum (self.settings, b"synth.gain", c_double (gain))

    def set_buffer (self, size=0, driver=None):
        if self.audio_driver is not None:   # remove current audio driver
            self.F.delete_fluid_audio_driver (self.audio_driver)
        if size:
            self.F.fluid_settings_setint (self.settings, b"audio.period-size", size)
        self.start (driver)   # create new driver


class Player:               # interface for the FluidSynth internal midi player
    LOOP_INFINITELY = -1

    def __init__ (self, F, flsynth):
        self.F = F
        self.flsynth = flsynth # an instance of class Synth
        self.player = self.F.new_fluid_player(self.flsynth.synth)

    def add (self, midifile):  # add midifile to the playlist
        self.F.fluid_player_add (self.player, bs (midifile))

    def play (self, offset=0): # start playing at time == offset in midi ticks
        ticks = self.seek (offset);
        self.F.fluid_player_play (self.player)

    def stop (self):           # stop playing and return position in midi ticks
        self.F.fluid_player_stop (self.player)
        self.F.fluid_synth_all_notes_off (self.flsynth.synth, -1)   # -1 == all channels
        return self.get_ticks ()

    def wait (self):           # wait until player is finished
        self.F.fluid_player_join (self.player)

    def get_status (self):     # 1 == playing, 2 == player finished 
        return self.F.fluid_player_get_status (self.player)

    def get_ticks (self):      # get current position in midi ticks
        t = self.F.fluid_player_get_current_tick (self.player)
        return t

    def seek (self, ticks_p):  # go to position ticks_p (in midi ticks)
        self.F.fluid_synth_all_notes_off (self.flsynth.synth, -1)   # -1 == all channels
        self.F.fluid_player_seek (self.player, ticks_p);
        return self.get_ticks ()

    def seekW (self, ticks_p): # go to position ticks_p (in midi ticks) and wait until seeked
        self.F.fluid_synth_all_notes_off (self.flsynth.synth, -1)   # -1 == all channels
        ticks = self.F.fluid_player_seek (self.player, ticks_p)
        n = 0
        while abs (ticks - ticks_p) > 10 and n < 100:
            time.sleep (0.01)
            ticks = self.get_ticks ()
            n += 1          # time out after 1 sec
        return ticks

    def get_length (self):  # get duration of a midi track in ticks
        return self.F.fluid_player_get_total_ticks (self.player)

    def delete (self):
        self.F.delete_fluid_player (self.player)

    def renderLoop (self, quality = 0.5, callback=None):       # render midi file to audio file
        #renderer = getFnObj ('new_fluid_file_renderer', s.flsynth.synth)
        renderer = self.F.new_fluid_file_renderer(self.flsynth.synth)
        if not renderer:
            logger.error('[FluidSynth] failed to create file renderer')
            return
        self.F.fluid_file_set_encoding_quality (renderer, c_double (quality))
        k = c_int()         # get block size (samples are rendered one block at a time)
        self.F.fluid_settings_getint (self.flsynth.settings, b"audio.period-size", byref (k))
        n = 0               # sample counter
        while self.get_status () == 1:
            if self.F.fluid_file_renderer_process_block (renderer) != 0: # render one block
                logger.error('[FluidSynth] renderer_loop error')
                break
            n += k.value    # increment with block size
            if callback: callback (n)   # for progress reporting
        self.F.delete_fluid_file_renderer (renderer)
        return n

    def set_render_mode (self, file_name, file_type):  # set audio file and audio type
        st = self.flsynth.settings                     # should be called before the renderLoop
        self.F.fluid_settings_setstr (st, b"audio.file.name", bs (file_name))
        self.F.fluid_settings_setstr (st, b"audio.file.type", bs (file_type))
        self.F.fluid_settings_setstr (st, b"player.timing-source", b"sample");
        self.F.fluid_settings_setint (st, b"synth.parallel-render", 1)

    def set_reverb (self, name):   # change reverb model parameters
        roomsize, damp, width, level = revmods.get (name, revmods [name])
        self.flsynth.set_reverb (roomsize, damp, width, level)

    def set_chorus (self, nr, level, speed, depth_ms, type):    # change chorus model pararmeters
        self.flsynth.set_chorus (nr, level, speed, depth_ms, type)

    def set_reverb_level (self, newlev): # set reverb level 0-127 on all midi channels
        self.flsynth.set_reverb_level (newlev)

    def set_chorus_level (self, newlev): # set chorus level 0-127 on all midi channels
        self.flsynth.set_chorus_level (newlev)

    def set_gain (self, gain): # set master volume 0-10
        self.flsynth.set_gain (gain)

    def set_loop(s, loops = LOOP_INFINITELY):
        F.fluid_player_set_loop(s.player, loops)
