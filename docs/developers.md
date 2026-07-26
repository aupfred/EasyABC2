# 📗 **EasyABC2 — Developer Documentation**  
*(Developer Guide — English, Markdown)*

---

## 1. Introduction  
This document provides technical guidance for developers who want to understand, extend, or contribute to EasyABC2.  
It covers:

- Project structure  
- Internal architecture  
- Coding conventions  
- How to run the application in development mode  
- How to add new features  
- How to work with translations  
- How to package the application  

EasyABC2 is designed to be **modular, maintainable, and contributor‑friendly**.

---

## 2. Project Structure  
The repository is organized as follows:

```
project_root/
│
├── easyabc2/
│   ├── __init__.py
│   ├── __main__.py
│   ├── easyabc_app.py
│   ├── engines/
│   │   ├── midi/
│   │   ├── abc2midi_engine.py
│   │   ├── abc2svg_engine.py
│   │   ├── engines_manager.py
│   │   └── follow_engine.py
│   ├── models/
│   │   ├── abc_assist/
│   │   └── abc_document.py
│   ├── resources/
│   │   ├── abc2svg/
│   │   ├── abcmidi/
│   │   ├── docs/
│   │   ├── icons/
│   │   ├── img/
│   │   ├── locales/
│   │   ├── icons_rc.py
│   │   └── icons.qrc
│   ├── syntax/
│   │   └── abc_styler2.qrc
│   ├── ui/
│   │   ├── abc_assist_panel.py
│   │   ├── abc_editor.py
│   │   ├── abc_preview_dialog.py
│   │   ├── code_editor.py
│   │   ├── document_tab.py
│   │   ├── editor_adapter.py
│   │   ├── main_window.py
│   │   ├── play_range_selector_widget.py
│   │   ├── preferences_dialog.py
│   │   ├── score_view.py
│   │   ├── search_dialog.py
│   │   ├── tune_list_widget.py
│   │   └── txt_preview_dialog.py
│   └── utils/
│   │   ├── easyabc_utils.py
│   │   ├── logging_utils.py
│   │   ├── preferences.py
│   │   ├── search_controller.py
│   │   └── themes.py
│
├── docs/
│   ├── overview.md
│   ├── developers.md
│   ├── testers.md
│   ├── translators.md
│   └── build.md
│
├── third_party/
│   ├── abc2xml/
│   ├── mplay/
│   ├── testplayer/
│   └── xml2abc/
│
├── requirements.txt
├── README.md
└── LICENSE
```

### Key directories  
- **easyabc2/** — main application package  
- **controllers/** — logic controllers (search, playback, follow, etc.)  
- **ui/** — PySide6 UI components  
- **engines/** — interfaces to external tools (abc2midi, midi2abc, abc2svg)  
- **resources/** — icons, JS, CSS, translations, user documentation  
- **docs/** — developer/tester/contributor documentation  

---

## 3. Running EasyABC2 in Development Mode  
### 3.1 Install dependencies  
```
pip install -r requirements.txt
```

### 3.2 Run the application  
```
python -m easyabc2
```

### 3.3 Enable debug logging  
Inside your code, logs are available via the project logger:

```python
from easyabc2.utils.logging_utils import logger
logger.debug("Debug message")
```

To be noted that for now in the preferences the logging mode is forced to debug.

---

## 4. Architecture Overview  

EasyABC2 is built around a **controller‑driven architecture** with a clean separation between:

- UI (PySide6 widgets)
- Controllers (Controlling the application and ABC logic)
- Models & syntax (ABC interpretation and highlighters)
- Engines (management of core abc tools and midi rendering)
- Resources (icons, translations, default external core tools (abc2svg and abcmidi))
- Utils (various helpers and controllers)

The pipeline to render is (abc2svg + QuickJS)

### 4.1 Pipeline: abc2svg Integration  
**Pipeline:**  
1. ABC text is passed to abc2svg JS scripts  
2. QuickJS executes the JS  
3. SVG output is injected into a QWebEngineView  
4. JS events (cursor, errors, warnings) are captured  
5. Python controllers react accordingly  

**Error handling:**  
- JS exceptions are caught and logged  
- Rendering errors are displayed in the UI  


Below is a breakdown of each major component.

---

### 4.2 EasyABC_App  
**Role:**  
The central orchestrator of the application.

**Responsibilities:**  
- Creating and managing windows  
- Routing signals between controllers  
- Handling application‑level events (quit, preferences, etc.)

**Key interactions:**  
- Creates `MainWindow` instances  
- Connects to `SearchController`, `EnginesManager`, `Preferences`  

### 4.3 UI Modules  

#### 4.3.1 MainWindow  
**Role:**  
The central orchestrator of menus and user interactions.

**Responsibilities:**  
- Creating and managing tabs  
- Routing signals  
- Managing menus, toolbars, and global actions  

**Key interactions:**  
- Creates `DocumentTab` instances  
- Updates UI state based on controller events  

#### 4.3.2 DocumentTab  
**Role:**  
Represents a single ABC document.

**Responsibilities:**  
- Hosting the ABC editor  
- Hosting the SVG rendering view  
- Managing document state (modified, saved, encoding)  
- Handling per‑document playback state  
- Handling per‑document search results  

**Rendering pipeline:**  
1. ABC text → abc2svg (via QuickJS)  
2. SVG output → QWebEngineView  
3. JS events → FollowEngine  

---

### 4.4 Controllers Module  

#### 4.4.1 FollowEngine  
**Role:**  
For each abc document, synchronizes playback with the rendered SVG.

**Responsibilities:**  
- Receiving JS events from the SVG  
- Highlighting the current note  
- Managing cursor tracking  
- Communicating with the playback controller  

**Pipeline:**  
- SVG emits JS events  
- QuickJS → Python bridge  
- FollowEngine updates UI  

#### 4.4.2 EngineManagers  
**Role:**  
Manage central engines of the application.

**Responsibilities:**  
- Managing abc2svg engine with quickjs  
- Managing abc2midi and midi2abc
- Managing midi_player
- Update and control them centrally  

**Pipeline:**  
- Initialising  
- Updating based on preference changes  
- Accessing to each engine  

#### 4.4.3 SearchController  
**Role:**  
Provides search and replace functionality across one or multiple documents.

**Responsibilities:**  
- Extracting text from documents  
- Running search queries  
- Maintaining a list of results  
- Navigating between results  
- Performing Replace One / Replace All  
- Updating offsets after replacements  

**Design notes:**  
- Search logic is independent from UI  
- Results are stored in a structured format  
- Offset correction ensures stable navigation  

#### 4.4.4 MidiPlayer  
**Role:**  
Controls audio playback.

**Responsibilities:**  
- Starting/stopping playback  
- Managing tempo (todo)
- Managing loop ranges  
- Handling playback state transitions  
- Communicating with FollowEngine  

**Backends:**  
- macOS: direct synthesizer or fluidsynth
- Windows/Linux: fluidsynth  

#### 4.4.5 Preferences  
**Role:**  
Controls preferences of the application.

**Responsibilities:**  
- Manage the json file
- Return the user preference or the default one
- Track the changes of preference

**Pipeline:**  
- Loads preference at startup
- Saves them  
- Notifies preference changes

---

### 4.5 Engines module

#### 4.5.1 Abc2SvgEngine  
**Role:**  
Controls the svg rendering of abc2svg.

**Responsibilities:**  
- Initialise the quickjs environment for abc2svg
- Execute abc2svg

**Pipeline:**  
- Initialize quickjs and various abc2svg modules
- Enable transformation from abc to svg  

#### 4.5.2 Abc2MidiEngine
**Role:**  
Controls the 2 utils abc2midi and midi2abc provided by abcmidi.

**Responsibilities:**  
- Convert ABC to midi file to be able to play
- Retrieve from midi file generated the timing of each note

**Pipeline:**  
- Direct call of the utils by running the command

**Todo:**
- Add the ability to import in an ABC Document the MIDI file as ABC

---

## 4.6 Models & Syntax Module  
The **models** and **syntax** modules provide the internal representation of ABC documents and the tools needed to interpret, analyze, and highlight ABC notation.

### 4.6.1 AbcDocument  
**Role:**  
Represents a complete ABC document, including raw text, metadata, tune list, and helper methods.

**Responsibilities:**  
- Store raw ABC text  
- Extract tune headers and metadata  
- Provide access to individual tunes  
- Offer helper methods for search, navigation, and manipulation  
- Maintain document‑level state (encoding, modified flag, etc.)

**Key interactions:**  
- Used by `DocumentTab` to represent the current document  
- Used by `SearchController` to extract text and compute offsets  
- Used by engines (abc2svg, abc2midi) to provide ABC input  

### 4.6.2 AbcAssist  
**Role:**  
Provides optional assistance for ABC editing (future expansion).

**Responsibilities:**  
- Offer syntax hints  
- Provide suggestions for ABC fields  
- Assist with common ABC patterns (headers, repeats, ornaments)

**Notes:**  
This module is fully reused from EasyABC 1 with few modification for integration in new architecture.
It will expand as EasyABC2 grows to add interactions with other features.

### 4.6.3 Syntax / Highlighting  
The `syntax/` directory contains resources for ABC syntax highlighting.

**abc_styler2 (ABCHighlighter):**  
- Defines color rules for ABC syntax  
- Loaded by `CodeEditor`  
- Can be extended for themes  
- Provides visual cues for fields, notes, decorations, comments, etc.

**Key interactions:**  
- Used by `CodeEditor` to apply syntax highlighting  
- Works together with `themes.py` for color schemes  

---

## 4.7 Resources Module  
The `resources/` directory contains all non‑Python assets required by EasyABC2.

### 4.7.1 Icons  
- Application icons  
- Toolbar icons  
- Status icons  
- Bundled via `icons.qrc` and compiled into `icons_rc.py`

### 4.7.2 Locales  
- Translation files (`.po` and `.mo`)  
- Organized by language under `locales/<lang>/LC_MESSAGES/`  
- Loaded at runtime via gettext

### 4.7.3 Docs  
- User‑facing documentation (Markdown)  
- Embedded in the application for offline access  
- Can be displayed in a help dialog or QWebEngineView

### 4.7.4 abc2svg  
- JavaScript modules used by QuickJS  
- Core rendering engine for ABC → SVG  
- Includes `abc2svg.js`, `abc2svg-*.js`, and helper scripts

### 4.7.5 abcmidi  
- Bundled binaries or scripts for abc2midi and midi2abc  
- Used by `Abc2MidiEngine`

### 4.7.6 img  
- Miscellaneous images (logos, splash screens, etc.)

---

## 4.8 Utils Module  
The `utils/` module contains helper classes and controllers that support the rest of the application.

### 4.8.1 Logging  
**logging_utils.py:**  
- Centralized logging configuration  
- Provides a project‑wide logger  
- Currently defaults to DEBUG mode (subject to future preference control)

### 4.8.2 Themes  
**themes.py:**  
- Defines color themes for the editor and UI  
- Works with syntax highlighting  
- Future expansion: dark mode, custom themes

### 4.8.3 Preferences  
**preferences.py:**  
- Loads and saves user preferences from JSON  
- Provides default values when needed  
- Notifies listeners when preferences change  
- Used by `EngineManager`, `MainWindow`, and others

### 4.8.4 Various Helpers  
**easyabc_utils.py:**  
- Miscellaneous helper functions  
- File utilities  
- ABC‑related helpers  
- General convenience functions used across modules

---

## 4.9 Internationalization (gettext)  
**Initialization:**  
Translations are loaded via:

```python
lang = gettext.translation("easyabc2", LOCALE_DIR, fallback=True)
_ = lang.gettext
n_ = lang.ngettext
```

**Files:**  
```
easyabc2/resources/locales/<lang>/LC_MESSAGES/easyabc2.po
easyabc2/resources/locales/<lang>/LC_MESSAGES/easyabc2.mo
```

**Developer rules:**  
- Always wrap user‑visible strings in `_()`  
- For plurals, use `n_(singular, plural, count)`  
- Keep msgid stable when possible  
- Regenerate `.pot` after adding/modifying strings  

---

## 5. Coding Standards  
To keep the project maintainable:

### 5.1 Python conventions  
- Follow PEP8  
- Use type hints  
- Keep functions short and focused  
- Prefer composition over inheritance  
- Avoid circular imports  

### 5.2 UI conventions  
- UI logic stays in `ui/`  
- Business logic stays in controllers  
- Avoid mixing UI and logic  

### 5.3 Internationalization  
- Never concatenate translatable strings  
- Keep msgid stable  
- Use descriptive msgid (not abbreviations)  

---

## 6. Adding New Features  
### 6.1 Steps  
1. Identify the correct controller or create a new one  
2. Add UI elements in `ui/`  
3. Connect signals/slots  
4. Add logic in the controller  
5. Add translations  
6. Update documentation  
7. Add tests if applicable  

### 6.2 Example: adding a new menu action  
- Add action in `MainWindow`  
- Connect to a controller method  
- Add a tooltip (translatable)  
- Update user documentation  

---

## 7. Working With Translations  
### 7.1 Generate `.pot`  
```
xgettext --language=Python --keyword=_ --keyword=n_:1,2 \
         --from-code=UTF-8 -o easyabc2.pot $(find easyabc2 -name "*.py")
```

### 7.2 Update `.po` files  
```
msgmerge --update fr.po easyabc2.pot
```

### 7.3 Compile `.mo`  
```
msgfmt fr.po -o fr.mo
```

---

## 8. Packaging the Application  
Packaging is done using **PyInstaller**.  
The project includes a dedicated `.spec` file to ensure reproducible builds.

---

### 8.1 macOS  

To build EasyABC2 on macOS:

1. Clone the repository  
2. Ensure the following folders exist at the root level:  
   - `easyabc2/`  
   - `packaging/`  
3. Run the following command **from the root of the project**:

```
pyinstaller -y packaging/EasyABC2-mac.spec
```

This will generate:

```
dist/EasyABC2.app
```

The `.spec` file handles:

- embedding resources  
- embedding abc2midi / midi2abc  
- embedding abc2svg  
- generating a proper macOS Info.plist  
- setting the application icon  
- file associations (.abc, .mid, .midi)

Once generated, you can run either directly by double-clicking the app or by launching the following command from the root of the project:
```
./dist/EasyABC2.app/Contents/MacOS/EasyABC2
```

---

### 8.2 Windows  
A Windows `.spec` file will be provided later.

For experimentation only, you may try:

```
pyinstaller --windowed --name EasyABC2.exe ^
    --add-data "easyabc2/resources;easyabc2/resources" ^
    --icon easyabc2/resources/icons/app.ico ^
    easyabc2/run_easyabc2.py
```

⚠️ This will **not** embed abc2midi/midi2abc or abc2svg correctly.  
A proper Windows `.spec` file will be added later.

---

### 8.3 Linux  
A Linux `.spec` file will be provided later.

For experimentation only:

```
pyinstaller --windowed --name easyabc2 \
    --add-data "easyabc2/resources:easyabc2/resources" \
    easyabc2/run_easyabc2.py
```

⚠️ As with Windows, this does **not** embed third‑party binaries or JavaScript files.  
A dedicated `.spec` file will be added later.

---

## 9. Appendix  
### 9.1 Useful Tools  
- PySide6  
- QuickJS  
- gettext  
- fluidsynth  
- abc2svg
- abcmidi

### 9.2 Sample Development Commands  
```
python -m easyabc2
LANG=fr_FR.UTF-8 python -m easyabc2
```
