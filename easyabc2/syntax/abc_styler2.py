# easyabc2/syntax/abc_styler2.py

from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

from easyabc2.utils.themes import EDITOR_THEMES

class ABCHighlighter(QSyntaxHighlighter):

    STYLE_DEFAULT = 0
    STYLE_COMMENT = 1
    STYLE_DIRECTIVE = 2
    STYLE_FIELDX = 3
    STYLE_FIELDX_VALUE = 4
    STYLE_FIELD = 5
    STYLE_FIELD_VALUE = 6
    STYLE_GCHORD = 7
    STYLE_STRING = 8
    STYLE_CHORD = 9
    STYLE_GRACE = 10
    STYLE_ORNAMENT = 11
    STYLE_LYRICS = 12
    STYLE_BAR = 13
    STYLE_NOTE = 14

    def __init__(self, document, preferences=None):
        super().__init__(document)
        self.preferences = preferences
        self._build_formats()
        self.fields = 'ABCDEFGHIJKLMmNOPQRrSsTUVWwXYZ'

    # ------------------------------------------------------------
    # Prepare colors
    # ------------------------------------------------------------
    def _build_formats(self):
        self.formats = {}
        theme_name = self.preferences["editor_theme"]
        theme = EDITOR_THEMES.get(theme_name, EDITOR_THEMES["light"])


        def make(color_hex):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color_hex))
            return fmt

        def make_bold(color_hex):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color_hex))
            fmt.setFontWeight(QFont.Bold)
            return fmt

        def make_bg(color_hex, bg_hex):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color_hex))
            #fmt.setBackground(QColor(bg_hex))
            fmt.setFontWeight(QFont.Bold)
            return fmt

        # Default colors
        self.formats[self.STYLE_DEFAULT] = make("#000000")
        self.formats[self.STYLE_DIRECTIVE] = make("#803378")
        self.formats[self.STYLE_COMMENT] = make("#656E77")
        self.formats[self.STYLE_FIELDX] = make_bold("#000000")
        self.formats[self.STYLE_FIELDX_VALUE] = make("#000000")
        self.formats[self.STYLE_FIELD] = make_bold("#B75501")
        self.formats[self.STYLE_FIELD_VALUE] = make("#B75501")
        self.formats[self.STYLE_GCHORD] = make_bold("#131415")
        self.formats[self.STYLE_STRING] = make("#2F6F44")
        self.formats[self.STYLE_CHORD] = make("#131415")
        self.formats[self.STYLE_GRACE] = make("#AA5500")
        self.formats[self.STYLE_ORNAMENT] = make("#015692")
        self.formats[self.STYLE_LYRICS] = make("#88b688")
        self.formats[self.STYLE_BAR] = make_bold("#0000cc")
        self.formats[self.STYLE_NOTE] = make("#41505e")
        # Colors from theme
        self.formats[self.STYLE_DEFAULT] = make(theme["default"])
        self.formats[self.STYLE_COMMENT] = make(theme["comment"])
        self.formats[self.STYLE_DIRECTIVE] = make(theme["directive"])
        self.formats[self.STYLE_FIELDX] = make_bg(theme["fieldx"],"#FFF2CC")
        self.formats[self.STYLE_FIELDX_VALUE] = make_bg(theme["fieldx_value"],"#FFF2CC")
        self.formats[self.STYLE_FIELD] = make_bold(theme["field"])
        self.formats[self.STYLE_FIELD_VALUE] = make(theme["field_value"])
        self.formats[self.STYLE_GCHORD] = make_bold(theme["gchord"])
        self.formats[self.STYLE_STRING] = make(theme["string"])
        self.formats[self.STYLE_CHORD] = make(theme["chord"])
        self.formats[self.STYLE_GRACE] = make(theme["grace"])
        self.formats[self.STYLE_ORNAMENT] = make(theme["ornament"])
        self.formats[self.STYLE_LYRICS] = make(theme["lyrics"])
        self.formats[self.STYLE_BAR] = make_bold(theme["bar"])
        self.formats[self.STYLE_NOTE] = make(theme["note"])


    # ------------------------------------------------------------
    # highligh function called
    # ------------------------------------------------------------
    def highlightBlock(self, text):
        # 1. ABC Directives (%%...)
        if text.startswith('%%'):
            # Find comments at the end of a directive
            comment_pos = text.find('%', 2)  # after first 2 %
            if comment_pos != -1:
                # Highlight directive
                self.setFormat(0, comment_pos, self.formats[self.STYLE_DIRECTIVE])
                # Highlight comment
                self.setFormat(comment_pos, len(text) - comment_pos, self.formats[self.STYLE_COMMENT])
            else:
                # No comments → whole line as a directive
                self.setFormat(0, len(text), self.formats[self.STYLE_DIRECTIVE])
            return
        
        # 2. whole line as a comment
        if text.startswith('%'):
            self.setFormat(0, len(text), self.formats[self.STYLE_COMMENT])
            return

        # 3. Comment as end of line
        comment_pos = text.find('%')
        if comment_pos != -1:
            self.setFormat(comment_pos, len(text) - comment_pos, self.formats[self.STYLE_COMMENT])
            text_before = text[:comment_pos]
        else:
            text_before = text

        # 4. Apply ABC rules on text before comment
        self._highlight_abc(text_before)
       
    # ------------------------------------------------------------
    # Internal highlight functions per type
    # ------------------------------------------------------------
    def _highlight_abc(self, text):
        i = 0
        length = len(text)

        if len(text) > 2 and text[1] == ':' and text[0] in self.fields:
            self._highlight_field_or_lyrics(text)
            return
            
        while i < length:
            ch = text[i]
            
            # Ornaments
            if ch == '!':
                i = self._highlight_exclamation_ornament(text, i)
                continue

            if ch == '+':
                i = self._highlight_plus_ornament(text, i)
                continue

            # Chords [CEG]
            if ch == '[':
                i = self._highlight_chord_or_embedded_field(text, i)
                continue

            # Gracenotes {abc}
            if ch == '{':
                i = self._highlight_grace(text, i)
                continue

            # Guitar chords or annotation
            if ch == '"':
                i = self._highlight_string(text, i)
                continue

            # Bars
            if ch in "|:[]":
                i = self._highlight_bar(text, i)
                continue

            # Notes
            if ch in "^_=ABCDEFGabcdefg":
                i = self._highlight_note(text, i)
                continue

            i += 1

    def _highlight_field_or_lyrics(self, text):
        length = len(text)

        if text[0] == "X":
            self.setFormat(0, 2, self.formats[self.STYLE_FIELDX])
            self.setFormat(2, length - 2, self.formats[self.STYLE_FIELDX_VALUE])
            self.setCurrentBlockState(1)
        else:
            self.setFormat(0, 2, self.formats[self.STYLE_FIELD])
            self.setCurrentBlockState(0)
            if text[0] in "Ww":
                self.setFormat(2, length - 2, self.formats[self.STYLE_LYRICS])
            else:
                self.setFormat(2, length - 2, self.formats[self.STYLE_FIELD_VALUE])
        return

    def _highlight_exclamation_ornament(self, text, i):
        start = i
        i += 1
        length = len(text)

        while i < length and text[i] != '!':
            i += 1

        if i < length:
            i += 1  # include !
        self.setFormat(start, i - start, self.formats[self.STYLE_ORNAMENT])
        return i

    def _highlight_plus_ornament(self, text, i):
        start = i
        i += 1
        length = len(text)

        while i < length and text[i] != '+':
            i += 1

        if i < length:
            i += 1
        self.setFormat(start, i - start, self.formats[self.STYLE_ORNAMENT])
        return i

    def _highlight_chord_or_embedded_field(self, text, i):
        start = i
        length = len(text)

        # Embedded field case, e.g.: [M:3/4]
        if i + 2 < length and text[i+1] in self.fields and text[i+2] == ':':
            # find next ]
            i += 3
            while i < length and text[i] != ']':
                i += 1
            if i < length:
                i += 1
            self.setFormat(start, i - start, self.formats[self.STYLE_FIELD])
            return i

        # Else : it is a chord [CEG]
        i += 1
        while i < length and text[i] != ']':
            i += 1
        if i < length:
            i += 1
        self.setFormat(start, i - start, self.formats[self.STYLE_CHORD])
        return i

    def _highlight_grace(self, text, i):
        start = i
        i += 1
        length = len(text)

        while i < length and text[i] != '}':
            i += 1

        if i < length:
            i += 1
        self.setFormat(start, i - start, self.formats[self.STYLE_GRACE])
        return i

    def _highlight_string(self, text, i):
        start = i
        i += 1
        length = len(text)

        while i < length and text[i] != '"':
            if text[i] == '\\' and i + 1 < length:
                i += 2
                continue
            i += 1

        if i < length:
            i += 1
        self.setFormat(start, i - start, self.formats[self.STYLE_LYRICS])
        return i

    def _highlight_string(self, text, i):
        start = i
        i += 1
        length = len(text)

        # if wrong string
        if i >= length:
            return start + 1

        ch = text[i]

        # 1. Try to detect guitar chords
        # Starting with A-G
        if ch.upper() in "ABCDEFG":
            style = self.STYLE_GCHORD
        else:
            # 2. Text annotation
            style = self.STYLE_STRING

        # 3. Continue up to next "
        i += 1
        while i < length and text[i] != '"':
            if text[i] == '\\' and i + 1 < length:
                i += 2
                continue
            i += 1

        if i < length:
            i += 1  # include ending "

        # 4. Apply style
        self.setFormat(start, i - start, self.formats[style])

        return i

    def _highlight_bar(self, text, i):
        start = i
        length = len(text)

        # Include all characters of a bar
        bar_chars = "|:[]123456789"

        while i < length and text[i] in bar_chars:
            i += 1

        self.setFormat(start, i - start, self.formats[self.STYLE_BAR])
        return i

    def _highlight_note(self, text, i):
        start = i
        length = len(text)

        # 1. Accidentals
        while i < length and text[i] in "^_=":
            i += 1

        # 2. Note
        if i < length and text[i].upper() in "ABCDEFG":
            i += 1
        else:
            return start + 1  # not a note

        # 3. Octave
        while i < length and text[i] in "',":
            i += 1

        # 4. Length
        while i < length and text[i].isdigit():
            i += 1
        if i < length and text[i] == '/':
            i += 1
            while i < length and text[i].isdigit():
                i += 1

        # 5. Ornaments
        while i < length and text[i] in "~.><":
            i += 1

        self.setFormat(start, i - start, self.formats[self.STYLE_NOTE])
        return i
