from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from PySide6.QtCore import QUrl

from easyabc2.models.abc_assist.abc_context import *
from easyabc2.models.abc_assist.tune_actions import *
from easyabc2.models.abc_assist.tune_elements import *

class AbcAssistPanel(QWidget):
    def __init__(self, parent, editor, prefs, cwd):
        super().__init__(parent)

        self.editor_adapter = editor      # QtEditorAdapter
        self.editor = editor.editor       # QPlainTextEdit
        self.prefs = prefs                # settings
        self.cwd = cwd                    # ABC path

        # --- ABC ---
        self.elements = AbcStructure.generate_abc_elements(self.cwd)
        self.actions_handlers = AbcActionHandlers(self.elements, self.cwd)

        # --- UI ---
        layout = QVBoxLayout(self)
        self.browser = QTextBrowser(self)
        layout.addWidget(self.browser)

        # HTML links
        self.browser.setOpenLinks(False)
        self.browser.anchorClicked.connect(self.on_link_clicked)

        # current context
        self.context = None

    # ---------------------------------------------------------
    # Panel update
    # ---------------------------------------------------------
    def update_assist(self):
        """Update HTML and AbcContext."""
        #try:
        self.context = AbcContext(self.editor_adapter, self.prefs,
                                  on_invalidate=self.update_assist)

        element, match = self.get_current_element()

        if element:
            self.context.current_element = element
            self.context.set_current_match(match, element.tune_scope)
            element = element.get_inner_element(self.context)

        html = "<html><body>"
        if element:
            html += element.get_description_html(self.context)
            action_html = self.actions_handlers.get_action_handler(element).get_action_html(self.context)
            if action_html:
                html += "<br>" + action_html
        html += "</body></html>"

        self.browser.setHtml(html)

        #except Exception as e:
        #    print("Error in update_assist:", e)

    # ---------------------------------------------------------
    # Find ABC element at cursor position
    # ---------------------------------------------------------
    def get_current_element(self):
        for element in self.elements:
            m = element.matches(self.context)
            if m:
                return element, m
        return None, None

    # ---------------------------------------------------------
    # Management of HTML interactions
    # ---------------------------------------------------------
    def on_link_clicked(self, url: QUrl):
        href = url.toString()

        # external link?
        if href.startswith("http"):
            import webbrowser
            webbrowser.open(href)
            return

        # internal = action ABC
        parts = href.split("?", 1)
        action_name = parts[0]
        params = {}

        if len(parts) > 1:
            from urllib.parse import parse_qsl
            params = dict(parse_qsl(parts[1], keep_blank_values=True))

        handler = self.actions_handlers.get_action_handler(self.context.current_element)
        action = handler.get_action(action_name)

        if action:
            action.execute(self.context, params)
            self.editor.setFocus()
