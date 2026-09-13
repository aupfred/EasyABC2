# easyabc2/ui/score_view2.py

import re
import base64
import platform

from PySide6.QtCore import Qt, QByteArray, QRectF, QObject
from PySide6.QtWidgets import (QApplication, QGraphicsView, QGraphicsRectItem,
                               QGraphicsScene, QVBoxLayout, QWidget)
from PySide6.QtGui import (QPainter, QFontDatabase, QColor, QPen, QBrush, QPdfWriter, QPageSize,
                           QNativeGestureEvent, QWheelEvent)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QGraphicsSvgItem

from easyabc2.utils.themes import FOLLOW_THEMES
from easyabc2.utils.logging_utils import logger

PRIORITY_ORDER = ["active", "play-start", "play-end", "play-range"]

logger.debug("[ScoreView2] Importing ScoreView…")

class TrackpadGestureFilter(QObject):
    """Intercepts and processes trackpad gestures directly from the QGraphicsView's viewport."""
    def __init__(self, view: QGraphicsView):
        super().__init__(view)
        self.view = view

    def eventFilter(self, obj, event):
        # 1. NATIVE MAC TRACKPAD PINCH
        if (
            isinstance(event, QNativeGestureEvent)
            and event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture
        ):
            scale_factor = event.value()
            if scale_factor > 0:
                zoom_step = 1.0 + scale_factor
                self.view.scale(zoom_step, zoom_step)
            return True

        # 2. MOUSE WHEEL + CTRL (Mac, Win, Linux) & TRACKPAD PINCH (Win, Linux)
        elif isinstance(event, QWheelEvent):
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                angle_delta = event.angleDelta().y()
                zoom_factor = 1.1 if angle_delta > 0 else 0.9
                self.view.scale(zoom_factor, zoom_factor)
                return True

        return super().eventFilter(obj, event)

class TrackpadGestureFilter(QObject):
    """Intercepts and processes trackpad gestures directly from the QGraphicsView's viewport."""
    def __init__(self, view: QGraphicsView):
        super().__init__(view)
        self.view = view
        
        # Définition des limites de zoom
        self.MIN_ZOOM = 0.5   # 50%
        self.MAX_ZOOM = 5.0   # 500%

    def eventFilter(self, obj, event):
        zoom_factor = 1.0

        # 1. NATIVE MAC TRACKPAD PINCH
        if (
            isinstance(event, QNativeGestureEvent)
            and event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture
        ):
            zoom_factor = 1.0 + event.value()

        # 2. (MOUSE WHEEL or Trackpad) + CTRL (Mac, Win, Linux) & TRACKPAD PINCH (Win, Linux)
        elif isinstance(event, QWheelEvent):
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Value of the wheel whether up (positive) or down (negative)
                angle_delta = event.angleDelta().y()
                
                if angle_delta != 0:
                    # The more the move is quick the biggest angle_delta is.
                    # Calculate based on this trying to have a smooth zoom factor.
                    # the value of 1200.0 controls the speed, could change to 800 to make it quicker or 1500 to reduce speed.
                    zoom_factor = 2.0 ** (angle_delta / 1200.0)

        # Apply zoom while staying in the limit min/max
        if zoom_factor != 1.0:
            current_zoom = self.view.transform().m11()
            new_zoom = current_zoom * zoom_factor

            if new_zoom < self.MIN_ZOOM:
                zoom_factor = self.MIN_ZOOM / current_zoom
            elif new_zoom > self.MAX_ZOOM:
                zoom_factor = self.MAX_ZOOM / current_zoom

            self.view.scale(zoom_factor, zoom_factor)
            return True

        return super().eventFilter(obj, event)

class ScoreView(QWidget):
    # Signals / Callback to interface to document tab
    on_note_clicked = None  # Callback when note clicked (ex: lambda note_id: ...)
    page_loaded = None       # Callback when page loaded (ex: lambda: ...)

    @property
    def prefs(self):
        return QApplication.instance().prefs

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)

        # Configure Scene and View
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)

        # Activate gesture on trackpad anchors
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # FIX: Install the event filter on the viewport of the QGraphicsView
        self.gesture_filter = TrackpadGestureFilter(self.view)
        self.view.viewport().installEventFilter(self.gesture_filter)

        # Layout to add the view
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        # Initial variables for svg and highlighted notes
        self.svg_renderer = None
        self.svg_item = None
        self.interactive_notes = {}  # {note_id: QGraphicsRectItem}
        self.all_note_ids = []       # All note in the order
        self.active_note_ids = []    # Notes currently active
        self.system_positions = []
        self.playback_index = 0
        #self.currently_highlighted_id = None
        self.real_font_name = "abc2svg"  # Default font name. Todo add the complete font.
        self._available_fonts = None  # Cache pour les polices disponibles

        # Dictionnary to manage notes highlighted by type
        self.highlighted_notes = {
            "active": set(),     # Active note either follow playback or selection in editor (highest priority)
            "play-start": set(), # Beginning of play
            "play-end": set(),   # End of play
            "play-range": set(), # Notes in the range to play
        }

        # Load preferences
        self.theme = FOLLOW_THEMES.get(self.prefs["follow_theme"], FOLLOW_THEMES["light"]) if self.prefs else FOLLOW_THEMES["light"]
        self.follow_color = QColor(self.theme["follow-color"])
        self.follow_color.setAlphaF(float(self.theme["follow-opacity"]))

        # Connect to preferences signals
        if self.prefs:
            self.prefs.theme_follow_changed.connect(self._update_follow_theme)
            self.prefs.scroll_mode_changed.connect(self._update_scroll_mode)

        # Connect mouse signal
        self.view.mousePressEvent = self._custom_mouse_press_event

    def _update_follow_theme(self):
        """Update the color related to follow"""
        if self.prefs:
            self.theme = FOLLOW_THEMES.get(self.prefs["follow_theme"], FOLLOW_THEMES["light"])
            self.follow_color = QColor(self.theme["follow-color"])
            self.follow_color.setAlphaF(float(self.theme["follow-opacity"]))

    def _update_follow_theme(self):
        """Update the color related to follow"""
        if not self.prefs:
            logger.error("[ScoreView2] No prefs available")
            return

        self.theme = FOLLOW_THEMES.get(self.prefs["follow_theme"], FOLLOW_THEMES["light"])

        # Apply new colors to the highlighted notes
        for note_type in PRIORITY_ORDER:
            if self.highlighted_notes[note_type]:
                color_key = f"{note_type}-color"
                opacity_key = f"{note_type}-opacity"
                if color_key in self.theme and opacity_key in self.theme:
                    color = QColor(self.theme[color_key])
                    color.setAlphaF(float(self.theme[opacity_key]))
                    self._highlight_notes_by_type(
                        list(map(int, self.highlighted_notes[note_type])),
                        note_type,
                        color
                    )

    def _update_scroll_mode(self):
        """Update the scrolling mode when playback is on"""
        if self.prefs:
            self.scroll_mode = self.prefs["scroll_mode"]
            if hasattr(self, 'view'):
                pass

    def _custom_mouse_press_event(self, event):
        """Manage clic on notes."""
        if event.button() == Qt.LeftButton:
            target_item = self.view.itemAt(event.position().toPoint())
            if isinstance(target_item, QGraphicsRectItem):
                note_id = target_item.data(0)
                if self.on_note_clicked:
                    self.on_note_clicked(int(note_id))
                return  # stop here no drag needed
        # forward other case
        super(QGraphicsView, self.view).mousePressEvent(event)

    def load_svg(self, svg_text: str):
        """Load SVG and create the area where it is possible to clic"""
        # Initialise view and highlights
        self.scene.clear()
        self.interactive_notes.clear()
        self.all_note_ids.clear()
        self.active_note_ids.clear()
        self.system_positions = []
        self.currently_highlighted_id = None
        self.playback_index = 0

        # Clean up svg
        svg_text = re.sub(r'<div[^>]*>', '', svg_text).replace('</div>', '')
        # Extract SMUFL font if embedded
        self._extract_font(svg_text)
        
        # Text balises with multiple coordinates splitted in individual ones (to comply to svg capabilities of the widget)
        logger.info("[ScoreView2] Process the split of text balises...")
        processed_content = self._split_multi_coordinate_text_tags(svg_text)
        
        # Extract css style
        style_match = re.search(r'(<style>.*?</style>)', processed_content, re.DOTALL)
        global_style = style_match.group(1) if style_match else ""
        global_style = global_style.replace('music', f'"{self.real_font_name}"').replace('Music', f'"{self.real_font_name}"')

        # Extract multiple svg to build a single one
        svg_blocks = re.findall(r'<svg([^>]*)>(.*?)</svg>', processed_content, re.DOTALL)
        logger.info(f"[ScoreView2] {len(svg_blocks)} systems/groups extracted.")

        master_width = 794.0
        current_y = 0.0
        combined_groups = []

        # Main loop on each system/group
        for attrs_str, body in svg_blocks:
            h_match = re.search(r'height=["\']([\d\.]+)(?:px)?["\']', attrs_str)
            h = float(h_match.group(1)) if h_match else 120.0
            
            w_match = re.search(r'width=["\']([\d\.]+)(?:px)?["\']', attrs_str)
            if w_match: 
                master_width = max(master_width, float(w_match.group(1)))

            # Define area according to note definition
            rect_matches = re.findall(
                r'<rect\s+class=["\']notehit\s+_(?P<id>\d+)_["\']\s+x=["\'](?P<x>[\d\.-]+)["\']\s+y=["\'](?P<y>[\d\.-]+)["\']\s+width=["\'](?P<width>[\d\.-]+)["\']\s+height=["\'](?P<height>[\d\.-]+)["\']', 
                body
            )
            
            for note_id, rx, ry, rw, rh in rect_matches:
                abs_x = float(rx)
                abs_y = float(ry) + current_y
                abs_w = float(rw)
                abs_h = float(rh)
                
                # Create interaction
                rect_item = QGraphicsRectItem(abs_x, abs_y, abs_w, abs_h)
                rect_item.setPen(QPen(Qt.NoPen))
                rect_item.setBrush(QBrush(Qt.NoBrush))
                rect_item.setData(0, note_id)
                rect_item.setFlag(QGraphicsRectItem.ItemIsSelectable, True) # IMPORTANT enforce object can be selected
                rect_item.setZValue(10) # Ensure area is in the front
                rect_item.setCursor(Qt.CursorShape.PointingHandCursor) #ArrowCursor)
                
                self.interactive_notes[str(note_id)] = rect_item
                
                # Add the id to the list
                if note_id not in self.all_note_ids:
                    self.all_note_ids.append(note_id)

            # Save Y position and height before shifting
            # Add a 15px space: Todo verify if it can be removed
            self.system_positions.append({'top': current_y, 'bottom': current_y + h + 15.0})

            # Prepare integration in <g> shifted vertically
            class_match = re.search(r'class=["\']([^"\']+)["\']', attrs_str)
            class_attr = f' class="{class_match.group(1)}"' if class_match else ""
            
            group_tag = f'<g transform="translate(0, {current_y})"{class_attr}>'
            combined_groups.append(f"{group_tag}\n{body}\n</g>")
            
            # Next position
            current_y += h + 15.0

        # Join all block in one single SVG
        unified_svg = [
            f'<svg xmlns="http://w3.org" version="1.1" width="{master_width}px" height="{current_y}px" viewBox="0 0 {master_width} {current_y}" fill="currentColor" stroke-width=".7">',
            global_style,
            "\n".join(combined_groups),
            '</svg>'
        ]

        # Apply CSS style now that svg is complete
        unified_svg_str = "\n".join(unified_svg)
        unified_svg_str = self._apply_css_styles(unified_svg_str)
        # Build SVG to render
        svg_data = QByteArray(unified_svg_str.encode('utf-8'))

        self.svg_renderer = QSvgRenderer(svg_data)
        
        # Add SVG at the back
        self.svg_item = QGraphicsSvgItem()
        self.svg_item.setSharedRenderer(self.svg_renderer)
        self.svg_item.setFlags(QGraphicsSvgItem.ItemUsesExtendedStyleOption)
        self.svg_item.setZValue(1) # Keep Svg at the back
        self.scene.addItem(self.svg_item)
        
        # Add the area in the front
        for rect_item in self.interactive_notes.values():
            self.scene.addItem(rect_item)
        
        # Active note is by default the complete list
        self.active_note_ids = list(self.all_note_ids)
        
        # Adjust the zoom to the content
        self.scene.setSceneRect(0, 0, master_width, current_y)
        self.view.resetTransform()
        #self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
        # Zoom on first system
        if self.system_positions:
            first_system = self.system_positions[0]
            # Hight of first system
            first_system_height = first_system['bottom'] - first_system['top']
            
            # Apply the fit in view with small margin
            self.view.fitInView(
                0, 
                0, 
                master_width, 
                first_system_height + 20, 
                Qt.KeepAspectRatio
            )
        else:
            # Just in case adapt to view everything
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

        logger.info(f"[ScoreView2] {len(self.interactive_notes)} notes configured. {len(self.system_positions)} systems.")

        if self.page_loaded:
            self.page_loaded()
        
        return unified_svg_str
        
    def _extract_font(self, svg_content: str):
        """Extract and loads the SMUFL font."""
        font_match = re.search(r'src:\s*url\s*\(\s*["\']data:[^;]+;base64,([^"\']+)["\']\)', svg_content)
        if font_match:
            try:
                font_data = base64.b64decode(font_match.group(1).strip())
                font_id = QFontDatabase.addApplicationFontFromData(QByteArray(font_data))
                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families:
                        self.real_font_name = families[0]
                        logger.info(f"[ScoreView2] SMUFL font registered: '{self.real_font_name}'")
            except Exception as e:
                logger.warning(f"[ScoreView2] Unable to load font : {e}")

    def _split_multi_coordinate_text_tags(self, svg_content: str) -> str:
        """
        Split <text> balises with multiple coordinates in individual balises.
        Note: Keep all attributes and styles. Later on _apply_css_styles will manage.
        """
        pattern = r'(<text\s+([^>]*?)>(.*?)</text>)'

        def replacer(match):
            full_tag = match.group(1)
            attrs = match.group(2)
            text_data = match.group(3)

            # Extract x & y coordinates
            x_match = re.search(r'x=["\']([\d\.,\.-]+)["\']', attrs)
            y_match = re.search(r'y=["\']([\d\.,\.-]+)["\']', attrs)

            # return unchanged balises if only one coordinate or none
            if not x_match or not y_match or ',' not in x_match.group(1):
                return full_tag

            # Extract list of coordinates
            x_list = x_match.group(1).split(',')
            y_list = y_match.group(1).split(',')
            characters = list(text_data)  # convert in characters

            # Limit number of iterations
            count = min(len(x_list), len(y_list), len(characters))

            # Clean attributes of coordinates
            clean_attrs = re.sub(r'\bx=["\'][^"\']*["\']', '', attrs)
            clean_attrs = re.sub(r'\by=["\'][^"\']*["\']', '', clean_attrs)
            clean_attrs = re.sub(r'\s+', ' ', clean_attrs).strip()

            # Create individual balises
            individual_tags = []
            for i in range(count):
                individual_tags.append(
                    f'<text x="{x_list[i].strip()}" y="{y_list[i].strip()}" {clean_attrs}>{characters[i]}</text>'
                )

            return "\n".join(individual_tags)

        return re.sub(pattern, replacer, svg_content, flags=re.DOTALL)

    def highlight_note(self, note_id: int, color: QColor = None):
        """
        Highlight note according to the color.
        Args:
            note_id: ID of the note to highlight.
            color: Highlight color (optional). If none, follow the one from follow-color of the theme.
        Todo:
            manage multiple ids to be highlighted
        """
        note_key = str(note_id)
        if self.currently_highlighted_id and self.currently_highlighted_id in self.interactive_notes:
            old_rect = self.interactive_notes[self.currently_highlighted_id]
            old_rect.setBrush(QBrush(Qt.NoBrush))
            old_rect.setPen(QPen(Qt.NoPen))

        if note_key in self.interactive_notes:
            rect_item = self.interactive_notes[note_key]
            if color is None:
                color = self.follow_color 
            #highlight_color = QColor(255, 215, 0, 160)  # Yellow with mid opacity
            rect_item.setBrush(QBrush(color))
            rect_item.setPen(QPen(color.darker(120),1)) #QColor(255, 140, 0), 1))
            self.currently_highlighted_id = note_key
            self.view.ensureVisible(rect_item, 50, 50)

    def clear_highlights(self):
        """Remove highlights"""
        for rect in self.interactive_notes.values():
            rect.setBrush(QBrush(Qt.NoBrush))
            rect.setPen(QPen(Qt.NoPen))
        self.currently_highlighted_id = None

    def _highlight_notes_by_type(self, note_ids: list[int], note_type: str, color: QColor):
        """
        Highlight notes according to the type following the priorities.
        Args:
            note_ids: Liste of notes IDs to highlight.
            note_type: Type of highlight ("active", "play-range", "play-start", "play-end").
            color: Color to apply.
        """
        self._clear_highlights_by_type(note_type)

        for note_id in note_ids:
            note_key = str(note_id)
            if note_key in self.interactive_notes:
                rect_item = self.interactive_notes[note_key]

                # Verify priority
                is_highlighted_by_higher_priority = any(
                    note_key in self.highlighted_notes[priority_type]
                    for priority_type in PRIORITY_ORDER[:PRIORITY_ORDER.index(note_type)]
                )

                if not is_highlighted_by_higher_priority:
                    rect_item.setBrush(QBrush(color))
                    rect_item.setPen(QPen(color.darker(120), 1))

                # Add note to type in any case
                self.highlighted_notes[note_type].add(note_key)

    def _clear_highlights_by_type(self, note_type: str):
        """
        Remove highlight of a type and apply the one of lower priority if applicable.
        Args:
            note_type: Type of highlight to remove.
        """
        notes_to_clear = list(self.highlighted_notes[note_type])

        self.highlighted_notes[note_type].clear()

        for note_key in notes_to_clear:
            if note_key in self.interactive_notes:
                rect_item = self.interactive_notes[note_key]

                new_type = None
                for priority_type in PRIORITY_ORDER:
                    if note_key in self.highlighted_notes[priority_type]:
                        new_type = priority_type
                        break

                if new_type:
                    color_key = f"{new_type}-color"
                    opacity_key = f"{new_type}-opacity"
                    if color_key in self.theme and opacity_key in self.theme:
                        color = QColor(self.theme[color_key])
                        color.setAlphaF(float(self.theme[opacity_key]))
                        rect_item.setBrush(QBrush(color))
                        rect_item.setPen(QPen(color.darker(120), 1))
                else:
                    rect_item.setBrush(QBrush(Qt.NoBrush))
                    rect_item.setPen(QPen(Qt.NoPen))

    def clear_all_highlights(self):
        """Clear all type of highlights."""
        for rect in self.interactive_notes.values():
            rect.setBrush(QBrush(Qt.NoBrush))
            rect.setPen(QPen(Qt.NoPen))
        for note_type in self.highlighted_notes:
            self.highlighted_notes[note_type].clear()

    def highlight_notes(self, note_ids: list[int], color: QColor = None):
        """
        Highlight active notes (the one related to editor interaction or follow).
        Args:
            note_ids: Notes to highlight.
            color: Color to apply if any.
        """
        if color is None:
            color = QColor(self.theme["follow-color"])
            color.setAlphaF(float(self.theme["follow-opacity"]))
        self._highlight_notes_by_type(note_ids, "active", color)

    def highlight_play_range(self, note_ids: list[int], color: QColor = None):
        """
        Highlight the playback range.
        Args:
            note_ids: Notes to highlight.
            color: Color to apply if any.
        """
        if color is None:
            color = QColor(self.theme["play-range-color"])
            color.setAlphaF(float(self.theme["play-range-opacity"]))
        self._highlight_notes_by_type(note_ids, "play-range", color)

    def highlight_play_start(self, note_ids: list[int], color: QColor = None):
        """
        Highlight start of playback.
        Args:
            note_ids: Notes to highlight.
            color: Color to apply if any.
        """
        if color is None:
            color = QColor(self.theme["play-start-color"])
            color.setAlphaF(float(self.theme["play-start-opacity"]))
        self._highlight_notes_by_type(note_ids, "play-start", color)

    def highlight_play_end(self, note_ids: list[int], color: QColor = None):
        """
        Highlight end of playback.
        Args:
            note_ids: Notes to highlight.
            color: Color to apply if any.
        """
        if color is None:
            color = QColor(self.theme["play-end-color"])
            color.setAlphaF(float(self.theme["play-end-opacity"]))
        self._highlight_notes_by_type(note_ids, "play-end", color)

    def clear_selection(self):
        """Remove highlight of following types (play-range, play-start, play-end)."""
        self._clear_highlights_by_type("play-range")
        self._clear_highlights_by_type("play-start")
        self._clear_highlights_by_type("play-end")

    def run_js(self, script: str):
        """
        Temporary function during transition.
        """
        if not script:
            return

        # highlightNote(123)
        if "highlightNote(" in script:
            match = re.search(r'highlightNote\((\d+)\)', script)
            if match:
                note_id = int(match.group(1))
                self.highlight_notes([note_id])

        # highlightNotes([123,456,789])
        elif "highlightNotes([" in script:
            match = re.search(r'highlightNotes\(\[(.*?)\]\)', script)
            if match:
                note_ids_str = match.group(1)
                if note_ids_str.strip():
                    note_ids = [int(id.strip()) for id in note_ids_str.split(',') if id.strip()]
                    self.highlight_notes(note_ids)

        # clearSelection()
        elif "clearSelection()" in script:
            self.clear_selection()

        # highlightPlayRange([123,456])
        elif "highlightPlayRange([" in script:
            match = re.search(r'highlightPlayRange\(\[(.*?)\]\)', script)
            if match:
                note_ids_str = match.group(1)
                if note_ids_str.strip():
                    note_ids = [int(id.strip()) for id in note_ids_str.split(',') if id.strip()]
                    self.highlight_play_range(note_ids)

        # highlightPlayStart([123])
        elif "highlightPlayStart([" in script:
            match = re.search(r'highlightPlayStart\(\[(.*?)\]\)', script)
            if match:
                note_ids_str = match.group(1)
                if note_ids_str.strip():
                    note_ids = [int(id.strip()) for id in note_ids_str.split(',') if id.strip()]
                    self.highlight_play_start(note_ids)

        # highlightPlayEnd([123])
        elif "highlightPlayEnd([" in script:
            match = re.search(r'highlightPlayEnd\(\[(.*?)\]\)', script)
            if match:
                note_ids_str = match.group(1)
                if note_ids_str.strip():
                    note_ids = [int(id.strip()) for id in note_ids_str.split(',') if id.strip()]
                    self.highlight_play_end(note_ids)

    def highlight_from_editor_position(self, start: int):
        #Todo verify if still needed
        logger.debug(f"[ScoreView] Highlight request: {start}, page_ready: {self.page_ready}")

    def export_tune_to_pdf(self, file):
        #self.view.page().printToPdf(file)
        pdf_writer = QPdfWriter(file)
        pdf_writer.setPageSize(QPageSize.A4)
        painter = QPainter(pdf_writer)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.scene.sceneRect()
        self.scene.render(painter, QRectF(0, 0, pdf_writer.width(), pdf_writer.height()), rect)
        painter.end()

    def _apply_css_styles(self, svg_content: str) -> str:
        """
        Apply explicitly CSS styles to <g>, <text>, <tspan>.
        Split property 'font' in individual properties.
        """
        style_matches = re.findall(r'<style>(.*?)</style>', svg_content, re.DOTALL)
        if not style_matches:
            return svg_content

        all_css_rules = "\n".join(style_matches)

        # Parse CSS:
        # - Class (ex: .f20 { ... })
        # - Complex rules (ex: .f23 text,tspan { ... })
        class_styles = {}  # {class_name: {'*': [{prop: value}, ...]}}
        tag_styles = {}    # {tag_name: {class_name: [{prop: value}, ...]}}
        font_faces = {}     # {font_family: base64_data}

        for rule in all_css_rules.split('}'):
            if not rule.strip():
                continue

            parts = rule.split('{', 1)
            if len(parts) != 2:
                continue
            selector = parts[0].strip()
            properties = parts[1].strip()

            if selector.lower().startswith('@font-face'):
                font_family_match = re.search(r'font-family:\s*["\']([^"\']+)["\']', properties, re.IGNORECASE)
                src_match = re.search(r'src:\s*url\s*\(\s*["\']data:application/octet-stream;base64,([^"\']+)["\']', properties, re.IGNORECASE)
                if font_family_match and src_match:
                    font_family = font_family_match.group(1)
                    font_data_b64 = src_match.group(1)
                    font_faces[font_family] = font_data_b64
                continue

            # Build dictionary of CSS properties {prop: value}
            props_dict = {}
            for prop in properties.split(';'):
                prop = prop.strip()
                if not prop:
                    continue
                prop_parts = prop.split(':', 1)
                if len(prop_parts) != 2:
                    continue
                prop_name = prop_parts[0].strip().lower()
                prop_value = prop_parts[1].strip()

                # Split 'font' in individual properties
                if prop_name == 'font':
                    font_parts = prop_value.split()
                    for part in font_parts:
                        if part in ['bold', 'bolder']:
                            props_dict['font-weight'] = part
                        elif part in ['italic', 'oblique']:
                            props_dict['font-style'] = part
                        elif part in ['normal']:
                            props_dict['font-weight'] = part
                            props_dict['font-style'] = part
                        else:
                            font_size_match = re.match(r'([\d.]+)(px|pt|em|%)?', part)
                            if font_size_match:
                                props_dict['font-size'] = f"{font_size_match.group(1)}{font_size_match.group(2) or 'px'}"
                            else:
                                props_dict['font-family'] = part
                else:
                    props_dict[prop_name] = prop_value

            # Manage class definition (ex: .f20)
            if selector.startswith('.'):
                class_name = selector[1:].split()[0]
                if ' ' in selector:
                    # (ex: .f23 text,tspan)
                    tags = selector.split()[1].split(',')
                    for tag in tags:
                        tag = tag.strip()
                        if tag not in tag_styles:
                            tag_styles[tag] = {}
                        if class_name not in tag_styles[tag]:
                            tag_styles[tag][class_name] = []
                        tag_styles[tag][class_name].append(props_dict)
                else:
                    # (ex: .f20)
                    if class_name not in class_styles:
                        class_styles[class_name] = {}
                    if '*' not in class_styles[class_name]:
                        class_styles[class_name]['*'] = []
                    class_styles[class_name]['*'].append(props_dict)

        logger.debug(f"[ScoreView2] class_styles: {class_styles}")
        logger.debug(f"[ScoreView2] tag_styles: {tag_styles}")

        self.font_faces = font_faces

        def merge_css_properties(*props_dicts: list[dict]) -> dict:
            """Merge dictionnaries (last value is kept)."""
            merged = {}
            for props in props_dicts:
                merged.update(props)
            return merged

        def css_dict_to_svg_attrs(props_dict: dict) -> str:
            """Convert property to SVG attributs."""
            attrs = []
            seen_props = set()

            for prop_name, prop_value in props_dict.items():
                if prop_name in seen_props:
                    continue  # Avoid to double property
                seen_props.add(prop_name)

                if prop_name == 'font-size':
                    attrs.append(f'font-size="{prop_value}"')
                elif prop_name == 'font-family':
                    normalized_font = self._normalize_font_family(prop_value)
                    if normalized_font:
                        attrs.append(f'font-family="{normalized_font}"')
                elif prop_name == 'font-weight':
                    if prop_value in ['bold', 'bolder']:
                        attrs.append('font-weight="bold"')
                    elif prop_value in ['normal', '100', '200', '300', '400']:
                        attrs.append('font-weight="normal"')
                    else:
                        attrs.append(f'font-weight="{prop_value}"')
                elif prop_name == 'font-style':
                    if prop_value in ['italic', 'oblique']:
                        attrs.append('font-style="italic"')
                    elif prop_value == 'normal':
                        attrs.append('font-style="normal"')
                    else:
                        attrs.append(f'font-style="{prop_value}"')
                elif prop_name == 'fill':
                    attrs.append(f'fill="{prop_value}"')
                elif prop_name == 'stroke':
                    attrs.append(f'stroke="{prop_value}"')
                elif prop_name == 'stroke-width':
                    attrs.append(f'stroke-width="{prop_value}"')
                elif prop_name == 'text-anchor':
                    attrs.append(f'text-anchor="{prop_value}"')
                elif prop_name == 'white-space':
                    #attrs.append(f'xml:space="{prop_value}"')
                    if prop_value == 'pre':
                        attrs.append('xml:space="preserve"')
                    else:
                        attrs.append('xml:space="default"')
                elif prop_name == 'dy':
                    attrs.append(f'dy="{prop_value}"')
                elif prop_name == 'dx':
                    attrs.append(f'dx="{prop_value}"')
                elif prop_name == 'transform':
                    attrs.append(f'transform="{prop_value}"')

            return ' '.join(attrs)

        def apply_style_to_tag(match):
            """Apply style to balises <g>, <text> ou <tspan>."""
            tag_name = match.group(1)
            attrs = match.group(2)
            logger.debug(f"[ScoreView2] Applying style to {tag_name} with attribs {attrs}")

            class_match = re.search(r'class=["\']([^"\']+)["\']', attrs)
            logger.debug(f"[ScoreView2] class found: {class_match}")
            style_match = re.search(r'style=["\']([^"\']*)["\']', attrs)
            logger.debug(f"[ScoreView2] style found: {style_match}")

            props_list = []
            unused_classes = []

            # Add properties from class (ex: .f20)
            if class_match:
                classes = class_match.group(1).split()
                for class_name in classes:
                    # Verify class for any type of tag
                    if class_name in class_styles and '*' in class_styles[class_name]:
                        props_list.extend(class_styles[class_name]['*'])
                    # Verify for specific ones
                    elif tag_name in tag_styles and class_name in tag_styles[tag_name]:
                        props_list.extend(tag_styles[tag_name][class_name])
                    else:
                        unused_classes.append(class_name)  # Keep class if unused

            # Add inline properties
            if style_match:
                inline_props = {}
                for prop in style_match.group(1).split(';'):
                    prop = prop.strip()
                    if not prop:
                        continue
                    prop_parts = prop.split(':', 1)
                    if len(prop_parts) != 2:
                        continue
                    prop_name = prop_parts[0].strip().lower()
                    prop_value = prop_parts[1].strip()
                    inline_props[prop_name] = prop_value
                props_list.append(inline_props)

            # Merge CSS properties
            if props_list:
                merged_props = merge_css_properties(*props_list)
                svg_attrs = css_dict_to_svg_attrs(merged_props)
                if svg_attrs:
                    new_attrs = re.sub(r'class=["\'][^"\']*["\']', '', attrs)
                    new_attrs = re.sub(r'style=["\'][^"\']*["\']', '', new_attrs)
                    # Add unused one if any
                    if unused_classes:
                        new_attrs = f'class="{ " ".join(unused_classes) }" {new_attrs}'
                    new_attrs = f"{svg_attrs} {new_attrs}".strip()
                    return f'<{tag_name} {new_attrs}>'

            return match.group(0)  # Return complete balise if no style

        # Apply style to <g>, <text>, <tspan>
        processed_content = re.sub(
            r'<(g|text|tspan)\s+([^>]*)>',
            apply_style_to_tag,
            svg_content,
            flags=re.DOTALL
        )

        # For now do not remove <style> as still used for path
        # Todo clean the one not used anymore
        #processed_content = re.sub(r'<style>.*?</style>', '', processed_content, flags=re.DOTALL)

        return processed_content

    def _normalize_font_family(self, font_family: str) -> str:
        """
        Normalize font and keep the first known one.
        Use System font for generic family such as (serif, sans-serif, monospace).
        Special case for the music one to be replace with real font name
        """
        font_list = [f.strip() for f in font_family.split(',')]

        for font in font_list:
            if font.lower() == "music":
                font = self.real_font_name
            resolved_font = resolve_generic_font(font)
            if self._font_exists(resolved_font):
                return resolved_font

        return self._get_default_font()

    def _get_default_font(self) -> str:
        """
        Default font of system.
        """
        return resolve_generic_font("serif")

    def _font_exists(self, font_family: str) -> bool:
        """
        Verify if font exist.
        Keep track of available fonts.
        """
        if self._available_fonts is None:
            db = QFontDatabase()
            self._available_fonts = [f.lower() for f in db.families()]
        return font_family.lower() in self._available_fonts
    
def resolve_generic_font(font_name: str) -> str:
    """
    Use System font for generic family such as (serif, sans-serif, monospace).
    """
    cleaned = font_name.strip().lower()

    if cleaned == "sans-serif":
        return QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont).family()

    elif cleaned == "monospace":
        return QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family()
    
    elif cleaned == "serif":
        current_os = platform.system()
        if current_os == "Darwin":  # macOS
            return "Times New Roman"
        elif current_os == "Windows":
            return "Times New Roman"
        else:  # Linux / autre
            return "DejaVu Serif"

    return font_name
