# easyabc2/ui/document_tab.py
import re
import uuid
from pathlib import Path
from dataclasses import dataclass

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QSplitter
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QTextCursor

from easyabc2.engines.abc2svg_engine import ABC2SVGEngine
from easyabc2.engines.follow_engine import FollowScoreEngine, TimedSvgNote
from easyabc2.ui.abc_editor import ABCEditor
from easyabc2.models.abc_document import AbcDocument, TuneInfo
from easyabc2.ui.score_view import ScoreView
from easyabc2.utils.easyabc_utils import *
from easyabc2.ui.abc_assist_panel import AbcAssistPanel
from easyabc2.ui.editor_adapter import QtEditorAdapter
from easyabc2.ui.tune_list_widget import TuneListWidget
from easyabc2.utils.logging_utils import logger
from easyabc2 import _

logger.debug("[DocumentTab] Importing…")

from collections import namedtuple

PendingPos = namedtuple("PendingPos", "row col timestamp")

@dataclass
class TunePlaybackState:
    start_enabled: bool = False
    end_enabled: bool = False
    start_tick: int = 0
    end_tick: int = 0
    loop_enabled: bool = False
    tempo_factor: float = 1.0

class DocumentTab(QWidget):
    textChanged = Signal()
    cursorMoved = Signal(int, int)  # line, absolute_position
    noteClicked = Signal(int)
    playPositionChanged = Signal(int, int)
    tuneStopped = Signal()
    warningsChanged = Signal(bool)

    def __init__(self, base_temp_dir, parent=None):
        super().__init__(parent)
        self.uid = uuid.uuid4().hex
        base_temp_dir = Path(base_temp_dir)
        self.temp_dir = base_temp_dir / f"tab_{self.uid}"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        prefs = QApplication.instance().prefs
        self.current_file = None
        self.abc_document = None
        self.current_tune_index = None
        self.current_tune = None
        self.audio_tune = None
        self.note_offsets = []
        self.text_changed = False
        self.saved_text = ""
        self.loading = False
        self.encoding = "utf-8"
        self.max_tick = 100
        self.play_start_tick = 0
        self.play_end_tick = self.max_tick
        self.play_start_enabled = False
        self.play_end_enabled = False
        self.loop_enabled = False
        self.tempo_factor = 1.0
        self.playback_state = {}  # key = tune.index
        self.last_played_tick = 0
        self.play_just_started = False

        self.resources_path = Path(__file__).resolve().parent.parent / "resources"
        # Widgets
        self.editor = ABCEditor()
        self.is_score_view_loaded = False
        self.score_view = ScoreView()
        self.score_view.on_note_clicked = self._on_note_clicked

        self.follow_engine = FollowScoreEngine(
            score_js=lambda code: self.score_view.run_js(code)
        )
        self.score_view.page_loaded = self._on_page_loaded
        
        self.editor_adapter = QtEditorAdapter(self.editor)
        
        self.tune_list = TuneListWidget()
        self.tune_list.tuneSelected.connect(self.on_tune_selected)

        self.assist_panel = AbcAssistPanel(
            parent=None,
            editor=self.editor_adapter,
            prefs=prefs,
            cwd=self.resources_path
        )

        # Vertical Layout
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.score_view)
        splitter.addWidget(self.editor)
        splitter.setSizes([600, 400])

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

        # Signals
        self.editor.debouncedTextChanged.connect(self._on_editor_changed)
        self.editor.cursorPositionChanged.connect(self._on_cursor_changed)
        # Timer to filter events from editor to save perf
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._process_editor_event)
 
        self.play_timer = QTimer(self)
        self.play_timer.setSingleShot(True)
        self.play_timer.timeout.connect(self._on_play_tick)

        self._initialize_document()

    @property
    def engines(self):
        return QApplication.instance().engines

    def _initialize_document(self):
        abc = self.editor.toPlainText()
        self.abc_document = AbcDocument(abc)

        has_warnings = bool(self.abc_document.duplicate_indexes)
        self.warningsChanged.emit(has_warnings)
    
    def apply_preferences(self):
        pass

    # ------------------------------------------------------------
    # File Management actions
    # ------------------------------------------------------------
    def load_file(self, path):
        self.loading = True

        text, encoding = read_abc_file(path)
        text = normalize_abc_text(text)

        self.editor.setPlainText(text)
        self.editor.ensureCursorVisible()
        self.editor.viewport().update()
        QApplication.processEvents()
        self.current_file = path
        self.encoding = encoding
        self.saved_text = text
        self.text_changed = True # force to propagate change for first rendering

        self.loading = False

    def save(self):
        if not self.current_file:
            return False

        text = self.editor.toPlainText()

        try:
            data = text.encode(self.encoding)
        except UnicodeEncodeError:
            QMessageBox.warning(
                self,
                _("Encoding error"),
                _("Cannot save using encoding '{enc}'. Some characters cannot be represented.").format(enc=self.encoding)
             )
            return False

        with open(self.current_file, "wb") as f:
            f.write(data)

        self.saved_text = text
        self.text_changed = False
        return True

    def save_as(self, path):
        text = self.editor.toPlainText()

        try:
            data = text.encode(self.encoding)
        except UnicodeEncodeError:
            QMessageBox.warning(
                self,
                _("Encoding error"),
                _("Cannot save using encoding '{enc}'. Some characters cannot be represented.").format(enc=self.encoding)
            )
            return False

        with open(path, "wb") as f:
            f.write(data)

        self.current_file = path
        self.saved_text = text
        self.text_changed = False
        return True

    # ------------------------------------------------------------
    # SVG external interactions
    # ------------------------------------------------------------
    def update_svg(self):
        abc = self.editor.toPlainText()
        svg = self.engines.abc2svg.abc_to_svg(abc)
        self._update_note_offsets(svg)
        #self.follow_engine.is_my_page_loaded = False
        self.is_score_view_loaded = False
        self.score_view.load_svg(svg)
        return svg

    def update_svg(self, abc_text: str | None):
        if not abc_text:
            svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="600" height="140">
  <rect width="100%" height="100%" fill="#f8f8f8"/>
  <text x="50%" y="45%" font-size="20" text-anchor="middle" fill="#444">
    {_("No tune selected")}
  </text>
  <text x="50%" y="70%" font-size="14" text-anchor="middle" fill="#666">
    {_("Please select or complete a tune in the editor")}
  </text>
</svg>
"""
        else:
            svg = self.engines.abc2svg.abc_to_svg(abc_text)
            self._update_note_offsets(svg)
            #self.follow_engine.is_my_page_loaded = False

        self.is_score_view_loaded = False
        save_temp_svg(svg, self.temp_dir)
        self.score_view.load_svg(svg)
        return svg

    # Internal API SVG
    # ------------------------------------------------------------
    def _update_note_offsets(self, svg_text: str):
        self.note_offsets = self._extract_note_offsets(svg_text)
        return

    def _extract_note_offsets(self, svg_text):
        # Looks for any class of kind _123_
        return sorted({
            int(m.group(1))
            for m in re.finditer(r'class="[^"]*_(\d+)_', svg_text)
        })

    # ------------------------------------------------------------
    # Request to refresh
    # ------------------------------------------------------------
    def rebuild_svg(self):
        self.update_svg(self.current_tune_abc)
        if self.audio_tune is not None and self.current_tune is not None and self.current_tune != self.audio_tune:
            self._update_active_notes()

    def rebuild_midi(self):
        if self.audio_tune is not None:
            return
        
        self._update_midi()

    # ------------------------------------------------------------
    # Action Requests
    # ------------------------------------------------------------
    def goto_line(self, line: int) -> None:
        self.editor.go_to_line(line)

    def on_tune_selected(self, tune):
        self.goto_line(tune.start_line)
        self.editor.setFocus()

    def is_modified(self):
        return self.editor.toPlainText() != self.saved_text

    def export_tune_to_pdf(self, file):
        self.score_view.export_tune_to_pdf(file)

    def highlight_tick(self, tick):
        self.follow_engine.set_selected_for_play(tick)
        
    def highlight_start_tick(self, tick):
        self.follow_engine.set_selected_start(tick)
        
    def highlight_end_tick(self, tick):
        self.follow_engine.set_selected_end(tick)

    def unhighlight_start_tick(self, tick):
        self.follow_engine.set_selected_start(tick)
        
    def unhighlight_end_tick(self, tick):
        self.follow_engine.set_selected_end(tick)

    def update_start_tick(self, tick):
        logger.debug("[DocumentTab] Update start tick")
        if tick == self.play_start_tick:
            return
        
        self.play_start_enabled = True
        self.play_start_tick = tick
        if self.play_start_tick > self.play_end_tick:
            self.play_end_tick = tick
        self._update_play_selection_display()
        self._update_playback_state()

    def update_end_tick(self, tick):
        logger.debug("[DocumentTab] Update end tick")
        if tick != self.play_end_tick:
            self.play_end_enabled = True
            self.play_end_tick = tick
            if self.play_start_tick > self.play_end_tick:
                self.play_start_tick = tick
            self._update_play_selection_display()
            self._update_playback_state()

    def enable_start(self, enabled):
        logger.debug("[DocumentTab] enable start")
        if enabled != self.play_start_enabled:
            self.play_start_enabled = enabled
            self._update_play_selection_display()
            self._update_playback_state()

    def enable_end(self, enabled):
        logger.debug("[DocumentTab] enable end")
        if enabled != self.play_end_enabled:
            self.play_end_enabled = enabled
            self._update_play_selection_display()
            self._update_playback_state()

    def _update_playback_state(self):
        logger.debug("[DocumentTab] Update playback state")
        if self.audio_tune is not None:
            tune = self.audio_tune
        else:
            tune = self.current_tune
        state = self.playback_state.setdefault(tune.index, TunePlaybackState())
        state.start_enabled = self.play_start_enabled
        state.end_enabled = self.play_end_enabled
        state.start_tick = self.play_start_tick
        state.end_tick = self.play_end_tick
        state.loop_enabled = self.loop_enabled
        state.tempo_factor = self.tempo_factor

    def _update_play_selection_display(self):
        logger.debug("[DocumentTab] Update play selection display")
        if not self.play_start_enabled and not self.play_end_enabled:
            self.follow_engine.clear_selection()
            return

        # tick -1 to have no start marker and still highlight range, change to self.max_tick to prevent range
        start_tick=self.play_start_tick if self.play_start_enabled else -1

        # tick self.max_tick+1 to have no end marker and still highlight range, change to -1 to prevent range
        end_tick=self.play_end_tick if self.play_end_enabled else self.max_tick+1

        self.follow_engine.set_selected_start(start_tick)
        self.follow_engine.set_selected_play_range(start_tick, end_tick)
        self.follow_engine.set_selected_end(end_tick)

    # ------------------------------------------------------------
    # Signals / Timers Actions
    # ------------------------------------------------------------
    def _on_editor_changed(self):
        if self.loading:
            return
        #self.text_changed = self.text_changed or self.is_modified()
        self.text_changed = True
        self._debounce_timer.start(150)

    def _on_cursor_changed(self):
        if self.loading:
            return
        self._debounce_timer.start(150)
        #cursor = self.editor.textCursor()
        #line = cursor.blockNumber()
        #pos = cursor.position()
        #self.cursorMoved.emit(line, pos)

    def _on_note_clicked(self, start_rel):
        doc = self.abc_document
        tune = doc.tune_at_line(self.editor.textCursor().blockNumber())
        pos_abs = doc.relative_to_absolute(start_rel, tune)
        self.editor.setCursorPosition(pos_abs)
        self.editor.setFocus()
        # Signal to notify MainWindow
        #self.noteClicked.emit(int(start_rel))

    def _on_page_loaded(self):
        logger.debug("[DocumentTab] Page loaded")
        self.is_score_view_loaded = True

        #self.follow_engine.page_loaded()
        self._update_play_selection_display()

        self._update_active_notes()

    # ------------------------------------------------------------
    # Playback interactions
    # ------------------------------------------------------------
    def play(self):
        if self.engines.midi_player:
            logger.debug("[DocumentTab] Tab Play")
            self.follow_engine.reset()
            self.audio_tune = self.current_tune
            self.tune_list.update_icons(self.current_tune, self.audio_tune)
            self.engines.midi_player.load(self.temp_dir / "current.mid")
            self.engines.midi_player.set_title(self.audio_tune.title)
            self.engines.midi_player.play()
            self.play_just_started = True
            self.play_timer.start(20)
            return
        return

    def stop(self):
        if self.engines.midi_player:
            self.engines.midi_player.stop()
            self.follow_engine.reset()
            tune_changed_while_playing = (self.audio_tune != self.current_tune)
            self.audio_tune = None
            self.engines.midi_player.set_title(None)
            self.tune_list.update_icons(self.current_tune, self.audio_tune)
            if tune_changed_while_playing:
                self._update_midi()
            self.tuneStopped.emit()

    def set_loop(self,enabled):
        self.loop_enabled = enabled
        self._update_playback_state()

    def tell(self):
        if self.engines.midi_player:
            return self.engines.midi_player.tell()
        return 0

    # Playback internal API
    # ------------------------------------------------------------
    def _on_play_tick(self):
        # Effective play started after some delay
        if self.play_just_started:
            title = self.audio_tune.title
            logger.debug(f"[DocumentTab] Play {title}")
            play_start_enabled = self.play_start_enabled
            play_start_tick = self.play_start_tick
            logger.debug(f"[DocumentTab] Play start_enabled {play_start_enabled} at ticks {play_start_tick}")
            length = self.engines.midi_player.length()
            logger.debug(f"[DocumentTab] Tune length {length}")
            # Need to make sure that midi file is properly loaded
            if length == 0:
                self.play_timer.start(20)
                return
            self.play_just_started = False
            if self.play_start_enabled:
                play_start_tick = self.play_start_tick
                logger.debug(f"[DocumentTab] Play; go to selected tick {play_start_tick}")
                self.engines.midi_player.seek(self.play_start_tick)
            self.play_timer.start(20)
            return

        # Let player continue to play MIDI if not independant (e.g. MPlay)
        self.engines.midi_player.idle()

        # Get current position
        tick = self.engines.midi_player.tell()
        length = self.engines.midi_player.length()
        
        if tick >= self.play_end_tick:
            if self.engines.midi_player.loop_enabled:
                self.follow_engine.reset()
                self.engines.midi_player.seek(self.play_start_tick)
                if not (self.engines.midi_player.is_playing or self.engines.midi_player.is_paused):
                    self.engines.midi_player.play()
                tick = self.play_start_tick
            else:
                self.stop()
                return

        # Request to highlight note if tune that is playing is also the one displayed
        is_visual = (self.audio_tune == self.current_tune)
        self.follow_engine.on_tick(tick, is_visual)

        # Request position slider to update
        if tick != self.last_played_tick:
            self.last_played_tick = tick
            self.playPositionChanged.emit(tick, length)
        # Relaunch timer or force stop
        if self.engines.midi_player.is_playing or self.engines.midi_player.is_paused:
            self.play_timer.start(20)
        else:
            self.stop()

    def on_midi_loaded(self):
        logger.info("[DocumentTab] MIDI loaded")

        # Not needed, kept in case

    def on_midi_stopped(self):
        logger.info("[DocumentTab] Music stopped")

        # Not needed, kept in case

    # ------------------------------------------------------------
    # Document internal processing
    # ------------------------------------------------------------
    def _process_editor_event(self):
        logger.debug("[DocumentTab] PROCESS_EDITOR_EVENT")
        cursor = self.editor.textCursor()
        new_tune = self.abc_document.tune_at_line(cursor.blockNumber())
        tune_changed = (new_tune != self.current_tune)
        self.assist_panel.update_assist()

        if not self.text_changed and not tune_changed and self.is_score_view_loaded:
            logger.debug("[DocumentTab] Editor event: case no text changed and same tune")
            self._update_active_notes()
            return

        if self.text_changed:
            logger.debug("[DocumentTab] Editor event: case text changed → rebuild document")
            self._update_document_state()
            self.text_changed = False

        if tune_changed and new_tune:
            logger.debug("[DocumentTab] Editor event: case new tune → rebuild for this tune")
            self._update_for_tune(new_tune)

        # Notify MainWindow (TuneList, title…)
        self.textChanged.emit()

    def _update_document_state(self):
        logger.debug("[DocumentTab] UPDATE_DOCUMENT_STATE")

        cursor = self.editor.textCursor()
        abc = self.editor.toPlainText()
        self.abc_document = AbcDocument(abc)
        has_warnings = bool(self.abc_document.duplicate_indexes)
        self.warningsChanged.emit(has_warnings)

        self.tune_list.set_tunes(self.abc_document.tunes)
        new_tune = self.abc_document.tune_at_line(cursor.blockNumber())
        #tune_changed = (new_tune != self.current_tune)
        #if tune_changed:
        if new_tune:
            self._update_for_tune(new_tune)
        #else:
        #    self._update_active_notes()
        #return

    def _update_for_tune(self, tune):
        logger.debug("[DocumentTab] UPDATE_FOR_TUNE")
        
        if not tune:
            logger.error("[DocumentTab] no tune")
            svg = self.update_svg(None)
            return
        
        self._update_current_tune(tune)
        if not self.current_tune_abc:
            logger.error(f"[DocumentTab] no current abc for tune {tune}")
            svg = self.update_svg(None)
            return

        svg = self.update_svg(self.current_tune_abc)

        if not self.engines.abc2svg.valid:
            logger.error("[DocumentTab] Abc2svg not valid")
            return
        
        self.tune_list.select_tune(self.current_tune.index)
        self.tune_list.update_icons(self.current_tune, self.audio_tune)

        #if self.audio_tune is not None:
        if (self.engines.midi_player.is_playing or self.engines.midi_player.is_paused):
            logger.debug("[DocumentTab] play in progress do not update midi")
            if self.is_score_view_loaded:
                if self.current_tune != self.audio_tune:
                    logger.debug("[DocumentTab] current tune is not the one played so possible to highlight not from editor")
                    self._update_active_notes()
                else:
                    logger.debug("[DocumentTab] current tune is the one played so highllight on tick")
                    self.follow_engine.on_tick(self.last_played_tick, True)
            return

        self._update_midi()
        self._restore_playback_state_for_tune()
        if self.is_score_view_loaded:
            self._update_play_selection_display()
        
            self._update_active_notes()

    def _update_current_tune(self, tune):
        self.follow_engine.reset()
        self.current_tune_index = tune.index
        self.current_tune = tune
        doc = self.abc_document
        self.current_tune_abc = doc.get_tune_abc(tune)
        save_temp_abc(self.current_tune_abc,self.temp_dir)    

    def _update_midi(self):
        logger.debug("[DocumentTab] UPDATE_MIDI")
        mftext = self.engines.abc2midi.build_follow_data(
            self.current_tune_abc,
            self.temp_dir / "current.mid"
        )
        save_temp_mftext(mftext, self.temp_dir)

        self._build_follow_engine(
            self.current_tune,
            self.current_tune_abc,
            mftext
        )

    def _build_follow_engine(self, tune, abc_text, mftext):
        logger.debug("[DocumentTab] UPDATE_FOR_TUNE")
        ticks_per_quarter = 480
        if not mftext or not abc_text.strip():
            logger.error("[DocumentTab] FollowEngine skipped: incomplete ABC or mftext")
            return
        try:
            midi_events = self._parse_mftext_to_midi_events(mftext, ticks_per_quarter)
        except Exception as e:
            logger.warning(f"[DocumentTab] Invalid mftext, skipping follow: {e}")
            return
        logger.debug(f"[DocumentTab] midi_events: {midi_events}")

        # Do not try to build if no midi_events
        if midi_events:
            self.follow_engine.build2(abc_text, midi_events)

    def _parse_mftext_to_midi_events(self, mftext: str, ticks_per_quarter: int):
        logger.debug("[DocumentTab] Parse mftect to midi events")
        # in mftext,
        # CntlParm lines with unknown are used to report corresponding row and col of note in abc text
        # CntlParm with unknown are always preceeding a note on instruction
        # to manage trill, mordent... off event are stored until end of track or a line with CntlParm
        # in this case the pending off is considered.
        
        pos_re = re.compile(r'^\s*(\d+\.\d+)\s+CntlParm\s+1\s+unknown\s+=\s*\d*\s+(\d+)')
        note_re = re.compile(r'^\s*(\d+\.\d+)\s+Note\s+(on|off)\s+(\d+)\s+(\d+)')
        end_re = re.compile(r'^\s*(\d+\.\d+)\s+Meta\s+event\,\s+end\s+of\s+track')

        events = []
        active = {}
        pos_values = []
        current_row = None
        current_col = None
        last_timestamp = None
        pending_position = None
        pending_stops = {}
        self.play_start_tick = 0
        self.play_end_tick = 0

        for line in mftext.splitlines():
            m = end_re.match(line)
            if m:
                for key, stop_tick in pending_stops.items():
                    start_tick, row, col = active.pop(key)
                    events.append({
                        "row": row,
                        "col": col,
                        "start_tick": start_tick,
                        "stop_tick": stop_tick,
                    })
                pending_stops.clear()
                timestamp = float(m.group(1))
                tick = int(timestamp * ticks_per_quarter)
                if tick >= self.play_end_tick:
                    self.play_end_tick = tick
                continue
                
            # ABC Position encoded in 5 values
            m = pos_re.match(line)
            if m:
                for key, stop_tick in pending_stops.items():
                    start_tick, row, col = active.pop(key)
                    events.append({
                        "row": row,
                        "col": col,
                        "start_tick": start_tick,
                        "stop_tick": stop_tick,
                    })
                pending_stops.clear()

                timestamp = float(m.group(1))
                value = int(m.group(2))
                # New sequence or same timestamp
                if not pos_values or timestamp == last_timestamp:
                    pos_values.append(value)
                    last_timestamp = timestamp

                    if len(pos_values) == 5:
                        v0, v1, v2, v3, v4 = pos_values
                        row = (v0 << 14) + (v1 << 7) + v2
                        col = (v3 << 7) + v4
                        current_row = row
                        current_col = col
                        pending_position = PendingPos(row, col, timestamp)
                        pos_values = []
                        last_timestamp = None
                else:
                    # new timestamp → reset
                    pos_values = [value]
                    last_timestamp = timestamp
                continue

            # Note on/off
            m = note_re.match(line)
            if m:
                #if not current_row or not current_col:
                #    continue
                note_timestamp = float(m.group(1))
                tick = int(note_timestamp * ticks_per_quarter)
                onoff = m.group(2)
                channel = int(m.group(3))
                note_num = int(m.group(4))
                key = (channel, note_num)
                

                if onoff == "on":
                    if pending_position and note_timestamp >= pending_position.timestamp:
                        current_row, current_col = pending_position.row, pending_position.col
                        pending_position = None
                        #current_row = current_row + tune_start_line - file_header_line

                        active[key] = (tick, current_row, current_col)
                else:
                    if key in active:
                        pending_stops[key] = tick
                        self.max_tick = tick
                        self.play_end_tick = tick

        events.sort(key=lambda e: e["start_tick"])
        return events

    def _restore_playback_state_for_tune(self):
        logger.debug("[DocumentTab] Restore playback state for tune")
        state = self.playback_state.get(self.current_tune.index)
        if not state:
            state = TunePlaybackState(
                start_enabled=False,
                end_enabled=False,
                start_tick=0,
                end_tick=self.max_tick,
                loop_enabled=False,
                tempo_factor=1.0,
            )
            self.playback_state[self.current_tune.index] = state

        logger.debug(f"[DocumentTab] Stored playback info {self.playback_state}")
        logger.debug(f"[DocumentTab] Restore playback tune {self.current_tune.index}")
        logger.debug(f"[DocumentTab] Restore start {state.start_enabled}@{state.start_tick}")
        logger.debug(f"[DocumentTab] Restore end {state.end_enabled}@{state.end_tick}")
        logger.debug(f"[DocumentTab] Restore loop {state.loop_enabled}")
        logger.debug(f"[DocumentTab] Restore tempo {state.tempo_factor}")
        # Appliquer l’état
        self.play_start_enabled = state.start_enabled
        self.play_end_enabled = state.end_enabled
        self.play_start_tick = state.start_tick
        self.play_end_tick = state.end_tick
        self.loop_enabled = state.loop_enabled
        self.tempo_factor = state.tempo_factor

    def _update_active_notes(self):
        if not self._can_update_active_notes():
            logger.debug("[DocumentTab] do not set active notes")
            return
        logger.debug("[DocumentTab] SET_ACTIVE_NOTES")
        doc = self.abc_document
        cursor = self.editor.textCursor()
        tune = doc.tune_at_line(cursor.blockNumber())

        if cursor.hasSelection():
            abs_start = cursor.selectionStart()
            abs_end   = cursor.selectionEnd()

            rel_start = doc.absolute_to_relative(abs_start, tune)
            rel_end   = doc.absolute_to_relative(abs_end, tune)

            active = [o for o in self.note_offsets if rel_start <= o <= rel_end]

        else:
            pos_abs = cursor.position()
            pos_rel = doc.absolute_to_relative(pos_abs, tune)

            # previous note or same
            note = max((o for o in self.note_offsets if o <= pos_rel), default=None)
            active = [note] if note is not None else []

        #if not self.follow_engine.playing:
        #if not self.engines.midi_player.is_playing and not self.engines.midi_player.is_paused and self.is_score_view_loaded:
        self.follow_engine.set_active_notes(active)

    def _can_update_active_notes(self):
        if self.current_tune is None:
            return False
        return not self.is_playing_current_tune()

    def is_playback_available(self):
        if self.current_tune is None:
            return False

        if not self.engines.midi_player.is_active:
            logger.debug("[Document Tab] OK as no play started")
            return True

        logger.debug(f"[Document Tab] Playback available: {self.audio_tune == self.current_tune}")
        return self.is_playing_current_tune()

    def is_playing_current_tune(self):
        if self.current_tune is None:
            return False

        if not self.engines.midi_player.is_active:
            return False

        if self.audio_tune is None:
            return False

        return self.audio_tune == self.current_tune


