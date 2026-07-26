from PySide6.QtCore import QObject, Signal, Slot, QUrl
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtGui import QShortcut, QKeySequence

from easyabc2.utils.themes import FOLLOW_THEMES
from easyabc2.utils.logging_utils import logger

logger.debug("[ScoreView] Importing ScoreView…")

class JsBridge(QObject):
    noteClicked = Signal(str)

    @Slot(str)
    def onNoteClicked(self, start: str):
        self.noteClicked.emit(start)


class ScoreView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.on_note_clicked = None
        self.page_loaded = None
        self.page_ready = False
        self.pending_highlight = None

        prefs = QApplication.instance().prefs
        prefs.theme_follow_changed.connect(self._update_css)
        prefs.scroll_mode_changed.connect(self._update_scroll_mode)

        logger.debug("[ScoreView] Initialize prefs…")
        self._update_css()
        self._update_scroll_mode()

        logger.debug("[ScoreView] Create WebEngine…")
        self.view = QWebEngineView(self)

        # JS ↔ Python bridge
        logger.debug("[ScoreView] Add access to developper tools…")
        self.devtools = QWebEngineView()
        self.view.page().setDevToolsPage(self.devtools.page())
        QShortcut(QKeySequence("Ctrl+Alt+I"), self.view, activated=self.show_devtools)

        logger.debug("[ScoreView] Create bridge…")
        self.bridge = JsBridge()
        self.bridge.noteClicked.connect(self._on_note_clicked)

        logger.debug("[ScoreView] Create WebChannel…")
        self.channel = QWebChannel(self.view.page())
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        self.view.loadFinished.connect(self._on_page_loaded)

        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
        self.setLayout(layout)

    #def _update_css(self, update_js=False):
    #    logger.debug("[ScoreView] get prefs…")
    #    prefs = QApplication.instance().prefs
    #    self.theme_name = prefs["follow_theme"]
    #    if self.theme != FOLLOW_THEMES.get(self.theme_name, FOLLOW_THEMES["light"]):
    #        self.theme = FOLLOW_THEMES.get(self.theme_name, FOLLOW_THEMES["light"])
    #        self.css_vars = "\n".join(
    #            f"    --{key}: {value};"
    #            for key, value in self.theme.items()
    #        )
    #        if update_js:
    #            js = f"applyFollowTheme({json.dumps(self.theme)});"
    #            self.run_js(js)

    def _update_css(self, update_js=False):
        logger.debug("[ScoreView] get prefs…")
        prefs = QApplication.instance().prefs
        theme_name = prefs["follow_theme"]
        self.scroll_mode = prefs["scroll_mode"]
        self.score_view.run_js(f"setScrollMode('{self.prefs['scroll_mode']}');")

        self.follow_color = prefs["follow_color"]
        logger.debug(f"[ScoreView] theme name: {theme_name}, scroll_mode: {self.scroll_mode}")

        new_theme = FOLLOW_THEMES.get(theme_name, FOLLOW_THEMES["light"])
        logger.debug(f"[ScoreView] new theme: {new_theme}")


        # Verify if theme item values are right. Use of getattr for initialisation
        if new_theme == getattr(self, "theme", None):
            return

        # Update current theme
        self.theme_name = theme_name
        self.theme = new_theme

        # Create CSS variable
        self.css_vars = "\n".join(
            f"    --{key}: {value};"
            for key, value in new_theme.items()
        )
        logger.debug(f"[ScoreView] css_vars: {self.css_vars}")

        # Update theme if page is ready
        # At init, page is not ready so no risk to update but extra flag just in case
        if update_js and self.page_ready:
            js = f"applyFollowTheme({json.dumps(new_theme)});"
            self.run_js(js)

    def _update_css(self):
        logger.debug("[ScoreView] get prefs…")
        prefs = QApplication.instance().prefs
        theme_name = prefs["follow_theme"]
        logger.debug(f"[ScoreView] theme name: {theme_name}")

        new_theme = FOLLOW_THEMES.get(theme_name, FOLLOW_THEMES["light"])
        logger.debug(f"[ScoreView] new theme: {new_theme}")

        # Create CSS variable
        self.css_vars = "\n".join(
            f"    --{key}: {value};"
            for key, value in new_theme.items()
        )
        logger.debug(f"[ScoreView] css_vars: {self.css_vars}")

        # Update theme if page is ready
        # At init, page is not ready so no js call but will be taken into account at load
        if self.page_ready:
            js = f"applyFollowTheme({json.dumps(new_theme)});"
            self.run_js(js)

    def _update_scroll_mode(self):
        prefs = QApplication.instance().prefs
        self.scroll_mode = prefs['scroll_mode']
        
        # Update mode if page is ready
        # At init, page is not ready o no js call but will be taken into account at load
        if self.page_ready:
            self.run_js(f"setScrollMode('{prefs['scroll_mode']}');")

    def apply_preferences(self):
        #self._update_css(update_js=True)
        #self._update_scroll_mode(update_js=True)

        #self.scroll_mode = prefs["scroll_mode"]
        #self.follow_color = prefs["follow_color"]
        pass

    # ---------------------------------------------------------
    # Load SVG generated by abc2svg
    # ---------------------------------------------------------
    def load_svg(self, svg_text: str):
        self.page_ready = False

        html = f"""
<html>
    <head>
        <meta charset="utf-8" />
        <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <style>
        :root {{
            {self.css_vars}
        }}

        .notehit {{
            fill: var(--follow-color);
            fill-opacity: 0;
            cursor: pointer;
        }}
        .notehit.selectedforplay {{
            fill: var(--selectedforplay-color);
            fill-opacity: var(--selectedforplay-opacity);
        }}
        /* Notes in play range */
        .notehit.play-range {{
            fill: var(--play-range-color);
            fill-opacity: var(--play-range-opacity);
        }}
        /* First note in play range */
        .notehit.play-start {{
            fill: var(--play-start-color);
            fill-opacity: var(--play-start-opacity);
        }}

        /* Last note in play range */
        .notehit.play-end {{
            fill: var(--play-end-color);
            fill-opacity: var(--play-end-opacity);
        }}

        .notehit.active {{
            fill: var(--follow-color);
            fill-opacity: var(--follow-opacity);
        }}
        </style>
    </head>
    <body>

        {svg_text}

        <script>
        window.scrollMode = "{self.scroll_mode}";
        let bridge = null;

        new QWebChannel(qt.webChannelTransport, function(channel) {{
            bridge = channel.objects.bridge;
        }});

        function highlightNote(start) {{
            document.querySelectorAll('.notehit.active')
                .forEach(el => el.classList.remove('active'));

            const selector = '.notehit._' + start + '_';

            const svgs = document.querySelectorAll('svg');
            for (const svg of svgs) {{
                const el = svg.querySelector(selector);
                if (el) {{
                    el.classList.add('active');
                    return;
                }}
            }}
        }}

        function scrollToNote(start) {{
            const el = document.querySelector('.notehit._' + start + '_');
            if (!el) return;

            const rect = el.getBoundingClientRect();

            const targetTop = rect.top + window.scrollY - 100;
            const targetLeft = rect.left + window.scrollX - 100;

            window.scrollTo({{
                top: targetTop,
                left: targetLeft,
                behavior: 'smooth'
            }});
        }}

        function highlightNotes(activeIDs) {{
            // reset
            document.querySelectorAll('.notehit.active')
                .forEach(el => el.classList.remove('active'));

            // activate
            for (const id of activeIDs) {{
                const el = document.querySelector('.notehit._' + id + '_');
                if (el) el.classList.add('active');
                if (!el) {{
                    console.warn("Highlight failed: no note with id", id);
                }}
            }}

            scrollActiveNotes(activeIDs);
        }}

        function highlightSelection(activeIDs) {{
            // reset selection
            document.querySelectorAll('.notehit.selectedforplay')
                .forEach(el => el.classList.remove('selectedforplay'));

            // add new selection
            for (const id of activeIDs) {{
                const el = document.querySelector('.notehit._' + id + '_');
                if (el) el.classList.add('selectedforplay');
            }}

            scrollActiveNotes(activeIDs);
        }}
        
        function clearSelection() {{
            document.querySelectorAll('.notehit.play-start, .notehit.play-end, .notehit.play-range')
                .forEach(el => {{
                    el.classList.remove('play-start', 'play-end', 'play-range');
                }});
        }}

        function highlightPlayStart(activeIDs) {{
            // Reset start
            document.querySelectorAll('.notehit.play-start')
                .forEach(el => el.classList.remove('play-start'));

            // Add new start
            for (const id of activeIDs) {{
                const el = document.querySelector('.notehit._' + id + '_');
                if (el) el.classList.add('play-start');
            }}

            scrollActiveNotes(activeIDs);
        }}
        
        function highlightPlayEnd(activeIDs) {{
            // Reset End
            document.querySelectorAll('.notehit.play-end')
                .forEach(el => el.classList.remove('play-end'));

            // Add new end
            for (const id of activeIDs) {{
                const el = document.querySelector('.notehit._' + id + '_');
                if (el) el.classList.add('play-end');
            }}

            scrollActiveNotes(activeIDs);
        }}
        
        function highlightPlayRange(activeIDs) {{
            // Reset play selection
            document.querySelectorAll('.notehit.play-range')
                .forEach(el => el.classList.remove('play-range'));

            // End new selection
            for (const id of activeIDs) {{
                const el = document.querySelector('.notehit._' + id + '_');
                if (el) el.classList.add('play-range');
            }}

            //scrollActiveNotes(activeIDs);
        }}

        function getActiveBoundingBox(activeIDs) {{
            let minTop = Infinity, maxBottom = -Infinity;
            let minLeft = Infinity, maxRight = -Infinity;

            for (const id of activeIDs) {{
                const el = document.querySelector('.notehit._' + id + '_');
                if (!el) continue;

                const rect = el.getBoundingClientRect();
                minTop = Math.min(minTop, rect.top);
                maxBottom = Math.max(maxBottom, rect.bottom);
                minLeft = Math.min(minLeft, rect.left);
                maxRight = Math.max(maxRight, rect.right);
            }}

            if (minTop === Infinity) return null;

            return {{ minTop, maxBottom, minLeft, maxRight }};
        }}

        function scrollActiveNotes(activeIDs) {{
            const box = getActiveBoundingBox(activeIDs);
            if (!box) return;

            if (window.scrollMode === "center") {{
                scrollToBoundingBoxCentered(box);
            }} else {{
                scrollToBoundingBoxMinimal(box);
            }}
        }}

        function scrollToBoundingBoxCentered(box) {{
            // const targetTop = box.minTop + window.scrollY - 80;
            // const targetLeft = box.minLeft + window.scrollX - 80;
            const targetTop = (box.minTop + box.maxBottom) / 2 + window.scrollY - window.innerHeight / 2;
            const targetLeft = (box.minLeft + box.maxRight) / 2 + window.scrollX - window.innerWidth / 2;

            window.scrollTo({{
                top: targetTop,
                left: targetLeft,
                behavior: 'smooth'
            }});
        }}

        function scrollToBoundingBoxMinimal(box) {{
            const margin = 50;

            let targetTop = window.scrollY;
            let targetLeft = window.scrollX;

            // Vertical
            if (box.minTop < margin) {{
                targetTop = box.minTop + window.scrollY - margin;
            }} else if (box.maxBottom > window.innerHeight - margin) {{
                targetTop = box.maxBottom + window.scrollY - window.innerHeight + margin;
            }}

            // Horizontal
            if (box.minLeft < margin) {{
                targetLeft = box.minLeft + window.scrollX - margin;
            }} else if (box.maxRight > window.innerWidth - margin) {{
                targetLeft = box.maxRight + window.scrollX - window.innerWidth + margin;
            }}

            window.scrollTo({{
                top: targetTop,
                left: targetLeft,
                behavior: 'smooth'
            }});
        }}

        document.addEventListener('click', function(e) {{
            if (e.target.classList.contains('notehit')) {{
                const cls = [...e.target.classList].find(c => c.startsWith('_') && c.endsWith('_'));
                const start = cls.slice(1, -1);
                if (bridge) bridge.onNoteClicked(start);
            }}
        }});

        function applyFollowTheme(theme) {{
            for (const key in theme) {{
                document.documentElement.style.setProperty(`--${{key}}`, theme[key]);
            }}
        }}
        function setScrollMode(mode) {{
            window.scrollMode = mode;
        }}
        </script>

    </body>
</html>
        """

        self.view.setHtml(html, QUrl("about:blank"))

    # ---------------------------------------------------------
    # Python → JS
    # ---------------------------------------------------------
    def highlight_from_editor_position(self, start: int):
        #if self.page_ready:
        #    self.view.page().runJavaScript(f"highlightNote({start});")
        logger.debug(f"[ScoreView] Highlight request: {start}, page_ready: {self.page_ready}")
        if not self.page_ready:
            logger.debug("[ScoreView] Page not ready, storing pending highlight")
            self.pending_highlight = start
            return
        self.pending_highlight = None
        self.run_js(f"highlightNote({start});")

    def run_js(self, script: str):
        logger.debug(f"[ScoreView] Running JS: {script}")
        if self.page_ready:
            self.view.page().runJavaScript(script)

    def run_js(self, script):
        logger.debug(f"[ScoreView] Running JS: {script}")
        if not self.page_ready:
            logger.warning("[ScoreView] JS ignored: page not ready")
            return
        self.view.page().runJavaScript(script, self._js_callback)

    # ---------------------------------------------------------
    # JS → Python
    # ---------------------------------------------------------
    def _js_callback(self, result):
        if result is None:
            logger.debug("[ScoreView] JS executed")
        else:
            logger.debug(f"[ScoreView] JS returned: {result}")

    def _on_note_clicked(self, start: str):
        if self.on_note_clicked:
            try:
                start = int(start)
            except ValueError:
                return
            self.on_note_clicked(start)

    def _on_page_loaded(self, ok: bool):
        self.page_ready = ok
        logger.debug(f"[ScoreView] Page loaded: {ok}")
        #if self.pending_highlight is not None:
        #    print("Running pending highlight:", self.pending_highlight)
        #    self.run_js(f"highlightNote({self.pending_highlight});")
        #    self.pending_highlight = None
        if self.page_loaded:
            self.page_loaded()

    def get_svg_html(self, callback):
        self.view.page().toHtml(callback)

    def show_devtools(self):
        self.devtools.show()

    def export_tune_to_pdf(self, file):
        self.view.page().printToPdf(file)
