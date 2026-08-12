"""
Otomobil Yönetim Paneli - Ana giriş
"""
import sys
import os

# Proje kök dizinini Python yoluna ekle (IDE/komut satırı uyumluluğu için)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Tutarlı görünüm için

    # Stil sayfası (modern görünüm)
    app.setStyleSheet("""
        QMainWindow { background-color: #fafafa; }
        QPushButton:hover { opacity: 0.9; }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()