# 📘 **EasyABC2 — Project Overview, Usage Guide, and Architecture**  
*(Overview Document — English, Markdown)*

---

## 1. Introduction  
### 1.1 Project Goals  
EasyABC2 is a modern, modular, internationalized rewrite of EasyABC.  
Its objectives include:

- Render music via abc2svg (used to be via abcm2ps)
- Allow selection of extract to be played
- A clean and modular architecture  
- Modern UI using PySide6  
- Full internationalization (gettext)  
- Cross‑platform distribution (macOS, Windows, Linux)

### 1.2 Target Audience  
- Musicians and arrangers  
- ABC notation users  
- Teachers and students  
- Developers and contributors  
- Translators and testers

### 1.3 Current Feature Set  
- ABC editing  
- SVG rendering via abc2svg  
- Audio playback using either direct synthesiser (Mac) or fluidsynth
- Follow‑mode (cursor tracking)  
- Search and replace (single and multi‑document)  
- Multi‑tab document management  
- Internationalization support  

### 1.4 Project Philosophy
EasyABC2 aims to remain:
- lightweight and fast
- transparent in its architecture
- friendly to contributors
- faithful to ABC notation standards
- extensible without becoming bloated

### 1.5 What EasyABC2 is NOT
- It is not a full DAW
- It is not a graphical music notation editor like MuseScore
- It does not aim to support non‑ABC formats

---

## 2. User‑Facing Features (Tester Reference)  
### 2.1 Main Interface  
- Main window layout  
- Toolbar  
- Tab bar  
- Editor panel  
- SVG rendering panel  

### 2.2 ABC Editing  
- Syntax highlighting  
- Navigation  
- Error reporting  
- Undo/redo  
- Interaction with rendered score  

### 2.3 Search and Replace  
- Text search  
- Multi‑document search  
- Replace One  
- Replace All  
- Result list and navigation  
- Offset updates after replacement  

### 2.4 Playback and Follow Mode  
- Start/stop playback  
- Tempo control  
- Loop mode  
- Synchronization with SVG  
- Cursor tracking  

### 2.5 Document Management  
- Open / Save / Save As  
- Modified state detection  
- Tab management  
- File encoding handling  

### 2.6 Preferences  
- Paths to external tools (abc2midi, midi2abc, abc2svg)  
- Rendering options  
- Playback options  
- UI options  

### 2.7 Internationalization  
- Language selection via system locale  
- Structure of translation files  
- How to test translations  

### 2.8 Current Limitations
- No import/export options yet
- No incipit generation
- No transposition helpers
- No contextual help system

---

## 3. Internal Architecture (Developer Reference)  
### 3.1 Project Structure  
- Directory layout  
- Modules and responsibilities  
- Resource folders (icons, JS, CSS, locales)

### 3.2 MainWindow  
- Role and responsibilities  
- Signal/slot orchestration  
- Tab management  
- Integration with controllers  

### 3.3 DocumentTab  
- ABC editor  
- SVG rendering pipeline  
- State management  
- Interaction with playback and search  

### 3.4 SearchController  
- Text extraction  
- Indexing  
- Search algorithm  
- Replace One / Replace All  
- Offset correction logic  
- Public vs internal API  

### 3.5 FollowEngine  
- Communication with SVG  
- JS event handling  
- Playback synchronization  
- Cursor tracking  

### 3.6 PlaybackController  
- Audio engine  
- Tempo and loop management  
- Playback state machine  

### 3.7 Internationalization  
- gettext initialization  
- `.po` / `.mo` structure  
- `.pot` generation  
- msgid conventions  

### 3.8 abc2svg Integration  
- QuickJS usage  
- JS execution pipeline  
- Error handling  
- Rendering lifecycle  

### 3.9 Coding Standards
- Use PEP8
- Use type hints
- Keep UI logic separate from controllers
- Keep msgid stable when possible

---

## 4. Roadmap  
### 4.1 Features to Reintroduce (from EasyABC)  
- Import/export options  
- Incipit generation  
- X: renumbering  
- Sorting tunes by field  
- Transposition helpers  
- Musical symbol insertion  
- Help system  
- Tooltips and contextual help  

### 4.2 New Features Considered  
- Dark mode  
- Native PDF export  
- Plugin system  
- Collaborative editing  
- API for external tools  

### 4.3 Priorities  
- Short‑term  
- Mid‑term  
- Long‑term  

---

## 5. Contribution Guidelines  
### 5.1 For Testers  
- Installation instructions  
- How to run EasyABC2  
- What to test  
- How to report issues  
- Sample ABC files  

### 5.2 For Developers  
- Setting up the environment  
- Running in debug mode  
- Adding new features  
- Adding translatable strings  
- Running tests  
- Packaging the application  

### 5.3 For Translators  
- Editing `.po` files  
- Compiling `.mo` files  
- Testing translations  
- msgid conventions  
- Language‑specific notes  

### 5.4 Build & Packaging Overview
- PyInstaller is used for macOS, Windows, Linux
- Locales are bundled from easyabc2/resources/locales
- External tools (abc2midi, midi2abc) must be included manually

---

## 6. Appendices  
### 6.1 Full Project Tree  
### 6.2 Python Dependencies  
### 6.3 External Tools  
### 6.4 Keyboard Shortcuts  
### 6.5 ABC Notation Reference (summary)

---
