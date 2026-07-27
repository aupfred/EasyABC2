
# 📦 **EasyABC2 — Build & Packaging Guide**  
*(Build Documentation — English, Markdown)*

---

## 1. Introduction  
This document explains how to build and package EasyABC2 into standalone applications for:

- macOS  
- Windows  
- Linux  

EasyABC2 uses **PyInstaller** for cross‑platform packaging.  
The goal is to produce a self‑contained application that includes:

- Python runtime  
- PySide6  
- QuickJS  
- abc2svg JavaScript modules  
- abcmidi tools (abc2midi, midi2abc)  
- translations (`.mo` files)  
- icons, images, and user documentation  

This guide assumes familiarity with Python packaging and basic command‑line usage.

---

## 2. Preparing the Environment  

### 2.1 Install dependencies  
```
pip install -r requirements.txt
```

### 2.2 Install PyInstaller  
```
pip install pyinstaller
```

### 2.3 Verify external tools  
Ensure the following exist inside `easyabc2/resources/`:

- `abc2svg/` (JS modules)  
- `abcmidi/` (abc2midi, midi2abc binaries)  
- `locales/` (translations)  
- `docs/` (user documentation)  
- `icons/` and `img/`  

See Resources Module for details.

---

## 3. Packaging Overview  

EasyABC2 is packaged using a **single PyInstaller command per OS**, with:

- `--windowed` for GUI  
- `--add-data` to include resources  
- `--icon` for application icon  
- `easyabc2/easyabc_app.py` as the entry point  

The build process produces:

- a standalone executable  
- a `dist/` directory containing all required files  

To ease the packaging is done using **PyInstaller**.  
The project includes a dedicated `.spec` file present in the tools folder to ensure reproducible builds.
Note: the `.spec` file to avoid an issue with setuptools


---

## 4. Packaging on macOS  

To build EasyABC2 on macOS:

1. Clone the repository  
2. Ensure the following folders exist at the root level:  
   - `easyabc2/`  
   - `tools/`  
3. Run the following command **from the root of the project**:

```
pyinstaller -y tools/EasyABC2-mac.spec
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

or

```
open dist/EasyABC2.app
```

---

## 5. Packaging on Windows  

A Windows `.spec` file will be provided later.

For experimentation only, you may try the basic command.


### 5.1 Basic command  
```
pyinstaller --windowed --name EasyABC2.exe \
    --add-data "easyabc2/resources;easyabc2/resources" \
    --icon easyabc2/resources/icons/app.ico \
    easyabc2/easyabc_app.py
```

### 5.2 Notes for Windows  
- Use `;` instead of `:` in `--add-data`  
- `.ico` icons are required  
- Fluidsynth DLLs must be included if used  
- Windows builds tend to be larger due to bundled DLLs  

### 5.3 Testing the build  
Double‑click:

```
dist/EasyABC2.exe
```

---

## 6. Packaging on Linux  

A Linux `.spec` file will be provided later.

For experimentation only, you may try the basic command.

### 6.1 Basic command  
```
pyinstaller --windowed --name easyabc2 \
    --add-data "easyabc2/resources:easyabc2/resources" \
    easyabc2/easyabc_app.py
```

### 6.2 Notes for Linux  
- Linux builds are typically smaller  
- Some distros require additional Qt libraries  
- AppImage packaging may be added later  

### 6.3 Testing the build  
```
./dist/easyabc2
```

---

## 7. Resource Inclusion Details  

PyInstaller does **not** automatically include non‑Python files.  
You must explicitly include:

### 7.1 abc2svg JavaScript modules  
```
easyabc2/resources/abc2svg/
```

Used by `Abc2SvgEngine`.

### 7.2 abcmidi tools  
```
easyabc2/resources/abcmidi/
```

Used by `Abc2MidiEngine`.

### 7.3 Locales  
```
easyabc2/resources/locales/<lang>/LC_MESSAGES/easyabc2.mo
```

Used by gettext.

### 7.4 Icons and images  
```
easyabc2/resources/icons/
easyabc2/resources/img/
```

Used by UI components.

### 7.5 User documentation  
```
easyabc2/resources/docs/
```

Displayed in help dialogs.

See Resources Module.

---

## 8. Entry Point  

The recommended entry point is:

```
easyabc2/easyabc_app.py
```

This file:

- initializes preferences  
- loads translations  
- creates the main window  
- starts the Qt event loop  

---

## 9. Troubleshooting  

### 9.1 Missing resources  
If the app launches without icons, translations, or abc2svg:

- verify `--add-data` paths  
- check OS‑specific path syntax  
- inspect `dist/` directory structure  

### 9.2 QtWebEngine issues  
If SVG preview fails:

- ensure PySide6‑QtWebEngine is installed  
- ensure `QtWebEngineProcess` is bundled  
- check macOS sandboxing restrictions  

### 9.3 MIDI playback issues  
If playback fails:

- verify fluidsynth DLLs (Windows)  
- verify CoreAudio backend (macOS)  
- check abcmidi binaries  

### 9.4 Application crashes on startup  
Check logs:

```
dist/EasyABC2/EasyABC2.exe --debug
```

or

```
LANG=en_US.UTF-8 ./dist/easyabc2
```

---

## 10. Future Improvements  

- macOS signing + notarization  
- Windows MSI installer  
- Linux AppImage or Flatpak  
- Automatic build scripts  
- CI/CD integration (GitHub Actions)  
- Dependency pruning for smaller builds  

---

## 11. Appendix  

### 11.1 Useful Commands  
```
pyinstaller --clean --noconfirm ...
```

```
rm -rf build/ dist/
```

### 11.2 Related Documentation  
- Overview  
- Developer Guide  
- Tester Guide  
- Resources Module
