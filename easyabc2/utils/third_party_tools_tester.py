# easyabc2/utils/third_party_tools_tester.py

import os
from easyabc2.utils.easyabc_utils import run_process
from easyabc2.engines.midi.fluidsynthplayer import load_fluidsynth_from_path
from easyabc2 import _

def test_abc2midi(path):
    if not path:
        return False, _("No path configured")
    if not os.path.exists(path):
        return False, _("Path does not exist")

    stdout, stderr, code = run_process([path, "-ver"])
    if code == 0:
        version = _short(stdout.strip()) or _("OK")
        return True, _("abc2midi OK — version: ") + version
    return False, _("abc2midi failed: ") + _short(stderr.strip() or _("Unknown error"))

def test_midi2abc(path):
    if not path:
        return False, _("No path configured")
    if not os.path.exists(path):
        return False, _("Path does not exist")

    stdout, stderr, code = run_process([path, "-ver"])
    if code == 0:
        version = _short(stdout.strip()) or _("OK")
        return True, _("midi2abc OK — version: ") + version
    return False, _("midi2abc failed: ") + _short(stderr.strip() or _("Unknown error"))

def test_abc2svg_scripts(path):
    if not path:
        return False, _("No directory configured")
    if not os.path.isdir(path):
        return False, _("Directory does not exist")

    required = ["abc2svg-1.js"]
    for r in required:
        if not os.path.exists(os.path.join(path, r)):
            return False, _("Missing script: ") + r

    return True, _("abc2svg scripts OK")

def test_xml2abc(path):
    if not path:
        return False, _("No path configured")
    if not os.path.exists(path):
        return False, _("Path does not exist")

    stdout, stderr, code = run_process(["python3", path, "--version"])
    if code == 0:
        version = _short(stdout.strip()) or _("OK")
        return True, _("xml2abc OK — version: ") + version

    return False, _("xml2abc failed: ") + _short(stderr.strip() or _("Unknown error"))

def test_abc2xml(path):
    if not path:
        return False, _("No path configured")
    if not os.path.exists(path):
        return False, _("Path does not exist")

    stdout, stderr, code = run_process(["python3", path, "--version"])
    if code == 0:
        version = _short(stdout.strip()) or _("OK")
        return True, _("abc2xml OK — version: ") + version

    return False, _("abc2xml failed: ") + _short(stderr.strip() or _("Unknown error"))

def test_fluidsynth_library(path):
    if not path:
        return False, _("No library configured")
    if not os.path.exists(path):
        return False, _("Invalid path")

    try:
        F = load_fluidsynth_from_path(path)
        from ctypes import c_int, byref
        x, y, z = c_int(), c_int(), c_int()
        try:
            F.fluid_version(byref(x), byref(y), byref(z))
            version = f"{x.value}.{y.value}.{z.value}"
            return True, _("OK — FluidSynth version: ") + version
        except:
            return True, _("Library loaded, but version unknown")

    except Exception as e:
        return False, _("Found library but cannot load: ") + _short(str(e))

def test_soundfont(path, fluidsynth_lib):
    if not path:
        return False, _("No SoundFont configured")
    if not os.path.exists(path):
        return False, _("SoundFont file does not exist")

    try:
        F = load_fluidsynth_from_path(fluidsynth_lib)

        from ctypes import c_int, c_void_p, c_char_p

        settings = F.new_fluid_settings()
        synth = F.new_fluid_synth(settings)

        sfid = F.fluid_synth_sfload(synth, path.encode(), 1)
        if sfid < 0:
            return False, _("Cannot load SoundFont")

        return True, _("SoundFont OK")

    except Exception as e:
        return False, _("Error while testing SoundFont: ") + _short(str(e))

def _short(msg, limit=30):
    msg = msg.strip().replace("\n", " ")
    return msg if len(msg) <= limit else msg[:limit] + "…"
