# EasyABC2

EasyABC2 is a modern, cross‑platform rewrite of the original EasyABC music notation editor, now using abc2svg.  

---

## Features

EasyABC2 supports:
- ABC notation editing
- Real‑time playback
- MIDI import/export
- SVG rendering via abc2svg
- Multi‑file projects
- Customizable playback ranges
- Integrated search and navigation

This project is currently in active development (alpha stage).

---

## Installation (development mode)

Clone the repository:

```bash
git clone https://github.com/<your-username>/EasyABC2.git
cd EasyABC2
```

EasyABC2 requires Python 3.12 or later.
Create a virtual environment:

```bash
python3 -m venv easyabc2-env
source easyabc2-env/bin/activate
```

Install EasyABC2 in editable mode:

```bash
pip install -e .
```

Launch the application:

```bash
python3 easyabc2/run_easyabc2.py
```

---

## Packaging

Packaging is done using **PyInstaller**.  
A dedicated `.spec` file is provided to ensure reproducible macOS builds.

### macOS

From the root of the project:

```bash
pyinstaller -y packaging/EasyABC2-mac.spec
```

This generates:

```
dist/EasyABC2.app
```

You can run the application either by double‑clicking the app bundle or via:

```bash
./dist/EasyABC2.app/Contents/MacOS/EasyABC2
```

The macOS bundle includes:
- abc2midi / midi2abc binaries  
- abc2svg JavaScript engine  
- all resources (icons, images, locales)  
- a custom Info.plist with file associations (.abc, .mid, .midi)

### Windows / Linux

Dedicated `.spec` files will be provided later.

---

## Project Structure

```
EasyABC2/
│
├── easyabc2/                 # Main application package
│   ├── run_easyabc2.py       # Entry point
│   ├── ui/                   # Qt UI components
│   ├── engines/              # Playback, rendering, follow engine
│   ├── utils/                # Helpers and shared logic
│   ├── models/               # ABC document and assist
│   ├── syntax/               # ABC syntax highlighter
│   ├── resources/            # Icons, images, locales, etc.
│   └── third_party/          # abc2svg, abcmidi, mplay
│
├── packaging/
│   └── EasyABC2-mac.spec     # macOS PyInstaller spec file
│
├── docs/
│   ├── overview.md           # Overview of EasyABC2
│   ├── user_guide_en.md      # User guide
│   ├── translators.md        # Translation workflow
│   ├── testers.md            # Testing guidelines
│   ├── build.md              # Build instructions
│   └── developers.md         # Developer documentation
│
├── pyproject.toml            # Build configuration
└── README.md                 # This file
```
Full documentation is available in the `docs/` folder.

---

## Contributing

Contributions are welcome.  
Please open an issue or submit a pull request.

---

## License

To be defined.
