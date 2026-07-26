# 📘 **EasyABC2 — Translator Documentation**  
*(Translator Guide — English, Markdown)*

---

## 1. Introduction  
This document provides guidance for translators who want to contribute to EasyABC2 by adding or improving translations.

It covers:

- How EasyABC2 uses gettext  
- Where translation files are located  
- How to edit `.po` files  
- How to compile `.mo` files  
- How to test translations  
- Conventions for msgid  
- Best practices for translators  

EasyABC2 aims to support multiple languages and provide a fully internationalized user experience.

---

## 2. How EasyABC2 Uses gettext  

EasyABC2 uses the standard **gettext** system for internationalization.

### 2.1 Runtime loading  
At startup, EasyABC2 loads translations using:

```python
lang = gettext.translation("easyabc2", LOCALE_DIR, fallback=True)
_ = lang.gettext
n_ = lang.ngettext
```

### 2.2 Translatable strings  
All user‑visible strings in the code are wrapped in:

- `_()` for simple strings  
- `n_()` for plural forms  

Example:

```python
_("Open File")
n_("1 tune found", "%d tunes found", count)
```

See Internationalization for developer details.

---

## 3. Translation File Structure  

Translation files are stored under:

```
easyabc2/resources/locales/<lang>/LC_MESSAGES/
```

Each language contains:

- `easyabc2.po` — editable translation file  
- `easyabc2.mo` — compiled binary file used at runtime  

Example for French:

```
easyabc2/resources/locales/fr/LC_MESSAGES/easyabc2.po
easyabc2/resources/locales/fr/LC_MESSAGES/easyabc2.mo
```

Supported languages may include:

- da (Danish)  
- de (German)  
- fr (French)  
- it (Italian)  
- ja (Japanese)  
- nl (Dutch)  
- sv (Swedish)  
- zh_CN (Chinese Simplified)

---

## 4. Editing `.po` Files  

### 4.1 Recommended tools  
Translators may use:

- **Poedit** (recommended)  
- **Gtranslator**  
- **Lokalize**  
- Any text editor (VSCode, Sublime, etc.)

Poedit automatically:

- highlights missing translations  
- handles plural forms  
- marks fuzzy entries  
- compiles `.mo` files (optional)

### 4.2 `.po` file structure  
A typical entry looks like:

```
msgid "Open File"
msgstr "Ouvrir un fichier"
```

Plural example:

```
msgid "1 tune found"
msgid_plural "%d tunes found"
msgstr[0] "1 morceau trouvé"
msgstr[1] "%d morceaux trouvés"
```

### 4.3 Fuzzy entries  
When msgid changes slightly, gettext marks entries as:

```
#, fuzzy
```

Translators should:

- review fuzzy entries  
- update the translation  
- remove the `fuzzy` tag  

---

## 5. Compiling `.mo` Files  

After editing `.po`, translators must compile `.mo`:

```
msgfmt easyabc2.po -o easyabc2.mo
```

Poedit can do this automatically when saving.

The `.mo` file must be placed in:

```
easyabc2/resources/locales/<lang>/LC_MESSAGES/
```

---

## 6. Testing Translations  

### 6.1 Run EasyABC2 with a specific language  
On Linux/macOS:

```
LANG=fr_FR.UTF-8 python -m easyabc2
```

On Windows (PowerShell):

```
$env:LANG="fr_FR.UTF-8"
python -m easyabc2
```

### 6.2 What to check  
Translators should verify:

- Menus  
- Dialogs  
- Buttons  
- Tooltips  
- Error messages  
- Preferences  
- Search dialog  
- Playback controls  

See Tester Guide for more detailed testing instructions.

### 6.3 Missing translations  
Untranslated strings appear in English.  
Translators should note them and update the `.po` file.

---

## 7. Updating Translations After Code Changes  

When developers add or modify strings, they regenerate the `.pot` file.

Translators must then merge updates:

```
msgmerge --update easyabc2.po easyabc2.pot
```

This will:

- keep existing translations  
- add new msgid entries  
- mark changed entries as fuzzy  
- remove obsolete entries  

See Developer Guide for details.

---

## 8. Translation Conventions  

### 8.1 Do not translate ABC notation  
Fields like:

- `X:`  
- `T:`  
- `M:`  
- `K:`  
- `V:`  

must **never** be translated.

### 8.2 Do not translate file formats  
Examples:

- ABC  
- MIDI  
- SVG  
- PDF  

### 8.3 Keep msgid meaning intact  
Avoid:

- shortening  
- paraphrasing  
- adding extra meaning  

### 8.4 Respect punctuation  
If msgid ends with a colon, keep it:

```
msgid "Preferences:"
msgstr "Préférences :"
```

### 8.5 Tooltips should remain concise  
Tooltips must be:

- short  
- clear  
- helpful  

### 8.6 Error messages must remain precise  
Avoid vague translations.

---

## 9. Best Practices for Translators  

- Use Poedit for convenience  
- Translate progressively  
- Review fuzzy entries carefully  
- Test translations regularly  
- Coordinate with developers when msgid changes  
- Keep terminology consistent across the UI  
- Avoid overly long translations that break layout  

---

## 10. Appendix  

### 10.1 Useful Commands  
```
msgmerge --update easyabc2.po easyabc2.pot
msgfmt easyabc2.po -o easyabc2.mo
LANG=fr_FR.UTF-8 python -m easyabc2
```

### 10.2 Useful Links  
- Overview  
- Developer Guide  
- Tester Guide  
