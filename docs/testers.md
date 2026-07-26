
# 📘 **EasyABC2 — Tester Documentation**  
*(Tester Guide — English, Markdown)*

---

## 1. Introduction  
This document provides guidance for testers who want to evaluate EasyABC2, verify its stability, and report issues effectively.

It covers:

- Installation  
- Running the application  
- What to test  
- How to report issues  
- Sample workflows  
- Known limitations  

EasyABC2 is under active development. Your feedback is essential to ensure a stable and user‑friendly release.

---

## 2. Installation & Setup  

### 2.1 Requirements  
- Python 3.10+  
- macOS, Windows, or Linux  
- Basic familiarity with ABC notation (optional but helpful)

### 2.2 Install dependencies  
```
pip install -r requirements.txt
```

### 2.3 Run EasyABC2  
```
python -m easyabc2
```

### 2.4 Run with a specific language  
```
LANG=fr_FR.UTF-8 python -m easyabc2
```

To test internationalization, see Testing Translations.

---

## 3. What to Test  
This section lists the main areas testers should verify.  
Each subsection includes concrete actions and expected results.

## 3.1 Main Interface  
Testers should verify:

- Window layout loads correctly  
- Toolbar icons appear and respond  
- Tabs can be created, closed, renamed  
- Menus behave as expected  

**Actions:**

1. Open EasyABC2  
2. Create multiple tabs  
3. Switch between tabs  
4. Resize the window  
5. Open the Preferences dialog  

Expected result:  
UI remains responsive, no visual glitches, no crashes.

## 3.2 ABC Editing  
Testers should verify:

- Syntax highlighting  
- Editing responsiveness  
- Undo/redo  
- ABC field recognition  
- Error reporting  

**Actions:**

1. Paste a multi‑tune ABC file  
2. Edit headers (X:, T:, M:, K:)  
3. Add notes, rests, decorations  
4. Trigger syntax errors intentionally  

Expected result:  
Editor highlights syntax correctly, errors appear in the preview.

## 3.3 SVG Rendering (abc2svg)  
Testers should verify:

- Rendering correctness  
- Update on text change  
- Error messages from abc2svg  
- Interaction with the score  

**Actions:**

1. Type a simple tune  
2. Verify the score updates instantly  
3. Introduce an ABC error  
4. Click on notes in the SVG  

Expected result:  
SVG updates smoothly; errors appear; clicking notes moves the cursor.

## 3.4 Search & Replace  
Testers should verify:

- Search accuracy  
- Multi‑document search  
- Replace One  
- Replace All  
- Offset correction  

**Actions:**

1. Search for a word in a long ABC file  
2. Navigate through results  
3. Replace One  
4. Replace All  
5. Search across multiple tabs  

Expected result:  
Search results are correct; replacements update the document without breaking offsets.

See SearchController.

## 3.5 Playback & Follow Mode  
Testers should verify:

- Playback start/stop  
- Tempo changes (when implemented)  
- Loop mode  
- Cursor tracking  
- Synchronization with SVG  

**Actions:**

1. Play a tune  
2. Observe the moving cursor  
3. Enable loop mode  
4. Change playback range  
5. Stop playback  

Expected result:  
Playback is smooth; cursor follows notes; loop works; no desynchronization.

See FollowEngine.

## 3.6 Preferences  
Testers should verify:

- Loading/saving preferences  
- Changing paths to external tools  
- Changing playback options  
- Changing UI options  

**Actions:**

1. Open Preferences  
2. Change abc2midi path  
3. Restart EasyABC2  
4. Verify the change persists  

Expected result:  
Preferences persist and engines update accordingly.

See Preferences.

## 3.7 Internationalization  
Testers should verify:

- Language detection  
- Translated UI strings  
- Missing translations  
- Plural forms  

**Actions:**

1. Run EasyABC2 with `LANG=fr_FR.UTF-8`  
2. Check menus, dialogs, tooltips  
3. Switch to another language (if available)  

Expected result:  
UI appears in the selected language; untranslated strings are noted.

See Internationalization.

## 3.8 External Tools (abc2midi, midi2abc)  
Testers should verify:

- MIDI generation  
- MIDI playback  
- MIDI → ABC conversion (future)  

**Actions:**

1. Generate MIDI from ABC  
2. Play the MIDI  
3. Inspect timing information  

Expected result:  
MIDI is generated correctly; playback works; timing matches the score.

See Abc2MidiEngine.

---

## 4. Reporting Issues  
To ensure efficient debugging, testers should include:

### 4.1 Required Information  
- OS version  
- Python version  
- EasyABC2 version  
- Steps to reproduce  
- ABC file (minimal example)  
- Screenshots (if relevant)  
- Logs (if available)

### 4.2 How to report  
Issues can be reported via:

- GitHub Issues  
- Email (if applicable)  
- Internal bug tracker  

Include links to:

- Overview  
- Developer Guide

---

## 5. Sample Test Workflows  

### 5.1 Basic Workflow  
1. Open EasyABC2  
2. Paste a simple tune  
3. Verify rendering  
4. Play the tune  
5. Search for a word  
6. Replace it  
7. Save the file  

### 5.2 Multi‑Document Workflow  
1. Open 3 ABC files  
2. Search across all tabs  
3. Replace All  
4. Play each tune  
5. Verify preferences persist  

### 5.3 Internationalization Workflow  
1. Run with French locale  
2. Check menus  
3. Check dialogs  
4. Check tooltips  
5. Note missing translations  

---

## 6. Known Limitations  
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

## 7. Appendix  

### 7.1 Useful Commands  
```
python -m easyabc2
LANG=fr_FR.UTF-8 python -m easyabc2
```

### 7.2 Sample ABC Files  
Testers should prepare:

- Simple one‑tune ABC  
- Multi‑tune ABC  
- ABC with errors  
- ABC with complex ornaments  
- ABC with multiple voices  
