'''
    A simple midi player with Tkinter for FluidSynth
    Released under the LGPL
    Copyright 2012-2021, Willem Vree
'''
import time, os, sys
import fluidsynth as F
python3 = sys.version_info [0] > 2
if python3:
    import tkinter as T
    import tkinter.filedialog as TF
else:
    import Tkinter as T
    import tkFileDialog as TF

VERSION = 15

class TestPlayer:
    def __init__ (s):
        s.blen = 1024 if F.onLinux else 4096
        s.fs = F.Synth (bsize=s.blen) # make a synth
        s.driver_name = F.onLinux and 'pulseaudio' or 'dsound'
        s.fs.start (s.driver_name)  # set default output driver and start clock
        s.sf2 = 'example.sf2'       # set default soundfont
        s.sfid = s.fs.sfload (s.sf2)
        s.fs.program_select (0, s.sfid, 0, 0)
        s.p = F.Player (s.fs)   # make a new player
        s.fnm = ''              # current midi file
        s.dur = 0               # lenght of midi file
        s.playing = 0
        s.pause_time = 0        # time in midi tickst where player stopped
        s.set_gain (0.6)
    
    def setSf (s, fnm):         # load another sound font
        s.sf2 = fnm
        if s.sfid >= 0:
            s.fs.sfunload (s.sfid)
        s.sfid = s.fs.sfload (fnm)
        if s.sfid < 0: return 0     # not a sf2 file
        s.fs.program_select (0, s.sfid, 0, 0)
        s.pause_time  = 0       # resume playing at time == 0
        return 1

    def load (s, fnm):          # load a midi file
        s.reset ()              # reset the player, empty the playlist
        s.pause_time  = 0       # resume playing at time == 0
        s.p.add (fnm)           # add file to playlist

        # we need to trigger loading of the midifile just added, by playing it.
        old_gain = float (gn.get ())
        s.set_gain (0)          # mute before playing
        s.p.play ()
        time.sleep (0.1)        # sufficient for getting the midi file loaded
        s.p.stop ()
        s.p.seekW (0)           # back to the beginning
        s.set_gain (old_gain)   # put the volume back
        #~ print ('lengte', s.p.get_length (), 'status', s.p.get_status ())

        s.dur = s.p.get_length ()
        s.fnm = '' if s.dur == 0 else fnm
        return s.fnm

    def reset (s):              # the only way to empty the playlist ...
        s.p.delete ()           # delete player
        s.p = F.Player (s.fs)   # make a new one

    def play (s):
        if s.playing:
            s.pause_time = s.p.stop ()
            s.playing = 0
        else:
            s.p.play (s.pause_time)
            s.playing = 1

    def goto (s, time):         # go to time (in midi ticks)
        if time > s.dur or time < 0: return
        ticks = s.p.seek (time)
        s.pause_time = time
        return ticks

    def time (s):               # get play position in midi ticks
        return s.p.get_ticks ()

    def delete (s):             # free some memory
        s.p.delete ()
        s.fs.delete()

    def save (s, sfnm, qual, callback=None):
        fs = F.Synth (bsize=8192)   # init new fluidsynth, set buffersize to maximum (latency is no issue here)
        sfid = fs.sfload (s.sf2)    # load the sound font
        p = F.Player (fs)           # init new midi player
        p.add (s.fnm)               # add midi file to playlist
        p.set_gain (s.gain)         # use same gain as with audio playback
        p.play ()                   # set ready for playing midi file (without advancing time yet)
        p.set_render_mode (sfnm, 'oga')  # vorbis file with name sfnm
        ns = p.renderLoop (quality=qual, callback=callback)
        p.delete ()                 # free allocated stuff
        fs.delete ()
        return ns

    def status (s):             # 0 = ready, 1 = playing, 2 = finished
        return s.p.get_status ()

    def set_gain (s, gain):
        s.gain = gain
        s.p.set_gain (gain)

def setfont ():
    nm = TF.askopenfilename ()
    if not nm: return
    nm = os.path.relpath (nm)
    if player.setSf (nm):
        sf.set (nm)
        stat.set ('')
    else:
        stat.set ('loading %s as soundfont failed' % nm)
        sf.set ('---')

def setmidi ():
    nm = TF.askopenfilename ()
    if not nm: return
    nm = os.path.relpath (nm)
    if not nm: return
    nm2 = player.load (nm)
    if nm2:
        mf.set (nm2)
        tm.set (str (player.dur))
        stat.set ('')
    else:
        mf.set ('---')
        stat.set ('file %s is not a midi file' % nm)

def play ():
    player.play ()
    if player.playing:
        btxt = 'stop'
    else:
        btxt = 'play'
    play_btn.configure (text=btxt)

def progress ():
    if player.status () == 2 and player.playing:
        play ()              # stop
        player.load (player.fnm)    # rewind == reload
        goto ()
    if mf.get () == '---':
        play_btn.configure (state=T.DISABLED)
        prgr_btn.configure (state=T.DISABLED)
        sv_btn.configure  (state=T.DISABLED)
    else:
        play_btn.configure (state=T.NORMAL)
        prgr_btn.configure (state=T.NORMAL)
        if player.playing:
            sf_btn.configure (state=T.DISABLED)
            mf_btn.configure (state=T.DISABLED)
            sv_btn.configure (state=T.DISABLED)
            prgr.set (str (player.time ()))
        else:
            sf_btn.configure (state=T.NORMAL)
            mf_btn.configure (state=T.NORMAL)        
            sv_btn.configure  (state=T.NORMAL)
    root.after (200, progress)

def goto ():
    try:
        pos = int (prgr_en.get ())
        if pos < 0 or pos >= player.dur:
            raise Exception ('not a valid time')
        stat.set ('')
    except Exception as err:
        stat.set (err)
        return
    player.goto (pos)
    prgr.set (str (pos))

def save_progress (n):
    stat.set ('%d samples' % n)
    root.update_idletasks ()

def save ():
    try:
        qual = float (qv.get ())
        if qual < 0 or qual > 1:
            raise Exception ('0.0 <= quality <= 1.0')
    except Exception as err:
        stat.set (err)
        return
    fnm = TF.asksaveasfilename (defaultextension='.ogg', filetypes=[('vorbis', '*.ogg')], title='select save file name')
    if not fnm: return
    play_btn.configure (state=T.DISABLED)
    prgr_btn.configure (state=T.DISABLED)
    sv_btn.configure  (state=T.DISABLED)
    sf_btn.configure (state=T.DISABLED)
    mf_btn.configure (state=T.DISABLED)
    n = player.save (fnm, qual, save_progress)
    stat.set ('%d samples = %.1f secs of music' % (n, float (n) / 44100))

def reverb_level ():
    try:
        lev = int (rev.get ())
        if lev < 0 or lev > 127:
            raise Exception ('0 <= level <= 127')
        stat.set ('')
    except Exception as err:
        stat.set (err)
        return
    player.p.set_reverb_level (lev)

def chorus_level ():
    try:
        lev = int (chr.get ())
        if lev < 0 or lev > 127:
            raise Exception ('0 <= level <= 127')
        stat.set ('')
    except Exception as err:
        stat.set (err)
        return
    player.p.set_chorus_level (lev)

def set_gain ():
    try:
        gain = float (gn.get ())
        if gain < 0 or gain > 10:
            raise Exception ('0 <= gain <= 10')
        stat.set ('')
    except Exception as err:
        stat.set (err)
        return
    player.set_gain (gain)

def set_rev_mod ():
    player.p.set_reverb (rmod.get ())
    revmb.config (text=rmod.get ())

def set_bufsize ():
    if player.playing: play ();  # stop player if needed
    player.blen = int (bmod.get ())
    player.fs.set_buffer (player.blen)
    bufmb.config (text=bmod.get ())
def set_adrv ():
    if player.playing: play ();  # stop player if needed
    player.fs.set_buffer (driver=adrv.get ())
    txt = player.fs.audio_driver and adrv.get () or '---'
    drvmb.config (text=txt)

player = TestPlayer ()

root = T.Tk ()
sf = T.StringVar ()
sf.set (player.sf2)

frm = T.Frame (root, bd=1, relief=T.SUNKEN, padx=2, pady=2) # soundfont, midi file, play, position
frm.grid (row=0, column=0, padx=5, pady=5)
T.Label (frm, textvariable=sf).grid (row=0, column=0)
sf_btn = T.Button (frm, text='set soundfont', command=setfont)
sf_btn.grid (row=0, column=1)
mf = T.StringVar ()
mf.set ('---')
T.Label (frm, textvariable=mf).grid (row=1, column=0)
mf_btn = T.Button (frm, text='set midi file', command=setmidi)
mf_btn.grid (row=1, column=1)

play_btn = T.Button (frm, text='play', command=play)
play_btn.grid (row=2, column=1, rowspan=2)
prgr = T.StringVar ()
prgr.set ('0')
T.Label (frm, textvariable = prgr).grid (row=2, column=0)
tm = T.StringVar ()
tm.set ('0')
T.Label (frm, textvariable=tm).grid (row=2, column=2)
prgr_en = T.StringVar ()
prgr_en.set ('0')

T.Label (frm, text='position in ticks').grid (row=3, column=0)
T.Label (frm, text='duration in ticks').grid (row=3, column=2)

T.Entry (frm, textvariable=prgr_en, width=7).grid (row=4, column=0)
prgr_btn = T.Button (frm, text='go to', command=goto)
prgr_btn.grid (row=4, column=1)

frm = T.Frame (root, bd=1, relief=T.SUNKEN, padx=2, pady=2) # set gain
frm.grid (row=1, column=0, padx=5)
gn = T.StringVar (); gn.set (str (player.gain))
T.Entry (frm, textvariable=gn, width=3).grid (row=0, column=0)
T.Button (frm, text='set gain', command=set_gain).grid (row=0, column=1)
T.Label (frm, text='0-10').grid (row=0, column=2)

frm = T.Frame (root, bd=1, relief=T.SUNKEN, padx=2, pady=2) # quality setting and save
frm.grid (row=2, column=0, padx=5, pady=5)
qv = T.StringVar ()
qv.set ('0.6')
T.Entry (frm, textvariable=qv, width=3).grid (row=0, column=0)
T.Label (frm, text='compression quality (0.0-1.0)').grid (row=0, column=1)
sv_btn = T.Button (frm, text='save as', command=save)
sv_btn.grid (row=0, column=2)
stat = T.StringVar ()
stat_lab = T.Label (frm, textvariable=stat)
stat_lab.grid (row=1,column=0,columnspan=3,sticky=T.W)
stat_lab.configure (font = ('Tahoma', 8, 'bold'))

frm = T.Frame (root, bd=1, relief=T.SUNKEN, padx=2, pady=2) # reverb settings
frm.grid (row=0, column=2, padx=5, pady=5)
rev = T.StringVar (); rev.set ('0')
T.Entry (frm, textvariable=rev, width=3).grid (row=0, column=0)
T.Button (frm, text='set reverb level', command=reverb_level).grid (row=0, column=1, pady=3)
T.Label (frm, text='0-127').grid (row=0, column=2)
chr = T.StringVar (); chr.set ('0')
T.Entry (frm, textvariable=chr, width=3).grid (row=1, column=0)
T.Button (frm, text='set chorus level', command=chorus_level).grid (row=1, column=1, pady=3)
T.Label (frm, text='0-127').grid (row=1, column=2)
T.Label (frm, text='Reverb Model').grid (row=2, column=2)
rmod = T.StringVar (); rmod.set (F.revModels [0])
revmb = T.Menubutton (frm, text=F.revModels [0], relief=T.RAISED)
revmb.grid (row=2, column=1, pady=3)
revmenu = T.Menu (revmb, tearoff=0)
revmb.config (menu = revmenu)
revmenu.add_radiobutton (variable=rmod, label=F.revModels [0], command=set_rev_mod)
revmenu.add_radiobutton (variable=rmod, label=F.revModels [1], command=set_rev_mod)
revmenu.add_radiobutton (variable=rmod, label=F.revModels [2], command=set_rev_mod)
revmenu.add_radiobutton (variable=rmod, label=F.revModels [3], command=set_rev_mod)
revmenu.add_radiobutton (variable=rmod, label=F.revModels [4], command=set_rev_mod)

frm = T.Frame (root, bd=1, relief=T.SUNKEN, padx=2, pady=2) # buffer size and driver setting
frm.grid (row=1, column=2, rowspan=2, padx=5)
T.Label (frm, text='Buffer Size').grid (row=0, column=0)
bmod = T.StringVar (); bmod.set (str (player.blen))
bufmb = T.Menubutton (frm, text=bmod.get (), relief=T.RAISED)
bufmb.grid (row=1, column=0)
bufmenu = T.Menu (bufmb, tearoff=0)
bufmb.config (menu = bufmenu)
bufmenu.add_radiobutton (variable=bmod, label='64', command=set_bufsize)
bufmenu.add_radiobutton (variable=bmod, label='128', command=set_bufsize)
bufmenu.add_radiobutton (variable=bmod, label='256', command=set_bufsize)
bufmenu.add_radiobutton (variable=bmod, label='512', command=set_bufsize)
bufmenu.add_radiobutton (variable=bmod, label='1024', command=set_bufsize)
bufmenu.add_radiobutton (variable=bmod, label='2048', command=set_bufsize)
bufmenu.add_radiobutton (variable=bmod, label='4096', command=set_bufsize)
bufmenu.add_radiobutton (variable=bmod, label='8192', command=set_bufsize)

T.Label (frm, text='Audio Driver').grid (row=2, column=0)
adrv = T.StringVar (); adrv.set (player.driver_name)
drvmb = T.Menubutton (frm, text=adrv.get (), relief=T.RAISED)
drvmb.grid (row=3, column=0)
drvmenu = T.Menu (drvmb, tearoff=0)
drvmb.config (menu = drvmenu)
drvmenu.add_radiobutton (variable=adrv, label='pulseaudio', command=set_adrv)
drvmenu.add_radiobutton (variable=adrv, label='jack', command=set_adrv)
drvmenu.add_radiobutton (variable=adrv, label='alsa', command=set_adrv)
drvmenu.add_radiobutton (variable=adrv, label='oss', command=set_adrv)
drvmenu.add_radiobutton (variable=adrv, label='dsound', command=set_adrv)

root.after (200, progress)
root.mainloop ()