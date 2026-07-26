# __init__.py
__version__ = "0.0.1"

import gettext
import os
from pathlib import Path
import locale
#print("locale.getdefaultlocale() =", locale.getdefaultlocale())
#print("locale.getlocale() =", locale.getlocale())
#print("os.environ.get('LANG') =", os.environ.get('LANG'))
#print("os.environ.get('LANGUAGE') =", os.environ.get('LANGUAGE'))

# Base directory of the package
BASE_DIR = Path(__file__).resolve().parent

# Locale directory inside resources
LOCALE_DIR = BASE_DIR / "resources" / "locales"

# Domain name (the name of your .mo files)
DOMAIN = "easyabc2"

# Bind gettext
gettext.bindtextdomain(DOMAIN, LOCALE_DIR)
gettext.textdomain(DOMAIN)

lang = gettext.translation(DOMAIN, LOCALE_DIR, fallback=True)

print("Gettext LOCALE_DIR =", LOCALE_DIR)
print("Gettext DOMAIN =", DOMAIN)
print("Available languages =", gettext.find(DOMAIN, LOCALE_DIR))

# Public translation function
#_ = gettext.gettext
#n_ = gettext.ngettext
_ = lang.gettext
n_ = lang.ngettext