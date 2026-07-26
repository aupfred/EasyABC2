# easyabc2/engines/abc_engine.py
import quickjs
from pathlib import Path
import json

from easyabc2.utils.logging_utils import logger
from easyabc2 import _

logger.debug("[ABC2SVGEngine] Importing…")

class ABC2SVGEngine:
    def __init__(self, preferences):
        self.preferences = preferences
        self.fallback_svg = self._make_fallback_svg()

        self.base = Path(self.preferences["abc2svg_scripts_path"])
        logger.debug(f"[ABC2SVGEngine] abc2svg path: {self.base}")
        if not self.base.exists():
            self.valid = False
            return
        self.valid = True

        self.ctx = quickjs.Context()

        self.svg_buffer = ""

        # Python Callbacks
        self.ctx.add_callable("py_img_out", self._img_out)
        self.ctx.add_callable("py_errmsg", self._errmsg)
        self.ctx.add_callable("py_read_file", self._read_file)

        # Load abc2svg module
        # Todo: make it more generic to avoid to list each module
        modules = [
            "grid-1.js", "grid2-1.js", "grid3-1.js",
            "break-1.js", "page-1.js", "clip-1.js",
            "equalbars-1.js", "roman-1.js"
        ]
        for m in modules:
            self.ctx.eval((self.base / m).read_text(encoding="utf-8"))

        # Load abc2svg core
        self.ctx.eval((self.base / "abc2svg-1.js").read_text(encoding="utf-8"))

        # Prepare Abc object and render_abc function
        self.ctx.eval("""
        var user = {
            img_out: function(s){ py_img_out(s); },
            errmsg: function(msg, line, col){ py_errmsg(msg, line, col); },
            read_file: function(name){ return py_read_file(name); },
            page_format: true,

            anno_start: function(type, start, stop, x, y, w, h, s){},

            anno_stop: function(type, start, stop, x, y, w, h){
                if (type !== "note" && type !== "rest") return;

                abc.out_svg(`<rect class="notehit _${start}_" x="`);
                abc.out_sxsy(x, `" y="`, y);
                abc.out_svg(`" width="${w.toFixed(2)}" height="${abc.sh(h).toFixed(2)}"`);
                abc.out_svg(` fill="red" fill-opacity="0" pointer-events="all"/>\n`);
            }
        };

        function render_abc(src) {
            abc = new abc2svg.Abc(user);
            abc.tosvg("tune.abc", src);
        }
        """)

    # -----------------------------------------
    # Fallback SVG (internationalized)
    # -----------------------------------------
    def _make_fallback_svg(self):
        return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="600" height="140">
  <rect width="100%" height="100%" fill="#f8f8f8"/>
  <text x="50%" y="45%" font-size="20" text-anchor="middle" fill="#444">
    {_("abc2svg is not configured.")}
  </text>
  <text x="50%" y="70%" font-size="14" text-anchor="middle" fill="#666">
    {_("Please set the abc2svg scripts path in Preferences → Paths.")}
  </text>
</svg>
"""

    # --- Callbacks QuickJS ---
    def _img_out(self, svg):
        self.svg_buffer += svg

    def _errmsg(self, msg, line=None, col=None):
        logger.error(f"[ABC2SVGEngine] ABC error: {msg}")

    def _read_file(self, name):
        return None

    # --- Public API ---
    def abc_to_svg(self, abc_text):
        if not self.valid:
            return self.fallback_svg

        self.svg_buffer = ""
        try:
            self.ctx.eval(f"render_abc({json.dumps(abc_text)})")
        except Exception as e:
            logger.error(f"[ABC2SVGEngine] JS error: {e}")
            return ""
        return self.svg_buffer
