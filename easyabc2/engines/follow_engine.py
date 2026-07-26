# easyabc2/engines/follow_engine.py

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Callable, Dict, Any

from easyabc2.utils.logging_utils import logger

logger.debug("[FollowScore] Importing FollowEngine…")

@dataclass
class TimedSvgNote:
    start_id: int
    rect_index: int
    line: int
    col: int
    tick_intervals: List[Tuple[int, int]]  # (start_tick, stop_tick)


class FollowScoreEngine:
    """
    Engine to enable to follow the active note selected or currently played.
    """

    def __init__(self, score_js: Callable[[str], None], preferences = None):
        """
        score_js : function to execute JS in ScoreView,
        """
        logger.debug("[FollowScore] Initializing…")
        self.score_js = score_js
        self.preferences = preferences

        # SVG Notes with MIDI timing
        self.timed_notes: List[TimedSvgNote] = []

        # Events (tick, "on"/"off", TimedSvgNote)
        self.events: List[Tuple[int, str, TimedSvgNote]] = []
        self.event_index: int = 0

        self.active_notes = set() # set of active notes
        self.playing = False      # whether playing is in progress or not
        self.is_my_page_loaded = True # whether js page is loaded or not to avoid to call to early
        self.pending_highlights = None # list of highlights that were not done because of page loading

    def apply_preferences(self, preferences = None):
        self.preferences = preferences
    
    def build(self, svg_notes: List[Dict[str, Any]], midi_events: List[Dict[str, Any]]):
        """
        svg_notes : dict list from SVG parsing:
            {
                "rect_index": int,
                "start_id": int,
                "line": int,   # 0-based
                "col": int,    # 0-based
            }

        midi_events : dicts from mftext parsing :
            {
                "row": int,          # 1-based in mftext
                "col": int,          # 1-based
                "start_tick": int,
                "stop_tick": int,
            }

        This function:
          - maps (row, col) MIDI events to (line, col) SVG notes
          - builds :
             - TimedSvgNote
             - start/stop events
        """
        self._map_svg_to_midi(svg_notes, midi_events)
        self._build_events()

    def build2(self, abc_text, midi_events: List[Dict[str, Any]]):
        """
        abc_text: extract of the abc used to build the midi file

        midi_events : list of dicts from mftext, e.g. :
            {
                "row": int,          # 1-based in mftext
                "col": int,          # 1-based
                "start_tick": int,
                "stop_tick": int,
            }

        This functions:
          - generate the SVG note sorted by time
          - the list of events start/stop
        """
        logger.debug("[FollowScore] Building v2…")
        self._create_timed_svg_notes(abc_text, midi_events)
        self._build_events()
        logger.debug("[FollowScore] Built ok")


    def _map_svg_to_midi(self, svg_notes, midi_events):
        """
        Link SVG to MIDI notes via (line,col) ↔ (row,col).
        """

        svg_by_linecol: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
        for n in svg_notes:
            key = (n["line"] + 1, n["col"] + 1)  # editor 0-based → mftext 1-based
            svg_by_linecol.setdefault(key, []).append(n)

        notes_by_start_id: Dict[int, TimedSvgNote] = {}

        for ev in midi_events:
            key = (ev["row"], ev["col"])
            if key not in svg_by_linecol:
                continue

            # First SVG note SVG matching ABC position
            svg_note = svg_by_linecol[key][0]
            start_id = svg_note["start_id"]

            if start_id not in notes_by_start_id:
                notes_by_start_id[start_id] = TimedSvgNote(
                    start_id=start_id,
                    rect_index=svg_note["rect_index"],
                    line=svg_note["line"],
                    col=svg_note["col"],
                    tick_intervals=[]
                )

            notes_by_start_id[start_id].tick_intervals.append(
                (ev["start_tick"], ev["stop_tick"])
            )

        self.timed_notes = list(notes_by_start_id.values())

    def _create_timed_svg_notes(self, abc_text, midi_events):
        line_offsets = []
        line_offsets = self._compute_line_offsets(abc_text)
        if not line_offsets:
            logger.debug("[FollowEngine] No line_offset yet")
            return

        #ornaments_to_correct = 'HLMOPSTuv~.'
        ornaments_to_correct = 'HIJKLMNOPQRSTUVWhijklmnopqrstuvw~.'

        notes_by_start_id: Dict[int, TimedSvgNote] = {}

        for ev in midi_events:
            row = ev["row"] - 1
            col = ev["col"] - 1
            if row < 0 or row >= len(line_offsets):
                logger.debug(f"[FollowEngine] Ignoring mftext row {row}, out of range for line_offsets={len(line_offsets)}")
                continue
            if col < 0:
                logger.debug(f"[FollowEngine] Ignoring mftext col {col}")
                continue

            start_id = line_offsets[row] + col

            # --- Chords correction ---
            # abc2svg and abc2midi do not consider the same position for chords.
            # abc2svg is considering the character [
            # abc2midi is considering the first note of the chord
            #  → local offset -1
            if start_id > 0 and abc_text[start_id - 1] == "[":
                start_id -= 1

            # --- Decoration correction ---
            # abc2svg and abc2midi do not consider the same position for decoration.
            # abc2midi is considering the decoration
            # abc2svg is considering the note
            #  → local offset +1
            if start_id < len(abc_text) and abc_text[start_id] in ornaments_to_correct:
                start_id += 1
                
            if start_id not in notes_by_start_id:
                notes_by_start_id[start_id] = TimedSvgNote(
                    start_id=start_id,
                    rect_index=0,
                    line=row,
                    col=col,
                    tick_intervals=[]
                )

            notes_by_start_id[start_id].tick_intervals.append(
                (ev["start_tick"], ev["stop_tick"])
            )

        self.timed_notes = list(notes_by_start_id.values())

    def _compute_line_offsets(self, abc_text: str) -> list[int]:
        offsets = []
        pos = 0
        abc_lines = abc_text.splitlines()
        for line in abc_lines:
            offsets.append(pos)
            pos += len(line) + 1  # +1 for end of line '\n'
        return offsets

    def _build_events(self) -> None:
        """Build sorted list of events (tick, 'on'/'off', note)."""
        events: List[Tuple[int, str, TimedSvgNote]] = []

        for note in self.timed_notes:
            for (start, stop) in note.tick_intervals:
                events.append((start, "on", note))
                events.append((stop, "off", note))

        events.sort(key=lambda e: e[0])

        self.events = events
        self.event_index = 0
        self.active_notes.clear()

    # ------------------------------------------------------------------
    # Called periodically from GUI thread
    # ------------------------------------------------------------------

    def set_active_notes(self, ids):
        update_highlight = False
        ids = set(ids)
        logger.debug(f"[FollowScore] is pageloaded: {self.is_my_page_loaded}")

        # Deactivate old notes
        for old in list(self.active_notes):
            if old not in ids:
                self.active_notes.remove(old)
                update_highlight = True

        # Activate new notes
        for new in ids:
            if new not in self.active_notes:
                self.active_notes.add(new)
                update_highlight = True

        # Automatic Scroll
        if update_highlight:
            js_ids = ",".join(str(i) for i in ids)
            if not self.is_my_page_loaded:
                logger.debug(f"[FollowScore] storing id {js_ids}")
                self.pending_highlights = js_ids
                return

            logger.debug(f"[FollowScore] highlighting id {js_ids}")
            self.score_js(f"highlightNotes([{js_ids}]);")

    def page_loaded(self):
        self.is_my_page_loaded = True
        logger.debug("[FollowScore] Page loaded follow engine")

        if self.pending_highlights is not None:
            js_ids = self.pending_highlights
            self.pending_highlights = None
            self.score_js(f"highlightNotes([{js_ids}]);")

    def reset(self) -> None:
        """To be called on play and when new tune selected."""
        self.event_index = 0
        self.active_notes.clear()

    def on_tick(self, current_tick: int, is_visual: bool) -> None:
        logger.debug(f"[FollowScore] On tick: {current_tick} is_visual: {is_visual}")
        update_highlight = False
        logger.debug(f"[FollowScore] event_index: {self.event_index}") # event_index_tick: {self.events[self.event_index][0]}")

        while self.event_index < len(self.events) and self.events[self.event_index][0] <= current_tick:
            tick, kind, note = self.events[self.event_index]

            if kind == "on":
                if note.start_id not in self.active_notes:
                    self.active_notes.add(note.start_id)
                    update_highlight = True

            else:  # "off"
                if note.start_id in self.active_notes:
                    self.active_notes.remove(note.start_id)
                    update_highlight = True

            self.event_index += 1

        if update_highlight and is_visual:
            ids = list(self.active_notes)
            js_ids = ",".join(str(i) for i in ids)
            logger.debug(f"[FollowScore] Request highlightNotes for {js_ids}")
            self.score_js(f"highlightNotes([{js_ids}]);")

    def set_selected_play_range(self, start_tick: int, end_tick: int) -> None:
        note_ids = self._find_note_ids_between_ticks(start_tick, end_tick)

        js_ids = ",".join(str(i) for i in note_ids)
        self.score_js(f"highlightPlayRange([{js_ids}]);")

    def set_selected_start(self, tick):
        note_ids = self._find_note_ids_at_tick(tick)

        js_ids = ",".join(str(i) for i in note_ids)
        self.score_js(f"highlightPlayStart([{js_ids}]);")

    def set_selected_end(self, tick):
        note_ids = self._find_note_ids_at_tick(tick)

        js_ids = ",".join(str(i) for i in note_ids)
        self.score_js(f"highlightPlayEnd([{js_ids}]);")

    def clear_selection(self):
        self.score_js("clearSelection();")

    #def _find_note_ids_at_tick(self, tick: int):
    #    selected_ids = set()

    #    for ev_tick, kind, note in self.events:
    #        if ev_tick > tick and kind == "on":
    #            # no need to continue as events sorted
    #            break

    #        for (start, stop) in note.tick_intervals:
    #            if start<= tick < stop:
    #                selected_ids.add(note.start_id)
    #                continue

    #    return selected_ids

    def _find_note_ids_at_tick(self, tick: int):
        return self._find_note_ids_between_ticks(tick,tick+1)

    def _find_note_ids_between_ticks(self, start_tick: int, end_tick: int):
        selected_ids = set()

        for ev_tick, kind, note in self.events:
            if ev_tick > end_tick and kind == "on":
                # no need to continue as events sorted
                break


            for (start, stop) in note.tick_intervals:
                if start< end_tick and start_tick < stop:
                    selected_ids.add(note.start_id)
                    continue

        return selected_ids
