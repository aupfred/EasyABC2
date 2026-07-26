# easyabc2/engines/engine_manager.py

from easyabc2.engines.abc2svg_engine import ABC2SVGEngine
from easyabc2.engines.abc2midi_engine import Abc2MidiEngine
#from easyabc2.engines.xml2abc_engine import XML2ABCEngine
#from easyabc2.engines.abc2xml_engine import ABC2XMLEngine
from easyabc2.engines.midi import create_midi_player

class EngineManager:
    #def __init__(self, app_data_dir, prefs):
    def __init__(self, prefs):
        #self.prefs = prefs
        #self.app_data_dir = app_data_dir

        self.abc2svg = ABC2SVGEngine(prefs)
        self.abc2midi = Abc2MidiEngine(prefs)
        #self.xml2abc = XML2ABCEngine(prefs)
        #self.abc2xml = ABC2XMLEngine(prefs)
        
        self.midi_player = create_midi_player(prefs)

    def new_abc2svg_prefs(self, prefs):
        self.abc2svg = ABC2SVGEngine(prefs)

    def new_abc2midi_tools_prefs(self, prefs):
        self.abc2midi = Abc2MidiEngine(prefs)

    def new_midi_player_prefs(self, prefs):
        if prefs["midi_engine"] =="fluidsynth" and self.midi_player.player_type == "fluidsynth":
            try:
                self.midi_player.apply_preferences(prefs)
                return
            except Exception:
                pass

        self.midi_player = create_midi_player(prefs)
    
    def apply_preferences(self, prefs):
        self.prefs = prefs
        
        ## 1) ABC2SVGEngine: rebuild if new path
        #if prefs["abc2svg_scripts_path"] != self.abc2svg.preferences["abc2svg_scripts_path"]:
        #    self.abc2svg = ABC2SVGEngine(prefs)
#
        ## 2) abc2midi: no need to rebuild for new path, to be checked for options
        ## 3) xml2abc: no need to rebuild for new path, to be checked for options
        ## 4) abc2xml: no need to rebuild for new path, to be checked for options
        ## 5) MIDIPlayer : rebuild if new soundfont
        ##self.midi_player.apply_preferences(prefs)
        #engine_changed = prefs["midi_engine"] != self.midi_player.player_type
#
        #if engine_changed:
        #    self.midi_player = create_midi_player(prefs)
        #    return
#
        #if self.midi_player.player_type == "fluidsynth":
        #    try:
        #        self.midi_player.apply_preferences(prefs)
        #    except Exception:
        #        self.midi_player = create_midi_player(prefs)
        #    return
#
        #if self.midi_player.player_type == "mplay":
        #    self.midi_player = create_midi_player(prefs)
        #    return
#
        #self.midi_player = create_midi_player(prefs)

