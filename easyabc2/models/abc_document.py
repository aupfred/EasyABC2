# easyabc2/models/abc_document.py

from dataclasses import dataclass
from easyabc2.utils.logging_utils import logger
from easyabc2.models.abc_assist.abc_character_encoding import abc_text_to_unicode

logger.debug("[ABCDocument] Importing…")

@dataclass
class TuneInfo:
    index: int
    title: str
    start_line: int
    end_line: int
    header_end_line: int # last line of header (or -1 if None) could be removed

class AbcDocument:
    def __init__(self, text: str = ""):
        self.text = text
        self.lines = text.splitlines()
        self.tunes: list[TuneInfo] = []
        self.duplicate_indexes = {}
        self.header_end_line = None
        self.header_length_chars = None
        self._parse()

    def _parse(self):
        lines = self.lines
        tunes = []
        current = None
        header_end_line = -1
        seen_first_x = False
        seen_indexes = {}
        self.duplicate_indexes = {}

        for i, line in enumerate(lines):
            #logger.debug(f"[ABCDocument] line {i}: {line}")
            if line.startswith("X:"):
                if not seen_first_x:
                    header_end_line = i - 1
                    self.header_end_line = header_end_line
                    self.header_length_chars=self._offset_of_line(header_end_line+1)
                    logger.debug(f"[ABCDocument] header end line: {self.header_end_line}")
                    logger.debug(f"[ABCDocument] header length line: {self.header_length_chars}")
                    seen_first_x = True

                if current:
                    current.end_line = i - 1
                    tunes.append(current)
                    current = None

                try:
                    index = int(line[2:].strip())
                except:
                    index = -1

                if index in seen_indexes:
                    if index not in self.duplicate_indexes:
                        self.duplicate_indexes[index] = [seen_indexes[index]]
                    self.duplicate_indexes[index].append(i)
                else:
                    seen_indexes[index] = i

                current = TuneInfo(
                    index=index,
                    title="",
                    start_line=i,
                    end_line=len(lines) - 1,
                    header_end_line=header_end_line
                )
                logger.debug(f"[ABCDocument] DEBUG: X {current}")

            elif line.startswith("T:") and current and not current.title:
                raw_title = line[2:].strip()
                current.title = abc_text_to_unicode(raw_title)
                logger.debug(f"[ABCDocument] DEBUG: T {current.title}")

        if current:
            current.end_line = len(lines) - 1
            tunes.append(current)
            current = None

        self.tunes = tunes
        logger.debug(f"[ABCDocument] DEBUG: Tunes {self.tunes}")
        

    # --- Common functions ---

    def tune_at_line(self, line_number: int) -> TuneInfo | None:
        if not self.tunes or len(self.tunes) == 0:
            return None
        if not self.header_end_line or line_number <= self.header_end_line:
            return self.tunes[0]
        for tune in self.tunes:
            if tune.start_line <= line_number <= tune.end_line:
                return tune
        return None

    def _offset_of_line(self, line_number: int) -> int:
        # offset of start of line in number of chars from beginning of text file
        return sum(len(l) + 1 for l in self.lines[:line_number])

    def _header_length_chars(self, tune: TuneInfo) -> int:
        if self.header_end_line < 0:
            return 0
        return sum(len(l) + 1 for l in self.lines[:tune.header_end_line + 1])

    # --- Get abc limited to header and abc ---

    def get_tune_abc(self, tune: TuneInfo) -> str:
        header = self.lines[:tune.header_end_line + 1] if tune.header_end_line >= 0 else []
        tune_lines = self.lines[tune.start_line : tune.end_line + 1]
        return "\n".join(header + tune_lines) + "\n"

    # --- Convert between tune and absolute number of chars (header included) ---

    def absolute_to_relative(self, pos_abs: int, tune: TuneInfo | None) -> int:
        """
        pos_abs : position in text file
        retourne : position in abc extract (header + tune)
        """
        # No tune → abort
        if tune is None:
            return pos_abs

        # Unknown tune → fallback
        if tune not in self.tunes:
            return pos_abs

        header_len = self.header_length_chars
        tune_start_abs = self._offset_of_line(tune.start_line)

        # In case before the tune
        if pos_abs < tune_start_abs:
            return header_len

        return header_len + (pos_abs - tune_start_abs)

    def relative_to_absolute(self, pos_rel: int, tune: TuneInfo | None) -> int:
        """
        pos_rel : position in abc extract (header + tune)
        retourne : position in text file
        """
        if tune is None:
            return pos_rel

        if tune not in self.tunes:
            return pos_rel

        header_len = self.header_length_chars
        tune_start_abs = self._offset_of_line(tune.start_line)

        # In case before the tune
        if pos_rel < header_len:
            return tune_start_abs

        return tune_start_abs + (pos_rel - header_len)
