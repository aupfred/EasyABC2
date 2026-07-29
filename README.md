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
git clone https://github.com/aupfred/EasyABC2.git
cd EasyABC2
```

EasyABC2 requires Python 3.12 or later.
On Linux, you might need to install python-venv to enable the virtual environment. For instance on Debian:
```bash
sudo apt install python3-venv
```

Create a virtual environment:

```bash
python3 -m venv easyabc2-env
source easyabc2-env/bin/activate
pip install --upgrade pip
```

On Linux, install necessary dependencies to build quickjs:
```bash
sudo apt install build-essential python3-dev pkg-config libffi-dev
```

Install EasyABC2 in editable mode:

```bash
pip install -e .
```

Install at least abcmidi and fluidsynth.
On Debian-based systems:
```bash
sudo apt install abcmidi
sudo apt install fluidsynth libfluidsynth3 libfluidsynth-dev
```

Launch the application:

```bash
python3 easyabc2/run_easyabc2.py
```

or
```bash
python3 -m easyabc2
```

Once started, open the Preferences dialog to configure
* the path to abc2midi and midi2abc
* the fluidsynth library (use the Search/Test button to verify the installation)
* the soundfont path

You can use the test button to verify whether the path are right or not.
The indication is provided just underneath.

---

## Packaging

Packaging is done using **PyInstaller**.  
A dedicated `.spec` file is provided in the tools folder to ensure reproducible macOS builds.

### macOS

From the root of the project:

```bash
pyinstaller -y tools/EasyABC2-mac.spec
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
├── docs/
│   ├── overview.md           # Overview of EasyABC2
│   ├── user_guide_en.md      # User guide
│   ├── translators.md        # Translation workflow
│   ├── testers.md            # Testing guidelines
│   ├── build.md              # Build instructions
│   └── developers.md         # Developer documentation
│
├── tools/
│   └── EasyABC2-mac.spec     # macOS PyInstaller spec file
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
