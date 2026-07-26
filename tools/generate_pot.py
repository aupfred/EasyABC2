# tools/generate_pot.py
import os
from pathlib import Path
import subprocess

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "easyabc2"
LOCALE_DIR = SRC_DIR / "resources" / "locales"
POT_FILE = LOCALE_DIR / "easyabc2.pot"

def collect_sources():
    sources = []
    for root, dirs, files in os.walk(SRC_DIR):
        for f in files:
            if f.endswith(".py"):
                sources.append(str(Path(root) / f))
    return sources

sources = collect_sources()

cmd = [
    "xgettext",
    "--language=Python",
    "--keyword=_",
    "--keyword=n_",
    "--output", str(POT_FILE),
] + sources

print("Generating POT file...")
subprocess.run(cmd)
print("Done:", POT_FILE)
