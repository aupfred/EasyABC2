# easyabc2/__main__.py
import sys
#from easyabc2.main import main
from easyabc2.easyabc_app import EasyABCApp

def main():
    print("Starting EasyABC")

    app = EasyABCApp(sys.argv)
    return sys.exit(app.exec()) #app.exec()

if __name__ == "__main__":
    main()
