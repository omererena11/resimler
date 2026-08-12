import copy
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QSpinBox, QCheckBox,
    QDialogButtonBox, QTabWidget, QWidget, QColorDialog, QComboBox, QFontComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPixmap, QPainter, QPen, QBrush


class DesignDialog(QDialog):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.settings = copy.deepcopy(data_manager.data.home_page_settings)
        self.setWindowTitle("Ana Sayfa Tasarım Ayarları")
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.update_preview()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # --- Genel sekmesi ---
        gen_tab = QWidget()
        gen_layout = QFormLayout(gen_tab)

        self.title_edit = QLineEdit(self.settings["title"]["text"])
        gen_layout.addRow("Başlık Metni:", self.title_edit)

        self.title_font = QFontComboBox()
        self.title_font.setCurrentFont(QFont(self.settings["title"]["font_family"]))
        gen_layout.addRow("Başlık Font:", self.title_font)

        self.title_size = QSpinBox()
        self.title_size.setRange(10, 60)
        self.title_size.setValue(self.settings["title"]["font_size"])
        gen_layout.addRow("Başlık Boyut:", self.title_size)

        self.title_bold = QCheckBox("Kalın")
        self.title_bold.setChecked(self.settings["title"]["font_weight"] == "bold")
        gen_layout.addRow(self.title_bold)

        self.title_color_btn = QPushButton("Renk")
        self.title_color_btn.clicked.connect(lambda: self.choose_color("title", "color"))
        gen_layout.addRow("Başlık Rengi:", self.title_color_btn)

        self.bg_color_btn = QPushButton("Arka Plan Rengi")
        self.bg_color_btn.clicked.connect(lambda: self.choose_color("background_color"))
        gen_layout.addRow("Ana Sayfa Arka Plan:", self.bg_color_btn)

        tabs.addTab(gen_tab, "Genel")

        # --- Kartlar sekmesi ---
        card_tab = QWidget()
        card_layout = QFormLayout(card_tab)

        self.card_width = QSpinBox()
        self.card_width.setRange(100, 400)
        self.card_width.setValue(self.settings["card"]["width"])
        card_layout.addRow("Kart Genişliği:", self.card_width)

        self.card_img_height = QSpinBox()
        self.card_img_height.setRange(100, 400)
        self.card_img_height.setValue(self.settings["card"]["image_height"])
        card_layout.addRow("Görsel Yüksekliği:", self.card_img_height)

        self.card_radius = QSpinBox()
        self.card_radius.setRange(0, 30)
        self.card_radius.setValue(self.settings["card"]["border_radius"])
        card_layout.addRow("Köşe Yuvarlaklığı:", self.card_radius)

        self.card_gap = QSpinBox()
        self.card_gap.setRange(0, 40)
        self.card_gap.setValue(self.settings["carousel"]["gap"])
        card_layout.addRow("Kart Aralığı:", self.card_gap)

        self.card_shadow = QCheckBox("Gölge")
        self.card_shadow.setChecked(self.settings["card"]["shadow_enabled"])
        card_layout.addRow(self.card_shadow)

        self.card_bg_btn = QPushButton("Kart Rengi")
        self.card_bg_btn.clicked.connect(lambda: self.choose_color("card", "background_color"))
        card_layout.addRow("Kart Arka Plan:", self.card_bg_btn)

        tabs.addTab(card_tab, "Kartlar")

        # --- Marka Başlığı sekmesi ---
        brand_tab = QWidget()
        brand_layout = QFormLayout(brand_tab)

        self.brand_font = QFontComboBox()
        self.brand_font.setCurrentFont(QFont(self.settings["brand_header"]["font_family"]))
        brand_layout.addRow("Font:", self.brand_font)

        self.brand_size = QSpinBox()
        self.brand_size.setRange(10, 40)
        self.brand_size.setValue(self.settings["brand_header"]["font_size"])
        brand_layout.addRow("Boyut:", self.brand_size)

        self.brand_bold = QCheckBox("Kalın")
        self.brand_bold.setChecked(self.settings["brand_header"]["font_weight"] == "bold")
        brand_layout.addRow(self.brand_bold)

        self.brand_color_btn = QPushButton("Renk")
        self.brand_color_btn.clicked.connect(lambda: self.choose_color("brand_header", "color"))
        brand_layout.addRow("Renk:", self.brand_color_btn)

        self.section_gap = QSpinBox()
        self.section_gap.setRange(0, 80)
        self.section_gap.setValue(self.settings["sections"]["vertical_gap"])
        brand_layout.addRow("Bölüm Aralığı:", self.section_gap)

        tabs.addTab(brand_tab, "Marka Başlığı")

        layout.addWidget(tabs)

        # --- Canlı önizleme ---
        layout.addWidget(QLabel("Önizleme"))
        self.preview_widget = QLabel()
        self.preview_widget.setFixedHeight(150)
        self.preview_widget.setStyleSheet("background-color:white; border:1px solid #ccc;")
        layout.addWidget(self.preview_widget)

        # --- Butonlar ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # --- Sinyal bağlantıları (her widget tipi için ayrı ayrı) ---
        for spin in self.findChildren(QSpinBox):
            spin.valueChanged.connect(self.update_preview)
        for check in self.findChildren(QCheckBox):
            check.toggled.connect(self.update_preview)
        for combo in self.findChildren(QComboBox):
            combo.currentIndexChanged.connect(self.update_preview)
        # QLineEdit için textChanged
        for ledit in self.findChildren(QLineEdit):
            ledit.textChanged.connect(self.update_preview)
        # QFontComboBox da bir QComboBox türevidir, currentFontChanged daha spesifik olabilir ama currentIndexChanged de çalışır.
        for fcombo in self.findChildren(QFontComboBox):
            fcombo.currentFontChanged.connect(self.update_preview)

    def choose_color(self, section, key=None):
        if key:
            current = self.settings[section][key]
        else:
            current = self.settings[section] if isinstance(self.settings[section], str) else self.settings[section]
        color = QColorDialog.getColor(QColor(current), self)
        if color.isValid():
            if key:
                self.settings[section][key] = color.name()
            else:
                self.settings[section] = color.name()
            self.update_preview()

    def update_preview(self):
        # Güncel değerleri al
        self.settings["title"]["text"] = self.title_edit.text()
        self.settings["title"]["font_family"] = self.title_font.currentFont().family()
        self.settings["title"]["font_size"] = self.title_size.value()
        self.settings["title"]["font_weight"] = "bold" if self.title_bold.isChecked() else "normal"
        self.settings["background_color"] = self.settings.get("background_color", "#F5F5F5")
        self.settings["card"]["width"] = self.card_width.value()
        self.settings["card"]["image_height"] = self.card_img_height.value()
        self.settings["card"]["border_radius"] = self.card_radius.value()
        self.settings["carousel"]["gap"] = self.card_gap.value()
        self.settings["card"]["shadow_enabled"] = self.card_shadow.isChecked()
        self.settings["brand_header"]["font_family"] = self.brand_font.currentFont().family()
        self.settings["brand_header"]["font_size"] = self.brand_size.value()
        self.settings["brand_header"]["font_weight"] = "bold" if self.brand_bold.isChecked() else "normal"
        self.settings["sections"]["vertical_gap"] = self.section_gap.value()

        # Önizleme çizimi
        pix = QPixmap(self.preview_widget.width(), self.preview_widget.height())
        pix.fill(QColor(self.settings["background_color"]))
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)

        # Başlık
        title_font = QFont(self.settings["title"]["font_family"], self.settings["title"]["font_size"])
        title_font.setBold(self.settings["title"]["font_weight"] == "bold")
        painter.setFont(title_font)
        painter.setPen(QColor(self.settings["title"]["color"]))
        painter.drawText(10, 30, self.settings["title"]["text"])

        # Örnek kart
        card_x = 20
        card_y = 50
        card_w = self.settings["card"]["width"]
        card_h = self.settings["card"]["image_height"] + 30
        painter.setBrush(QColor(self.settings["card"]["background_color"]))
        painter.setPen(QPen(QColor(self.settings["card"]["border_color"]), self.settings["card"]["border_width"]))
        painter.drawRoundedRect(card_x, card_y, card_w, card_h,
                                self.settings["card"]["border_radius"], self.settings["card"]["border_radius"])

        # Marka başlığı
        brand_font = QFont(self.settings["brand_header"]["font_family"], self.settings["brand_header"]["font_size"])
        brand_font.setBold(self.settings["brand_header"]["font_weight"] == "bold")
        painter.setFont(brand_font)
        painter.setPen(QColor(self.settings["brand_header"]["color"]))
        painter.drawText(card_x, card_y - 5, "OPEL")

        painter.end()
        self.preview_widget.setPixmap(pix)

    def save_settings(self):
        self.update_preview()
        self.data_manager.data.home_page_settings = self.settings
        self.data_manager.save()
        self.accept()