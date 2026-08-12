import sys, os, base64
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QSplitter, QStatusBar, QMessageBox,
    QAbstractItemView, QScrollArea, QGridLayout, QSizePolicy, QProgressDialog,
    QInputDialog, QLineEdit, QApplication, QDialog, QSlider, QMenu, QSpinBox,
    QToolButton, QFormLayout, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint, QEvent, QThread
from PySide6.QtGui import QFont, QPixmap, QDrag, QMouseEvent, QAction

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from core.data_manager import DataManager
from core.github_manager import GitHubManager
from ui.dialogs import show_info, ask_yes_no, show_warning, show_error
from ui.brand_dialog import BrandDialog
from ui.model_dialog import ModelDialog
from ui.design_dialog import DesignDialog
import config


# ---------- TEMA ----------
class Theme:
    APP_BG = "#F0F2F5"
    PREVIEW_BG = "#E4E6EB"
    PANEL_BG = "#FFFFFF"
    PANEL_BORDER = "#DDE1E6"
    PHONE_FRAME = "#1A1C1E"
    PHONE_SCREEN = "#FAFBFC"
    CARD_BG = "#FFFFFF"
    CARD_BORDER = "#E8EAED"
    TEXT_PRIMARY = "#1A1C1E"
    TEXT_SECONDARY = "#5F6B7A"
    TEXT_TERTIARY = "#8E98A3"
    ACCENT = "#2563EB"
    ACCENT_LIGHT = "#EFF6FF"
    SELECTED_BORDER = "#2563EB"
    HIGHLIGHT_BG = "#F0F6FF"
    HIGHLIGHT_BORDER = "#B3D4FF"
    RULER_PANEL_BG = "#FBFCFD"
    RULER_TRACK = "#DDE1E6"
    RULER_FILL = "#2563EB"
    RULER_HANDLE = "#FFFFFF"
    RULER_HANDLE_BORDER = "#2563EB"
    BTN_PRIMARY = "#2563EB"
    BTN_SUCCESS = "#4caf50"
    BTN_DANGER = "#d32f2f"
    BTN_WARNING = "#ff9800"
    BTN_DARK = "#24292e"
    BRAND_DIVIDER = "#E8EAED"
    FILTER_BG = "#FFFFFF"
    FILTER_ACTIVE_BG = "#EFF6FF"
    FILTER_ACTIVE_BORDER = "#2563EB"


# ---------- GitHub Worker ----------
class GitHubWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, repo_owner, repo_name, token, data_dir):
        super().__init__()
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token
        self.data_dir = data_dir

    def run(self):
        try:
            gh = GitHubManager(self.repo_owner, self.repo_name, self.token)
            if not gh.test_connection():
                self.finished.emit(False, "GitHub bağlantısı başarısız.\nRepo adı ve token'ı kontrol edin.")
                return
            report = gh.full_sync(self.data_dir)
            self.finished.emit(True, "Güncelleme tamamlandı:\n" + "\n".join(report))
        except Exception as e:
            self.finished.emit(False, f"Hata: {str(e)}")


# ---------- Marka Listesi Öğesi ----------
class BrandListItem(QFrame):
    edit_clicked = Signal(str)
    delete_clicked = Signal(str)
    move_up = Signal(str)
    move_down = Signal(str)

    def __init__(self, brand_id, name, logo_path, model_count, is_first=False, is_last=False, parent=None):
        super().__init__(parent)
        self.brand_id = brand_id
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedHeight(80)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(50, 50)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("background-color: #e0e0e0; border-radius: 5px;")
        full_path = os.path.join(config.DATA_DIR, logo_path) if logo_path else ""
        if full_path and os.path.exists(full_path):
            pixmap = QPixmap(full_path)
            self.logo_label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("🏢")

        info_layout = QVBoxLayout()
        self.name_label = QLabel(name)
        self.name_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.count_label = QLabel(f"{model_count} Model")
        self.count_label.setStyleSheet("color: #666;")
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.count_label)

        order_layout = QVBoxLayout()
        order_layout.setSpacing(2)
        self.up_btn = QPushButton("↑")
        self.up_btn.setFixedSize(30, 25)
        self.up_btn.setEnabled(not is_first)
        self.up_btn.clicked.connect(lambda: self.move_up.emit(self.brand_id))
        self.down_btn = QPushButton("↓")
        self.down_btn.setFixedSize(30, 25)
        self.down_btn.setEnabled(not is_last)
        self.down_btn.clicked.connect(lambda: self.move_down.emit(self.brand_id))
        order_layout.addWidget(self.up_btn)
        order_layout.addWidget(self.down_btn)

        action_layout = QVBoxLayout()
        self.edit_btn = QPushButton("Düzenle")
        self.edit_btn.setFixedSize(70, 25)
        self.edit_btn.setStyleSheet(f"background-color: {Theme.BTN_PRIMARY}; color: white; border: none; padding: 3px; border-radius: 3px;")
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.brand_id))
        self.delete_btn = QPushButton("Sil")
        self.delete_btn.setFixedSize(50, 25)
        self.delete_btn.setStyleSheet(f"background-color: {Theme.BTN_DANGER}; color: white; border: none; padding: 3px; border-radius: 3px;")
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.brand_id))
        action_layout.addWidget(self.edit_btn)
        action_layout.addWidget(self.delete_btn)

        layout.addWidget(self.logo_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addLayout(order_layout)
        layout.addLayout(action_layout)


# ---------- ModelCard (Ana Panel) ----------
class ModelCard(QFrame):
    edit_clicked = Signal(str)
    delete_clicked = Signal(str)
    move_up = Signal(str)
    move_down = Signal(str)
    order_changed = Signal(str, str)

    def __init__(self, car, is_first=False, is_last=False, parent=None):
        super().__init__(parent)
        self.car_id = car.id
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(220, 270)
        self.setStyleSheet(f"ModelCard {{ background: {Theme.CARD_BG}; border: 1px solid {Theme.CARD_BORDER}; border-radius: 12px; }}")
        self.setAcceptDrops(True)
        self.drag_start_pos = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        img_path = os.path.join(config.DATA_DIR, car.thumbnail) if car.thumbnail else ""
        self.image_label = QLabel()
        self.image_label.setFixedHeight(110)
        self.image_label.setAlignment(Qt.AlignCenter)
        if img_path and os.path.exists(img_path):
            self.image_label.setPixmap(QPixmap(img_path).scaled(190, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.image_label.setText("🚗")
        layout.addWidget(self.image_label)

        self.name_label = QLabel(f"<b>{car.name}</b>")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.year_label = QLabel(str(car.year))
        self.year_label.setAlignment(Qt.AlignCenter)
        self.price_label = QLabel(car.price if car.price else "")
        self.price_label.setAlignment(Qt.AlignCenter)
        self.price_label.setStyleSheet("color: #e65100; font-weight: bold;")
        layout.addWidget(self.name_label)
        layout.addWidget(self.year_label)
        layout.addWidget(self.price_label)

        bottom = QHBoxLayout()
        bottom.setSpacing(3)
        self.up_btn = QPushButton("↑")
        self.up_btn.setFixedSize(28, 28)
        self.up_btn.setEnabled(not is_first)
        self.up_btn.clicked.connect(lambda: self.move_up.emit(self.car_id))
        self.down_btn = QPushButton("↓")
        self.down_btn.setFixedSize(28, 28)
        self.down_btn.setEnabled(not is_last)
        self.down_btn.clicked.connect(lambda: self.move_down.emit(self.car_id))
        bottom.addWidget(self.up_btn)
        bottom.addWidget(self.down_btn)
        bottom.addStretch()

        self.edit_btn = QPushButton("Düzenle")
        self.edit_btn.setFixedSize(55, 28)
        self.edit_btn.setStyleSheet(f"background-color: {Theme.BTN_PRIMARY}; color: white; border: none; padding: 2px; border-radius: 3px; font-size: 10px;")
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.car_id))
        self.delete_btn = QPushButton("Sil")
        self.delete_btn.setFixedSize(35, 28)
        self.delete_btn.setStyleSheet(f"background-color: {Theme.BTN_DANGER}; color: white; border: none; padding: 2px; border-radius: 3px; font-size: 10px;")
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.car_id))
        bottom.addWidget(self.edit_btn)
        bottom.addWidget(self.delete_btn)
        layout.addLayout(bottom)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drag_start_pos:
            if (event.pos() - self.drag_start_pos).manhattanLength() > 10:
                self.start_drag()
                self.drag_start_pos = None
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag_start_pos = None
        super().mouseReleaseEvent(event)

    def start_drag(self):
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self.car_id)
        drag.setMimeData(mime)
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(110, 135, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.setStyleSheet(self.styleSheet() + " background-color: rgba(255,255,255,180);")
        drag.exec(Qt.MoveAction)
        self.setStyleSheet(self.styleSheet().replace(" background-color: rgba(255,255,255,180);", ""))

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.source() != self:
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet() + f" background-color: {Theme.ACCENT_LIGHT};")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace(f" background-color: {Theme.ACCENT_LIGHT};", ""))

    def dropEvent(self, event):
        source_id = event.mimeData().text()
        if source_id and source_id != self.car_id:
            self.order_changed.emit(source_id, self.car_id)
            event.acceptProposedAction()
        else:
            event.ignore()
        self.setStyleSheet(self.styleSheet().replace(f" background-color: {Theme.ACCENT_LIGHT};", ""))


# ---------- Önizleme Kartı ----------
class PreviewCard(QFrame):
    clicked = Signal(str, str)
    double_clicked = Signal(str, str)
    delete_clicked = Signal(str)
    order_changed = Signal(str, str)
    right_drag_scroll = Signal(int)

    def __init__(self, car, brand_id, parent=None):
        super().__init__(parent)
        self.car_id = car.id
        self.brand_id = brand_id
        card_w = 170
        img_h = int(card_w * 9 / 16)
        self.setFixedSize(card_w, img_h + 60)
        self.setStyleSheet(f"PreviewCard {{ background: {Theme.CARD_BG}; border: 1px solid {Theme.CARD_BORDER}; border-radius: 12px; }} PreviewCard:hover {{ border-color: {Theme.ACCENT}; }}")
        self.setAcceptDrops(True)
        self.drag_start_pos = None
        self.is_right_drag = False
        self.right_drag_distance = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        img_path = os.path.join(config.DATA_DIR, car.thumbnail) if car.thumbnail else ""
        self.image_label = QLabel()
        self.image_label.setFixedHeight(img_h)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: #F0F1F3; border-bottom: 1px solid #E8EAED; border-radius: 12px 12px 0 0;")
        if img_path and os.path.exists(img_path):
            self.image_label.setPixmap(QPixmap(img_path).scaled(card_w, img_h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.image_label.setText("🚗")
        layout.addWidget(self.image_label)

        caption = QWidget()
        caption.setStyleSheet(f"background: {Theme.CARD_BG}; padding: 8px; border-radius: 0 0 12px 12px;")
        cap_layout = QVBoxLayout(caption)
        cap_layout.setContentsMargins(8, 6, 8, 6)
        cap_layout.setSpacing(2)

        name_lbl = QLabel(car.name)
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        name_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        name_lbl.setWordWrap(True)
        cap_layout.addWidget(name_lbl)

        if car.show_year:
            year_lbl = QLabel(str(car.year))
            year_lbl.setFont(QFont("Segoe UI", 9))
            year_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
            cap_layout.addWidget(year_lbl)

        if car.show_description and car.card_description:
            desc_lbl = QLabel(car.card_description)
            desc_lbl.setFont(QFont("Segoe UI", 9))
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet(f"color: {Theme.TEXT_TERTIARY};")
            desc_lbl.setMaximumHeight(24)
            cap_layout.addWidget(desc_lbl)

        layout.addWidget(caption)
        self.setCursor(Qt.PointingHandCursor)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.is_right_drag = True
            self.drag_start_pos = event.pos()
            self.right_drag_distance = 0
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.LeftButton:
            self.is_right_drag = False
            self.drag_start_pos = event.pos()
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_right_drag and event.buttons() & Qt.RightButton:
            if self.drag_start_pos:
                delta = event.pos().x() - self.drag_start_pos.x()
                self.right_drag_distance += abs(delta)
                self.right_drag_scroll.emit(-delta)
                self.drag_start_pos = event.pos()
            event.accept()
        elif event.buttons() & Qt.LeftButton and self.drag_start_pos and not self.is_right_drag:
            if (event.pos() - self.drag_start_pos).manhattanLength() > 10:
                self.start_drag()
                self.drag_start_pos = None
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_right_drag and event.button() == Qt.RightButton:
            self.setCursor(Qt.PointingHandCursor)
            self.is_right_drag = False
            self.drag_start_pos = None
            event.accept()
        elif event.button() == Qt.LeftButton:
            if self.drag_start_pos and (event.pos() - self.drag_start_pos).manhattanLength() < 5:
                self.clicked.emit(self.car_id, self.brand_id)
            self.drag_start_pos = None
            super().mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.car_id, self.brand_id)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        if self.right_drag_distance > 5:
            self.right_drag_distance = 0
            event.accept()
            return
        self.right_drag_distance = 0
        menu = QMenu(self)
        menu.addAction("Düzenle", lambda: self.double_clicked.emit(self.car_id, self.brand_id))
        menu.addAction("Sil", lambda: self.delete_clicked.emit(self.car_id))
        menu.exec(event.globalPos())
        event.accept()

    def start_drag(self):
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self.car_id)
        drag.setMimeData(mime)
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(85, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        drag.exec(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.source() != self:
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet() + f" border: 2px dashed {Theme.ACCENT};")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace(f" border: 2px dashed {Theme.ACCENT};", ""))

    def dropEvent(self, event):
        source_id = event.mimeData().text()
        if source_id and source_id != self.car_id:
            self.order_changed.emit(source_id, self.car_id)
            event.acceptProposedAction()
        else:
            event.ignore()
        self.setStyleSheet(self.styleSheet().replace(f" border: 2px dashed {Theme.ACCENT};", ""))


# ---------- Lightbox Dialog ----------
class LightboxDialog(QDialog):
    def __init__(self, images, parent=None):
        super().__init__(parent)
        self.images = images
        self.current = 0
        self.setWindowTitle("Görsel")
        self.setStyleSheet("background: black;")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setCursor(Qt.ArrowCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: black;")
        layout.addWidget(self.image_label)

        self.counter_label = QLabel()
        self.counter_label.setAlignment(Qt.AlignCenter)
        self.counter_label.setStyleSheet("color: white; font-size: 14px; background: rgba(0,0,0,0.6); padding: 5px; border-radius: 10px;")
        layout.addWidget(self.counter_label)

        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("❮")
        self.prev_btn.setStyleSheet("color: white; font-size: 30px; background: transparent; border: none;")
        self.prev_btn.clicked.connect(lambda: self.navigate(-1))
        self.next_btn = QPushButton("❯")
        self.next_btn.setStyleSheet("color: white; font-size: 30px; background: transparent; border: none;")
        self.next_btn.clicked.connect(lambda: self.navigate(1))
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)
        layout.addLayout(nav_layout)

        self.setMouseTracking(True)
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_controls)
        self.showFullScreen()
        self.show_image()

    def show_image(self):
        if 0 <= self.current < len(self.images):
            img_path = os.path.join(config.DATA_DIR, self.images[self.current]) if not self.images[self.current].startswith('http') else self.images[self.current]
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                scaled = pixmap.scaled(self.screen().size() * 0.85, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled)
            self.counter_label.setText(f"{self.current + 1} / {len(self.images)}")
            self.counter_label.setVisible(True)
            self.prev_btn.setVisible(True)
            self.next_btn.setVisible(True)
            self.hide_timer.start(3000)

    def hide_controls(self):
        self.counter_label.setVisible(False)
        self.prev_btn.setVisible(False)
        self.next_btn.setVisible(False)

    def navigate(self, direction):
        self.current += direction
        if self.current < 0:
            self.current = len(self.images) - 1
        elif self.current >= len(self.images):
            self.current = 0
        self.show_image()

    def mouseMoveEvent(self, event):
        self.counter_label.setVisible(True)
        self.prev_btn.setVisible(True)
        self.next_btn.setVisible(True)
        self.hide_timer.start(3000)
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:
            self.navigate(1)
        elif event.key() == Qt.Key_Left:
            self.navigate(-1)
        elif event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.navigate(-1)
        else:
            self.navigate(1)


# ---------- ModernRuler ----------
class ModernRuler(QWidget):
    valueChanged = Signal(int)

    def __init__(self, label, min_val, max_val, init_val, unit="px", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        title = QLabel(label)
        title.setFixedWidth(80)
        title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: 600;")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(init_val)
        self.slider.valueChanged.connect(self._on_change)
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ background: {Theme.RULER_TRACK}; height: 4px; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: {Theme.RULER_HANDLE}; border: 2px solid {Theme.RULER_HANDLE_BORDER}; width: 14px; margin: -5px 0; border-radius: 7px; }}
            QSlider::sub-page:horizontal {{ background: {Theme.RULER_FILL}; border-radius: 2px; }}
        """)
        self.spin = QSpinBox()
        self.spin.setRange(min_val, max_val)
        self.spin.setValue(init_val)
        self.spin.setSuffix(f" {unit}")
        self.spin.valueChanged.connect(self._on_spin)
        self.spin.setFixedWidth(70)
        self.spin.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; background: white; border: 1px solid {Theme.PANEL_BORDER}; border-radius: 4px; padding: 2px;")
        layout.addWidget(title)
        layout.addWidget(self.slider)
        layout.addWidget(self.spin)
        self.value = init_val

    def _on_change(self, val):
        self.value = val
        self.spin.blockSignals(True)
        self.spin.setValue(val)
        self.spin.blockSignals(False)
        self.valueChanged.emit(val)

    def _on_spin(self, val):
        self.value = val
        self.slider.blockSignals(True)
        self.slider.setValue(val)
        self.slider.blockSignals(False)
        self.valueChanged.emit(val)

    def getValue(self):
        return self.value


# ---------- Önizleme Dialog ----------
class PreviewDialog(QDialog):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.setWindowTitle("Mobil Önizleme")
        self.setMinimumSize(900, 750)
        self.setStyleSheet(f"background: {Theme.PREVIEW_BG};")
        self.zoom_level = 1.0
        self.phone_base_w = 375
        self.phone_base_h = 740
        self.active_filter = None

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        left_panel = QFrame()
        left_panel.setFixedWidth(240)
        left_panel.setStyleSheet(f"QFrame {{ background: {Theme.PANEL_BG}; border: 1px solid {Theme.PANEL_BORDER}; border-radius: 12px; }}")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(16)
        left_layout.addWidget(QLabel("Önizleme Ayarları"))
        self.img_height_ruler = ModernRuler("Görsel Y.", 100, 400, self.data_manager.data.home_page_settings["card"]["image_height"])
        self.img_height_ruler.valueChanged.connect(self.apply_ruler_changes)
        left_layout.addWidget(self.img_height_ruler)
        self.gap_ruler = ModernRuler("Aralık", 0, 40, self.data_manager.data.home_page_settings["carousel"]["gap"])
        self.gap_ruler.valueChanged.connect(self.apply_ruler_changes)
        left_layout.addWidget(self.gap_ruler)
        left_layout.addStretch()

        phone_container = QWidget()
        phone_container.setStyleSheet("background: transparent;")
        phone_container_layout = QVBoxLayout(phone_container)
        phone_container_layout.setAlignment(Qt.AlignCenter)

        self.phone_frame = QFrame()
        self.phone_frame.setFixedSize(int(self.phone_base_w * self.zoom_level), int(self.phone_base_h * self.zoom_level))
        self.phone_frame.setStyleSheet(f"QFrame {{ background: {Theme.PHONE_FRAME}; border-radius: 32px; }}")
        frame_layout = QVBoxLayout(self.phone_frame)
        frame_layout.setContentsMargins(10, 40, 10, 40)

        screen = QFrame()
        screen.setStyleSheet(f"background: {Theme.PHONE_SCREEN}; border-radius: 22px;")
        screen_layout = QVBoxLayout(screen)
        screen_layout.setContentsMargins(0, 0, 0, 0)
        screen_layout.setSpacing(0)

        self.preview_title = QLabel("TÜM OTOMOBİLLER")
        self.preview_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.preview_title.setStyleSheet(f"padding: 6px 16px; color: {Theme.TEXT_PRIMARY};")
        screen_layout.addWidget(self.preview_title)

        self.filter_scroll = QScrollArea()
        self.filter_scroll.setFixedHeight(60)
        self.filter_scroll.setWidgetResizable(True)
        self.filter_scroll.setStyleSheet("border: none; background: transparent;")
        self.filter_widget = QWidget()
        self.filter_layout = QHBoxLayout(self.filter_widget)
        self.filter_layout.setAlignment(Qt.AlignLeft)
        self.filter_layout.setContentsMargins(12, 6, 12, 6)
        self.filter_layout.setSpacing(8)
        self.filter_scroll.setWidget(self.filter_widget)
        screen_layout.addWidget(self.filter_scroll)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"background: {Theme.PHONE_SCREEN}; border: none;")
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll.setWidget(self.scroll_content)
        screen_layout.addWidget(self.scroll)
        frame_layout.addWidget(screen)
        phone_container_layout.addWidget(self.phone_frame)

        right_panel = QFrame()
        right_panel.setFixedWidth(220)
        right_panel.setStyleSheet(f"QFrame {{ background: {Theme.PANEL_BG}; border: 1px solid {Theme.PANEL_BORDER}; border-radius: 12px; }}")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)
        right_layout.addWidget(QLabel("Özellikler"))
        self.right_content = QLabel("Bir öğe seçin")
        self.right_content.setWordWrap(True)
        right_layout.addWidget(self.right_content)
        right_layout.addStretch()

        self.selected_card = None
        self.setAcceptDrops(True)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(phone_container, stretch=1)
        main_layout.addWidget(right_panel)

        self.refresh_filter_bar()
        self.refresh_content()

    def refresh_filter_bar(self):
        while self.filter_layout.count():
            child = self.filter_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        all_btn = QPushButton("TÜMÜ")
        all_btn.clicked.connect(lambda: self.set_filter(None))
        self.filter_layout.addWidget(all_btn)
        for brand in sorted(self.data_manager.data.brands, key=lambda b: b.order):
            if not brand.show_on_homepage: continue
            btn = QPushButton(brand.name)
            btn.clicked.connect(lambda checked, bid=brand.id: self.set_filter(bid))
            self.filter_layout.addWidget(btn)

    def set_filter(self, brand_id):
        self.active_filter = brand_id
        self.refresh_filter_bar()
        self.refresh_content()

    def refresh_content(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        settings = self.data_manager.data.home_page_settings
        for brand in sorted(self.data_manager.data.brands, key=lambda b: b.order):
            if not brand.show_on_homepage or (self.active_filter and brand.id != self.active_filter): continue
            models = [m for m in brand.models if m.show_on_homepage]
            if not models: continue
            brand_section = QWidget()
            brand_layout = QVBoxLayout(brand_section)
            brand_layout.setContentsMargins(0, 10, 0, 5)
            brand_layout.setSpacing(6)

            header = QHBoxLayout()
            logo_path = os.path.join(config.DATA_DIR, brand.logo) if brand.logo else ""
            logo_lbl = QLabel()
            logo_lbl.setFixedSize(24, 24)
            if logo_path and os.path.exists(logo_path):
                logo_lbl.setPixmap(QPixmap(logo_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                logo_lbl.setText("🏢")
            header.addWidget(logo_lbl)
            header.addWidget(QLabel(f"<b>{brand.name}</b>"))
            header.addStretch()
            brand_layout.addLayout(header)

            if brand.show_brand_description and brand.brand_description:
                style = brand.brand_description_style or {}
                effect = style.get("effect", "none")
                desc_container = QWidget()
                desc_container.setStyleSheet(f"""
                    background: {Theme.HIGHLIGHT_BG};
                    border-left: 4px solid {Theme.ACCENT};
                    border-radius: 8px;
                    margin: 4px 20px;
                """)
                if effect == "shimmer":
                    desc_container.setStyleSheet(desc_container.styleSheet() + """
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #f0f6ff, stop:0.5 #e0ecff, stop:1 #f0f6ff);
                    """)
                desc_layout = QVBoxLayout(desc_container)
                desc_layout.setContentsMargins(12, 8, 12, 8)
                desc_label = QLabel(brand.brand_description)
                desc_label.setWordWrap(True)
                desc_label.setFont(QFont(style.get("font_family", "Arial"), style.get("font_size", 14)))
                desc_label.setStyleSheet(f"""
                    color: {style.get('color', '#1A1C1E')};
                    text-align: {style.get('text_align', 'left')};
                    font-weight: {style.get('font_weight', 'normal')};
                """)
                desc_layout.addWidget(desc_label)
                brand_layout.addWidget(desc_container)

            row = QScrollArea()
            row.setWidgetResizable(True)
            row.setFixedHeight(settings["card"]["image_height"] + 90)
            row.setStyleSheet("border: none; background: transparent;")
            row_content = QWidget()
            row_layout = QHBoxLayout(row_content)
            row_layout.setAlignment(Qt.AlignLeft)
            row_layout.setSpacing(settings["carousel"]["gap"])
            row_layout.setContentsMargins(16, 8, 16, 8)

            models.sort(key=lambda m: m.homepage_order, reverse=True)
            for car in models:
                card = PreviewCard(car, brand.id)
                card.clicked.connect(self.on_card_clicked)
                card.double_clicked.connect(self.on_card_double_clicked)
                card.delete_clicked.connect(self.delete_card)
                card.order_changed.connect(self.on_card_swapped)
                card.right_drag_scroll.connect(lambda dx, r=row: self.scroll_row(r, dx))
                row_layout.addWidget(card)
            row.setWidget(row_content)
            brand_layout.addWidget(row)
            self.scroll_layout.addWidget(brand_section)

    def scroll_row(self, row_widget, delta):
        row_widget.horizontalScrollBar().setValue(row_widget.horizontalScrollBar().value() + delta)

    def apply_ruler_changes(self):
        settings = self.data_manager.data.home_page_settings
        settings["card"]["image_height"] = self.img_height_ruler.getValue()
        settings["carousel"]["gap"] = self.gap_ruler.getValue()
        self.refresh_content()

    def on_card_clicked(self, car_id, brand_id):
        if self.selected_card:
            self.selected_card.setStyleSheet(self.selected_card.styleSheet().replace(f" border: 2px solid {Theme.SELECTED_BORDER};", ""))
        card = self.sender()
        if card and isinstance(card, PreviewCard):
            card.setStyleSheet(card.styleSheet() + f" border: 2px solid {Theme.SELECTED_BORDER};")
            self.selected_card = card

        brand = self.data_manager.data.get_brand_by_id(brand_id)
        if brand:
            car = brand.get_model_by_id(car_id)
            if car:
                images = []
                if car.large_images:
                    images = car.large_images.copy()
                elif car.thumbnail:
                    images = [car.thumbnail]
                if images:
                    lightbox = LightboxDialog(images, self)
                    lightbox.exec()

    def on_card_double_clicked(self, car_id, brand_id):
        dialog = ModelDialog(self.data_manager, brand_id, car_id=car_id, parent=self)
        if dialog.exec():
            self.refresh_filter_bar()
            self.refresh_content()
            if self.parent():
                self.parent().refresh_brand_list()
                if self.parent().current_brand_id:
                    self.parent().load_models(self.parent().current_brand_id)

    def on_card_swapped(self, dragged_id, target_id):
        for brand in self.data_manager.data.brands:
            dragged_car = brand.get_model_by_id(dragged_id)
            target_car = brand.get_model_by_id(target_id)
            if dragged_car and target_car:
                models = [m for m in brand.models if m.show_on_homepage]
                ids = [m.id for m in sorted(models, key=lambda m: m.homepage_order, reverse=True)]
                try:
                    i1, i2 = ids.index(dragged_id), ids.index(target_id)
                    ids[i1], ids[i2] = ids[i2], ids[i1]
                    self.data_manager.reorder_cars(brand.id, ids)
                    self.refresh_content()
                except:
                    pass
                break

    def delete_card(self, car_id):
        pass

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: event.ignore()

    def dropEvent(self, event):
        pass


# ---------- Ana Pencere ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Otomobil Yönetim Paneli")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(f"background: {Theme.APP_BG};")
        self.data_manager = DataManager(config.DATA_DIR)
        self.data_manager.initialize()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)

        # Sol panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_title = QLabel("MARKALAR")
        left_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        left_title.setStyleSheet(f"padding: 10px; background: {Theme.PANEL_BG}; border-bottom: 1px solid {Theme.PANEL_BORDER};")
        self.brand_list = QListWidget()
        self.brand_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.brand_list.setDropIndicatorShown(True)
        self.brand_list.setStyleSheet(f"QListWidget::item {{ border-bottom: 1px solid {Theme.PANEL_BORDER}; }} QListWidget::item:selected {{ background: {Theme.ACCENT_LIGHT}; }}")
        self.brand_list.itemClicked.connect(self.on_brand_selected)
        self.brand_list.model().rowsMoved.connect(self.on_brands_reordered)
        self.add_brand_btn = QPushButton("+ YENİ MARKA")
        self.add_brand_btn.setStyleSheet(f"background-color: {Theme.BTN_SUCCESS}; color: white; font-weight: bold; padding: 10px; border: none; border-radius: 3px;")
        self.add_brand_btn.clicked.connect(self.on_add_brand)
        left_layout.addWidget(left_title)
        left_layout.addWidget(self.brand_list)
        left_layout.addWidget(self.add_brand_btn)

        # Sağ panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        self.right_title = QLabel("Modeller")
        self.right_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.right_title.setAlignment(Qt.AlignCenter)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"background: {Theme.PANEL_BG}; border: 1px solid {Theme.PANEL_BORDER}; border-radius: 8px;")
        self.scroll_widget = QWidget()
        self.models_layout = QGridLayout(self.scroll_widget)
        self.models_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll_area.setWidget(self.scroll_widget)
        right_layout.addWidget(self.right_title)
        right_layout.addWidget(self.scroll_area)
        self.add_model_btn = QPushButton("+ YENİ MODEL")
        self.add_model_btn.setStyleSheet(f"background-color: {Theme.BTN_SUCCESS}; color: white; font-weight: bold; padding: 10px; border: none; border-radius: 3px;")
        self.add_model_btn.clicked.connect(self.on_add_model)
        self.add_model_btn.setVisible(False)
        right_layout.addWidget(self.add_model_btn)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 750])
        main_layout.addWidget(splitter)

        # Alt butonlar
        bottom_layout = QHBoxLayout()
        self.save_btn = QPushButton("VERİLERİ KAYDET")
        self.save_btn.setStyleSheet(f"background-color: {Theme.BTN_WARNING}; color: white; font-weight: bold; padding: 10px 30px; border: none; border-radius: 3px;")
        self.save_btn.clicked.connect(self.on_save_data)
        self.preview_btn = QPushButton("📱 ÖNİZLEME")
        self.preview_btn.setStyleSheet(f"background-color: {Theme.BTN_PRIMARY}; color: white; font-weight: bold; padding: 10px 30px; border: none; border-radius: 3px;")
        self.preview_btn.clicked.connect(self.on_open_preview)
        self.github_btn = QPushButton("GITHUB'A GÜNCELLE")
        self.github_btn.setStyleSheet(f"background-color: {Theme.BTN_DARK}; color: white; font-weight: bold; padding: 10px 30px; border: none; border-radius: 3px;")
        self.github_btn.clicked.connect(self.on_github_update)
        self.design_btn = QPushButton("ANA SAYFA TASARIM AYARLARI")
        self.design_btn.setStyleSheet(f"background-color: #6c5ce7; color: white; font-weight: bold; padding: 10px 20px; border: none; border-radius: 3px;")
        self.design_btn.clicked.connect(self.on_design_settings)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.save_btn)
        bottom_layout.addWidget(self.preview_btn)
        bottom_layout.addWidget(self.github_btn)
        bottom_layout.addWidget(self.design_btn)
        main_layout.addLayout(bottom_layout)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Hazır")
        self.current_brand_id = None
        self.refresh_brand_list()

    def refresh_brand_list(self):
        self.brand_list.clear()
        brands = sorted(self.data_manager.data.brands, key=lambda b: b.order)
        for i, brand in enumerate(brands):
            is_first, is_last = (i == 0), (i == len(brands) - 1)
            item = QListWidgetItem(self.brand_list)
            widget = BrandListItem(brand.id, brand.name, brand.logo, len(brand.models), is_first, is_last)
            widget.edit_clicked.connect(self.on_edit_brand)
            widget.delete_clicked.connect(self.on_delete_brand)
            widget.move_up.connect(self.on_move_brand_up)
            widget.move_down.connect(self.on_move_brand_down)
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.UserRole, brand.id)
            self.brand_list.setItemWidget(item, widget)
        if self.current_brand_id:
            self.select_brand_in_list(self.current_brand_id)

    def select_brand_in_list(self, brand_id):
        for i in range(self.brand_list.count()):
            if self.brand_list.item(i).data(Qt.UserRole) == brand_id:
                self.brand_list.setCurrentRow(i)
                break

    def on_brands_reordered(self):
        ids = [self.brand_list.item(i).data(Qt.UserRole) for i in range(self.brand_list.count())]
        if ids:
            self.data_manager.reorder_brands(ids)

    def clear_model_list(self):
        while self.models_layout.count():
            child = self.models_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def load_models(self, brand_id):
        self.clear_model_list()
        brand = self.data_manager.data.get_brand_by_id(brand_id)
        if not brand: return
        self.right_title.setText(brand.name.upper())
        self.add_model_btn.setVisible(True)
        models = sorted(brand.models, key=lambda m: m.order)
        for i, car in enumerate(models):
            card = ModelCard(car, is_first=(i == 0), is_last=(i == len(models) - 1))
            card.edit_clicked.connect(self.on_edit_model)
            card.delete_clicked.connect(self.on_delete_model)
            card.move_up.connect(self.on_move_model_up)
            card.move_down.connect(self.on_move_model_down)
            card.order_changed.connect(self.on_model_swapped)
            self.models_layout.addWidget(card, i // 3, i % 3)

    def show_placeholder(self):
        self.clear_model_list()
        lbl = QLabel("Sol taraftan bir marka seçin")
        lbl.setAlignment(Qt.AlignCenter)
        self.models_layout.addWidget(lbl, 0, 0)
        self.right_title.setText("Modeller")
        self.add_model_btn.setVisible(False)

    def on_model_swapped(self, dragged_id, target_id):
        if not self.current_brand_id: return
        brand = self.data_manager.data.get_brand_by_id(self.current_brand_id)
        if not brand: return
        models = sorted(brand.models, key=lambda m: m.order)
        ids = [m.id for m in models]
        try:
            idx1, idx2 = ids.index(dragged_id), ids.index(target_id)
            ids[idx1], ids[idx2] = ids[idx2], ids[idx1]
        except ValueError:
            return
        self.data_manager.reorder_cars(self.current_brand_id, ids)
        self.load_models(self.current_brand_id)

    def on_brand_selected(self, item):
        w = self.brand_list.itemWidget(item)
        if w:
            self.current_brand_id = w.brand_id
            self.load_models(w.brand_id)

    def on_add_brand(self):
        dlg = BrandDialog(self.data_manager, parent=self)
        if dlg.exec(): self.refresh_brand_list()

    def on_edit_brand(self, brand_id):
        dlg = BrandDialog(self.data_manager, brand_id=brand_id, parent=self)
        if dlg.exec(): self.refresh_brand_list()
        if self.current_brand_id == brand_id: self.load_models(brand_id)

    def on_delete_brand(self, brand_id):
        brand = self.data_manager.data.get_brand_by_id(brand_id)
        if not brand: return
        if ask_yes_no(self, "Silme Onayı", f"{brand.name} silinsin mi?"):
            if brand.logo:
                p = os.path.join(config.DATA_DIR, brand.logo)
                if os.path.exists(p): os.remove(p)
            self.data_manager.delete_brand(brand_id)
            self.current_brand_id = None
            self.show_placeholder()
            self.refresh_brand_list()

    def on_add_model(self):
        if not self.current_brand_id:
            show_info(self, "Bilgi", "Önce bir marka seçin."); return
        dlg = ModelDialog(self.data_manager, self.current_brand_id, parent=self)
        if dlg.exec(): self.load_models(self.current_brand_id); self.refresh_brand_list()

    def on_edit_model(self, car_id):
        if not self.current_brand_id: return
        dlg = ModelDialog(self.data_manager, self.current_brand_id, car_id=car_id, parent=self)
        if dlg.exec(): self.load_models(self.current_brand_id)

    def on_delete_model(self, car_id):
        if not self.current_brand_id: return
        brand = self.data_manager.data.get_brand_by_id(self.current_brand_id)
        if not brand: return
        car = brand.get_model_by_id(car_id)
        if not car: return
        if ask_yes_no(self, "Silme Onayı", f"{car.name} silinsin mi?"):
            for img in [car.thumbnail] + car.large_images:
                if img:
                    fp = os.path.join(config.DATA_DIR, img)
                    if os.path.exists(fp): os.remove(fp)
            self.data_manager.delete_car(self.current_brand_id, car_id)
            self.load_models(self.current_brand_id)
            self.refresh_brand_list()

    def on_move_brand_up(self, brand_id):
        brands = sorted(self.data_manager.data.brands, key=lambda b: b.order)
        ids = [b.id for b in brands]
        idx = ids.index(brand_id)
        if idx == 0: return
        ids[idx], ids[idx - 1] = ids[idx - 1], ids[idx]
        self.data_manager.reorder_brands(ids)
        self.refresh_brand_list()

    def on_move_brand_down(self, brand_id):
        brands = sorted(self.data_manager.data.brands, key=lambda b: b.order)
        ids = [b.id for b in brands]
        idx = ids.index(brand_id)
        if idx >= len(ids) - 1: return
        ids[idx], ids[idx + 1] = ids[idx + 1], ids[idx]
        self.data_manager.reorder_brands(ids)
        self.refresh_brand_list()

    def on_move_model_up(self, car_id):
        if not self.current_brand_id: return
        brand = self.data_manager.data.get_brand_by_id(self.current_brand_id)
        if not brand: return
        models = sorted(brand.models, key=lambda m: m.order)
        ids = [m.id for m in models]
        idx = ids.index(car_id)
        if idx == 0: return
        ids[idx], ids[idx - 1] = ids[idx - 1], ids[idx]
        self.data_manager.reorder_cars(self.current_brand_id, ids)
        self.load_models(self.current_brand_id)

    def on_move_model_down(self, car_id):
        if not self.current_brand_id: return
        brand = self.data_manager.data.get_brand_by_id(self.current_brand_id)
        if not brand: return
        models = sorted(brand.models, key=lambda m: m.order)
        ids = [m.id for m in models]
        idx = ids.index(car_id)
        if idx >= len(ids) - 1: return
        ids[idx], ids[idx + 1] = ids[idx + 1], ids[idx]
        self.data_manager.reorder_cars(self.current_brand_id, ids)
        self.load_models(self.current_brand_id)

    def on_open_preview(self):
        dialog = PreviewDialog(self.data_manager, self)
        dialog.exec()
        self.refresh_brand_list()
        if self.current_brand_id: self.load_models(self.current_brand_id)

    def on_save_data(self):
        try:
            self.data_manager.save()
            self.status_bar.showMessage("Veriler kaydedildi.")
        except Exception as e:
            show_error(self, "Hata", str(e))

    def on_github_update(self):
        saved = self._load_credentials()
        if saved:
            repo_owner, repo_name, token = saved["owner"], saved["repo"], saved["token"]
        else:
            repo_owner, repo_name, token = self._ask_credentials(save=True)
            if not all([repo_owner, repo_name, token]): return
        self._github_progress = QProgressDialog("GitHub'a bağlanılıyor...", None, 0, 0, self)
        self._github_progress.setWindowModality(Qt.WindowModal)
        self._github_progress.setCancelButton(None)
        self._github_progress.show()
        QApplication.processEvents()
        self.data_manager.save()
        self._github_worker = GitHubWorker(repo_owner, repo_name, token, config.DATA_DIR)
        self._github_worker.finished.connect(self._on_github_finished)
        self._github_worker.start()

    def _on_github_finished(self, success, message):
        self._github_progress.close()
        if success: show_info(self, "GitHub Güncelleme", message)
        else: show_error(self, "Hata", message)

    def _ask_credentials(self, save=False):
        dialog = QDialog(self)
        dialog.setWindowTitle("GitHub Bilgileri")
        dialog.setFixedSize(380, 240)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("GitHub Bilgilerini Girin"))
        form = QFormLayout()
        owner_edit = QLineEdit()
        form.addRow("Repo Sahibi:", owner_edit)
        repo_edit = QLineEdit()
        form.addRow("Repo Adı:", repo_edit)
        token_edit = QLineEdit()
        token_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Token:", token_edit)
        layout.addLayout(form)
        remember_cb = QCheckBox("Bilgilerimi hatırla")
        remember_cb.setChecked(True)
        layout.addWidget(remember_cb)
        buttons = QHBoxLayout()
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(dialog.reject)
        ok_btn = QPushButton("Tamam")
        ok_btn.clicked.connect(dialog.accept)
        buttons.addStretch()
        buttons.addWidget(cancel_btn)
        buttons.addWidget(ok_btn)
        layout.addLayout(buttons)
        if dialog.exec() != QDialog.Accepted:
            return None, None, None
        owner = owner_edit.text().strip()
        repo = repo_edit.text().strip()
        token = token_edit.text().strip()
        if not all([owner, repo, token]):
            show_warning(self, "Eksik Bilgi", "Tüm alanları doldurun.")
            return None, None, None
        if remember_cb.isChecked() or save:
            self._save_credentials(owner, repo, token)
        return owner, repo, token

    def _save_credentials(self, owner, repo, token):
        data = f"{owner}|||{repo}|||{token}"
        encoded = base64.b64encode(data.encode()).decode()
        try:
            with open(config.CREDENTIALS_FILE, "w") as f:
                f.write(encoded)
        except:
            pass

    def _load_credentials(self):
        if not os.path.exists(config.CREDENTIALS_FILE):
            return None
        try:
            with open(config.CREDENTIALS_FILE, "r") as f:
                encoded = f.read()
            decoded = base64.b64decode(encoded.encode()).decode()
            parts = decoded.split("|||")
            if len(parts) == 3:
                return {"owner": parts[0], "repo": parts[1], "token": parts[2]}
        except:
            pass
        return None

    def on_design_settings(self):
        dlg = DesignDialog(self.data_manager, self)
        if dlg.exec():
            self.status_bar.showMessage("Tasarım ayarları kaydedildi.")