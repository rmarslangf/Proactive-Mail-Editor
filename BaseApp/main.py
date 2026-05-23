"""
Çalıştırma:
    python main.py

Bağımlılıklar:
    pip install PyQt5 PyQtWebEngine
"""
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from bulten import MainWindow
from bulten.config import PLATFORM


def main():
    # Platform ayarları
    if PLATFORM == "Darwin":
        os.environ.setdefault("QT_MAC_WANTS_LAYER", "1")
    if PLATFORM == "Linux":
        os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")

    # HiDPI
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
