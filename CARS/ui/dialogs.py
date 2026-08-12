"""
Yeniden kullanılabilir mesaj diyalogları.
"""
from PySide6.QtWidgets import QMessageBox, QWidget

def show_info(parent: QWidget, title: str, message: str):
    QMessageBox.information(parent, title, message)

def show_warning(parent: QWidget, title: str, message: str):
    QMessageBox.warning(parent, title, message)

def show_error(parent: QWidget, title: str, message: str):
    QMessageBox.critical(parent, title, message)

def ask_yes_no(parent: QWidget, title: str, question: str) -> bool:
    reply = QMessageBox.question(
        parent, title, question,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    return reply == QMessageBox.Yes