# easyabc2/utils/easyabc_utils.py
from pathlib import Path
import os
import platform
import re
import codecs

# --------------------------------------
# Utils related to path
# --------------------------------------
PACKAGE_DIR = Path(__file__).resolve().parent.parent
THIRD_PARTY_DIR = PACKAGE_DIR / "third_party"
RESOURCES_DIR = PACKAGE_DIR / "resources"

def get_app_data_dir(app_name="EasyABC2"):
    system = platform.system()

    if system == "Windows":
        base = os.getenv("APPDATA")
        if not base:
            base = Path.home() / "AppData" / "Roaming"
        else:
            base = Path(base)
        base = base / app_name

    elif system == "Darwin":
        base = Path("~/Library/Application Support").expanduser() / app_name

    else:
        base = Path("~/.config").expanduser() / app_name

    base.mkdir(parents=True, exist_ok=True)
    return base

def get_temp_dir(app_data_dir):
    temp = app_data_dir / "temp"
    temp.mkdir(exist_ok=True)
    return temp

# --------------------------------------
# Utils related to temporary files
# --------------------------------------
def save_temp_abc(text: str, temp_data_dir, filename="current_tune.abc"):
    path = temp_data_dir / filename
    path.write_text(text, encoding="utf-8")
    return path

def save_temp_svg(text: str, temp_data_dir, filename="current_tune.svg"):
    path = temp_data_dir / filename
    path.write_text(text, encoding="utf-8")
    return path

def save_temp_mftext(text: str, temp_data_dir, filename="current_tune.mftext"):
    path = temp_data_dir / filename
    path.write_text(text, encoding="utf-8")
    return path

def get_temp_dir_for_tab(global_temp_dir, tab_uid):
    name = f"tab_{tab_uid}"
    path = global_temp_dir / name
    path.mkdir(exist_ok=True)
    return path


# --------------------------------------
# Utils related to run external process
# --------------------------------------
import subprocess

def run_process(cmd, input_text=None, cwd=None, encoding="utf-8"):
    """
    Run external process returning (stdout, stderr, returncode).
    input_text : str or None
    """
    if input_text is not None:
        input_bytes = input_text.encode(encoding)
    else:
        input_bytes = None

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE if input_bytes else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd
    )

    stdout, stderr = proc.communicate(input_bytes)

    return (
        stdout.decode(encoding, errors="replace"),
        stderr.decode(encoding, errors="replace"),
        proc.returncode
    )

def get_output_from_process(cmd, input_text=None, cwd=None, encoding="utf-8"):
    if input_text is not None:
        input_bytes = input_text.encode(encoding)
    else:
        input_bytes = None

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE if input_bytes else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
    )
    stdout, stderr = proc.communicate(input_bytes)

    return (
        stdout.decode(encoding, errors="replace"),
        stderr.decode(encoding, errors="replace"),
        proc.returncode,
    )

# ----------------------------------------
# Utils related to text file and encodings
# ----------------------------------------

def read_entire_file(path):
    f = open(path, 'rb') # read in binary to avoid problem with EOL characters
    result = f.read()
    f.close()
    return result

def read_text_if_file_exists(filepath):
    ''' reads the contents of the given file if it exists, otherwise returns the empty string '''
    if filepath and os.path.exists(filepath):
        return read_entire_file(filepath)
    else:
        return ''

def read_abc_file(path):
    file_as_bytes = read_entire_file(path)
    encoding = get_encoding_abc(file_as_bytes)

    tried = []

    # 1) Explicit ABC encoding
    if encoding:
        tried.append(encoding)
        try:
            return file_as_bytes.decode(encoding), encoding
        except UnicodeError:
            pass

    # 2) UTF‑8
    tried.append("utf-8")
    try:
        return file_as_bytes.decode("utf-8"), "utf-8"
    except UnicodeError:
        pass

    # 3) Latin‑1 (always possible)
    tried.append("latin-1")
    return file_as_bytes.decode("latin-1"), "latin-1"

abc_charset_re = re.compile(
    b'(%%|I:)abc-charset\\s+(?P<encoding>[a-zA-Z0-9_\\-]+)'
)

def get_encoding_abc(abc_as_bytes, default_encoding=None):
    # BOM UTF‑8
    if abc_as_bytes.startswith(b"\xef\xbb\xbf"):
        return "utf-8"

    header = abc_as_bytes[:2048]

    match = abc_charset_re.search(header)
    if match:
        enc = match.group("encoding")
        enc = enc.decode("ascii", errors="ignore")

        # Normalise
        enc = enc.lower()
        if enc in ("utf8", "utf-8", "utf_8"):
            return "utf-8"

        # Verify if Python knows the encoding
        try:
            codecs.lookup(enc)
            return enc
        except LookupError:
            return None

    # New ABC files
    if header.startswith(b"%abc"):
        return "utf-8"

    return default_encoding

import unicodedata

def normalize_abc_text(text: str) -> str:
    # Normalise Unicode
    text = unicodedata.normalize("NFC", text)

    # Normalise end of lines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    return text
