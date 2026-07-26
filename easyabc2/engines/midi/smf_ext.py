# easyabc2/engines/midi/smf_ext.py

# Added to extend SMF provided by mplay
# Objective is to manage the change of tempo while playing

import sys
from time import time, sleep

import easyabc2.third_party.mplay.darwinmidi as darwinmidi
# Inject module in sys.modules to satisfy smf.py
sys.modules['darwinmidi'] = darwinmidi
from easyabc2.third_party.mplay.smf import SMF as SMFBase
from easyabc2.third_party.mplay.smf import instruments, families, drum_instruments, keys, modes, notes, chords, messages, meta

class SMFExt(SMFBase):
    def __init__(self):
        super().__init__()
        self.multibpm = 1.0

    def getsongposition(self):
        if self.pause != 0:
            now = (self.pause - self.elapsed_time) * 1000
        else:
            now = (time() - self.elapsed_time) * 1000
        return int(now * self.division * 1000 / self.tempo)

    def gotosongposition(self, song_position):
        #Need to turn off all currently note played otherwise will keep sounding
        for ch in range(16):
            self.allnotesoff(ch)
        self.songposition(song_position)
        if self.pause != 0:
            self.pause = time()

    def setsong(self, **info):
        if "multibpm" in info:
            new_multi = info["multibpm"]
            self.bpm = self.bpm * new_multi / self.multibpm
            self.multibpm = new_multi

            now = time()
            old_tempo = self.tempo
            self.tempo = 60000000 / self.bpm
            self.elapsed_time = now - (now - self.elapsed_time) * self.tempo / old_tempo
            return
        if 'goto' in info:
            self.gotosongposition(info['goto']/self.division)
            return
        if 'bar' in info:
            now = (time() - self.elapsed_time) * 1000
            beat = int(now * 1000 / self.tempo)
            beat += 4 * info['bar'] - (beat % 4)
            self.gotosongposition(beat)
            return

        return super().setsong(**info)

    def play(self, dev, wait=True):
        if not self.start:
            self.device = dev
            self.device.mididataset1(0x40007f, 0x00)
            sleep(0.04)
            self.start = time()
            self.writemidi([0xfc, 0xfa])
            self.elapsed_time = self.start
            self.line = ''
        if self.pause != 0:
            return 0.04
        for ev in self.ev[self.next:]:
            (at, message, byte1, byte2) = ev
            now = time() - self.elapsed_time
            while at > now * self.division * 1000000 / self.tempo:
                self.timing(at)
                delta = (at - now * self.division * 1000000 / self.tempo) / \
                    1000
                delta = min(delta, 1.0 / (self.division / 24))
                if wait:
                    sleep(delta)
                    now = time() - self.elapsed_time
                else:
                    return delta
            self.timing(at)
            if message == 0xff:
                (at, message, me_type, data) = ev
                if me_type == 0x05:
                    if data[0] in [13, 10]:
                        self.line = ''
                    else:
                        if data[-1] in [13, 10]:
                            self.text = self.line + printable(data[:-1])
                            self.line = ''
                        else:
                            self.line += printable(data)
                            self.text = self.line
                elif me_type == 0x51:
                    now = time()
                    tempo = self.tempo
                    self.tempo = (data[0] << 16) | (data[1] << 8) | data[2]
                    self.tempo = self.tempo / self.multibpm
                    self.bpm = 60000000 / self.tempo * self.denominator / 4
                    self.elapsed_time = now - (now - self.elapsed_time) * \
                        self.tempo / tempo
                elif me_type == 0x58:
                    self.numerator = data[0]
                    self.denominator = 1 << data[1]
                    self.clocks_per_beat = data[2]
                    self.notes_per_quarter = data[3]
                elif me_type == 0x59:
                    self.key = data[0]
                    self.mode = data[1]
                    if self.key < -7 or self.key > 8:
                        self.key = 8
                    if self.mode < 0 or self.mode > 2:
                        self.mode = 2
            else:
                me_type = message & 0xf0
                channel = message & 0x0f
                info = self.channel[channel]
                info['used'] = True
                if me_type in [0x80, 0x90] and channel != 9:
                    byte1 += self.key_shift
                if me_type == 0x80:
                    if byte1 in info['notes']:
                        info['notes'].remove(byte1)
                    info['velocity'] = 0
                elif me_type == 0x90:
                    if byte2 != 0:
                        if byte1 in info['notes']:
                            print('Note retriggered')
                        else:
                            info['notes'].append(byte1)
                        if not info['muted']:
                            info['intensity'] = byte2
                    elif byte1 in info['notes']:
                        info['notes'].remove(byte1)
                    info['velocity'] = byte2
                elif me_type == 0xb0:
                    if byte1 == 0:
                        info['variation'] = byte2
                    elif byte1 == 32:
                        byte2 = 2
                    elif byte1 == 7:
                        info['level'] = byte2
                    elif byte1 == 10:
                        info['pan'] = byte2
                    elif byte1 == 91:
                        info['reverb'] = byte2
                    elif byte1 == 93:
                        info['chorus'] = byte2
                    elif byte1 == 94:
                        info['delay'] = byte2
                elif me_type == 0xc0:
                    info['name'] = instruments[byte1]
                    info['instrument'] = byte1
                    info['family'] = families[byte1 // 8]
                if not info['muted']:
                    if me_type != 0xc0:
                        self.writemidi([message, byte1, byte2])
                    else:
                        self.writemidi([message, byte1])
            self.next += 1
        self.writemidi([0xfc])
        return 0
