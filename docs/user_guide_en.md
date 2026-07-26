
# 🎼 **EasyABC2 — User Guide (English)**  
*(In‑Application Help — Markdown)*

---

## 1. Introduction  
EasyABC2 is a modern, cross‑platform ABC notation editor and player.  
It allows you to:

- Edit ABC music notation  
- Render scores using **abc2svg**  
- Play tunes with synchronized cursor tracking  
- Search and replace text across multiple tunes  
- Manage multiple ABC files in tabs  
- Use the application in several languages  

This guide explains how to use EasyABC2’s main features.

---

## 2. Getting Started  

### 2.1 Opening EasyABC2  
When you launch EasyABC2, you will see:

- A **menu bar**  
- A **toolbar**  
- A **tab bar**  
- An **ABC editor**  
- A **score preview**  

You can start typing ABC notation immediately.

### 2.2 Opening an ABC file  
Use:

**File → Open…**

or drag‑and‑drop an `.abc` file into the window.

### 2.3 Creating a new file  
Use:

**File → New Tab**

A new empty document appears.

---

## 3. Editing ABC Notation  

### 3.1 The ABC Editor  
The editor supports:

- Syntax highlighting  
- Automatic score preview  
- Undo / redo  
- Multiple tunes per file  

You can type any valid ABC notation.  
For example:

```
X:1
T:Example Tune
M:4/4
K:D
D2 FA d2 fA | d2 fA g2 fe |
```

### 3.2 Multiple tunes  
EasyABC2 supports files containing several tunes.  
Each tune begins with an `X:` field.

### 3.3 Syntax errors  
If your ABC contains errors:

- The score preview may show warnings  
- Some notes may not render  
- The playback may skip invalid sections  

---

## 4. Score Preview (abc2svg)

The score preview is generated using **abc2svg**.

### 4.1 Automatic rendering  
Whenever you edit the ABC text, the score updates automatically.

### 4.2 Interacting with the score  
You can:

- Click notes to move the editor cursor  
- Scroll the score independently  
- Zoom using standard shortcuts (if enabled)

### 4.3 Rendering errors  
If abc2svg detects an error, it will display a message in the preview area.

See ABC Editing.

---

## 5. Playback & Follow Mode  

EasyABC2 can play your tune and highlight notes in real time.

### 5.1 Starting playback  
Use:

**Playback → Play**

or the toolbar play button.

### 5.2 Stopping playback  
Use:

**Playback → Stop**

### 5.3 Follow mode  
During playback:

- The current note is highlighted  
- The score scrolls automatically  
- The editor cursor follows the music  

### 5.4 Looping a range  
You can select a playback range using the **Play Range Selector**.

This allows you to:

- Practice a section  
- Repeat difficult passages  
- Focus on specific measures  

---

## 6. Search & Replace  

EasyABC2 includes a powerful search system.

### 6.1 Opening the search dialog  
Use:

**Edit → Search…**

### 6.2 Searching  
You can search:

- In the current document  
- Across all open tabs  

Results appear in a list.

### 6.3 Navigating results  
Use the **Next** and **Previous** buttons.

### 6.4 Replace One  
Replaces the selected match.

### 6.5 Replace All  
Replaces all matches in the document or across all tabs.

See SearchController.

---

## 7. Managing Documents  

### 7.1 Tabs  
Each ABC file opens in its own tab.

You can:

- Open multiple files  
- Close tabs  
- Rename tabs  
- Switch between tabs  

### 7.2 Saving  
Use:

**File → Save**  
**File → Save As…**

Modified tabs show an indicator.

### 7.3 File encoding  
EasyABC2 handles UTF‑8 by default.

---

## 8. Preferences  

Open preferences via:

**Edit → Preferences…**

### 8.1 External tools  
You can configure paths for:

- `abc2midi`  
- `midi2abc`  
- `abc2svg` (JS modules are bundled)

### 8.2 Playback options  
Depending on your system:

- macOS: built‑in synthesizer or fluidsynth  
- Windows/Linux: fluidsynth  

### 8.3 Interface options  
You can adjust:

- Themes (future)  
- Editor behavior  
- Rendering options  

See Preferences.

---

## 9. Internationalization  

EasyABC2 supports multiple languages.

### 9.1 Automatic language selection  
The application uses your system locale.

### 9.2 Manual testing  
You can run EasyABC2 with a specific language:

```
LANG=fr_FR.UTF-8 python -m easyabc2
```

### 9.3 Missing translations  
If a string is not translated, it appears in English.

See Translator Guide.

---

## 10. MIDI Tools  

EasyABC2 can convert ABC to MIDI using **abcmidi**.

### 10.1 Generate MIDI  
Use:

**Tools → Generate MIDI**

### 10.2 Play MIDI  
Playback uses the integrated MIDI player.

### 10.3 Convert MIDI to ABC  
This feature is planned for a future release.

See Abc2MidiEngine.

---

## 11. Known Limitations  

EasyABC2 is under active development.  
Current limitations include:

- No import/export options yet  
- No incipit generation  
- No X: renumbering  
- No transposition helpers  
- No contextual help system  
- Tempo control incomplete  
- MIDI → ABC import not implemented  

See Roadmap.

---

## 12. Troubleshooting  

### 12.1 Score does not update  
Check for ABC syntax errors.

### 12.2 Playback does not start  
Verify:

- MIDI tools are configured  
- Fluidsynth is installed (Windows/Linux)

### 12.3 Missing icons or translations  
Your installation may be incomplete.

### 12.4 Application crashes  
Try running from the terminal to view logs:

```
python -m easyabc2
```

---

## 13. Appendix  

### 13.1 Useful Commands  
```
python -m easyabc2
LANG=fr_FR.UTF-8 python -m easyabc2
```

### 13.2 Sample ABC  
```
X:1
T:Simple Tune
M:4/4
K:G
G2 B2 d2 g2 | g2 d2 B2 G2 |
```

### 13.3 Related Documentation  
- Overview  
- Developer Guide  
- Tester Guide  
- Translator Guide
