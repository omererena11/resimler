import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
                               QPushButton, QFileDialog, QLabel, QSpinBox, QDialogButtonBox,
                               QMessageBox, QCheckBox, QFontComboBox, QComboBox, QColorDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont, QColor
import config
from core.data_manager import DataManager
from core.image_manager import ImageManager

class BrandDialog(QDialog):
    def __init__(self, data_manager: DataManager, brand_id: str = None, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.brand_id = brand_id
        self.selected_logo_path = None
        self.logo_changed = False
        self.brand = data_manager.data.get_brand_by_id(brand_id) if brand_id else None
        self.current_color = "#1A1C1E"
        self.setWindowTitle("Marka Düzenle" if self.brand else "Yeni Marka")
        self.setMinimumWidth(500)
        self.setup_ui()
        if self.brand: self.load_brand_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit(); self.name_edit.setPlaceholderText("Marka adı")
        form.addRow("Marka Adı:", self.name_edit)

        logo_layout = QHBoxLayout()
        self.logo_label = QLabel(); self.logo_label.setFixedSize(80,80); self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("background:#eee; border:1px solid #ccc;")
        self.logo_label.setText("Logo")
        self.logo_path_display = QLabel("Seçilmedi"); self.logo_path_display.setWordWrap(True)
        select_btn = QPushButton("Fotoğraf Seç"); select_btn.clicked.connect(self.select_logo)
        clear_btn = QPushButton("Temizle"); clear_btn.clicked.connect(self.clear_logo)
        logo_layout.addWidget(self.logo_label)
        r = QVBoxLayout(); r.addWidget(self.logo_path_display)
        rb = QHBoxLayout(); rb.addWidget(select_btn); rb.addWidget(clear_btn); r.addLayout(rb)
        logo_layout.addLayout(r)
        form.addRow("Logo:", logo_layout)

        self.order_spin = QSpinBox(); self.order_spin.setMinimum(1); self.order_spin.setMaximum(999)
        max_order = max([b.order for b in self.data_manager.data.brands], default=0)
        self.order_spin.setValue(max_order+1)
        form.addRow("Sıra:", self.order_spin)

        self.homepage_check = QCheckBox("Ana sayfada göster"); self.homepage_check.setChecked(True)
        form.addRow(self.homepage_check)

        # Marka Açıklaması
        self.show_desc_check = QCheckBox("Marka açıklaması göster"); self.show_desc_check.setChecked(False)
        self.desc_edit = QLineEdit(); self.desc_edit.setPlaceholderText("Örn: 🚀 Yeni Grandland yakında yollarda!")
        self.desc_edit.setEnabled(False)
        self.show_desc_check.toggled.connect(lambda checked: self.desc_edit.setEnabled(checked))
        form.addRow(self.show_desc_check)
        form.addRow("Marka Açıklaması:", self.desc_edit)

        # Açıklama Stili
        style_label = QLabel("<b>Açıklama Stili</b>")
        form.addRow(style_label)

        font_layout = QHBoxLayout()
        self.font_combo = QFontComboBox(); self.font_combo.setCurrentFont(QFont("Arial"))
        font_layout.addWidget(QLabel("Font:")); font_layout.addWidget(self.font_combo)
        self.size_spin = QSpinBox(); self.size_spin.setRange(10, 40); self.size_spin.setValue(14)
        font_layout.addWidget(QLabel("Boyut:")); font_layout.addWidget(self.size_spin)
        form.addRow(font_layout)

        color_layout = QHBoxLayout()
        self.color_btn = QPushButton("Renk"); self.color_btn.clicked.connect(self.choose_color)
        self.color_btn.setStyleSheet(f"background: {self.current_color}; color: white; padding: 4px; border-radius: 4px;")
        color_layout.addWidget(QLabel("Yazı Rengi:")); color_layout.addWidget(self.color_btn)
        self.align_combo = QComboBox(); self.align_combo.addItems(["Sol", "Orta", "Sağ"])
        color_layout.addWidget(QLabel("Hizalama:")); color_layout.addWidget(self.align_combo)
        color_layout.addStretch()
        form.addRow(color_layout)

        # Efekt seçimi
        effect_layout = QHBoxLayout()
        self.effect_combo = QComboBox()
        self.effect_combo.addItem("Yok", "none")
        self.effect_combo.addItem("Kayan Yazı (Marquee)", "marquee")
        self.effect_combo.addItem("Parlama Efekti (Shimmer)", "shimmer")
        effect_layout.addWidget(QLabel("Efekt:")); effect_layout.addWidget(self.effect_combo)
        effect_layout.addStretch()
        form.addRow(effect_layout)

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.on_accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_brand_data(self):
        self.name_edit.setText(self.brand.name)
        self.order_spin.setValue(self.brand.order)
        self.homepage_check.setChecked(self.brand.show_on_homepage)
        self.show_desc_check.setChecked(self.brand.show_brand_description)
        self.desc_edit.setText(self.brand.brand_description)
        self.desc_edit.setEnabled(self.brand.show_brand_description)
        style = self.brand.brand_description_style
        if style:
            if "font_family" in style: self.font_combo.setCurrentFont(QFont(style["font_family"]))
            if "font_size" in style: self.size_spin.setValue(style["font_size"])
            if "color" in style:
                self.current_color = style["color"]
                self.color_btn.setStyleSheet(f"background: {self.current_color}; color: white; padding: 4px; border-radius: 4px;")
            if "text_align" in style:
                idx = self.align_combo.findText(style["text_align"].capitalize())
                if idx >= 0: self.align_combo.setCurrentIndex(idx)
            if "effect" in style:
                idx = self.effect_combo.findData(style["effect"])
                if idx >= 0: self.effect_combo.setCurrentIndex(idx)
        logo_full = os.path.join(config.DATA_DIR, self.brand.logo)
        if os.path.exists(logo_full):
            self.logo_label.setPixmap(QPixmap(logo_full).scaled(80,80,Qt.KeepAspectRatio,Qt.SmoothTransformation))
            self.logo_path_display.setText(self.brand.logo)

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.current_color), self)
        if color.isValid():
            self.current_color = color.name()
            self.color_btn.setStyleSheet(f"background: {self.current_color}; color: white; padding: 4px; border-radius: 4px;")

    def select_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Logo Seç", "", "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.webp)")
        if file_path: self.selected_logo_path = file_path; self.logo_changed = True
        self.logo_label.setPixmap(QPixmap(file_path).scaled(80,80,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        self.logo_path_display.setText(os.path.basename(file_path))

    def clear_logo(self): self.selected_logo_path = None; self.logo_changed = True; self.logo_label.clear(); self.logo_label.setText("Logo"); self.logo_path_display.setText("Seçilmedi")

    def on_accept(self):
        name = self.name_edit.text().strip()
        if not name: QMessageBox.warning(self, "Uyarı", "Marka adı boş olamaz."); return
        order = self.order_spin.value()
        show_home = self.homepage_check.isChecked()
        show_desc = self.show_desc_check.isChecked()
        brand_desc = self.desc_edit.text().strip() if show_desc else ""

        style = {
            "font_family": self.font_combo.currentFont().family(),
            "font_size": self.size_spin.value(),
            "font_weight": "normal",
            "font_style": "normal",
            "color": self.current_color,
            "text_align": self.align_combo.currentText().lower(),
            "effect": self.effect_combo.currentData()
        }

        if self.brand_id:
            kwargs = {
                "name": name, "order": order, "show_on_homepage": show_home,
                "show_brand_description": show_desc, "brand_description": brand_desc,
                "brand_description_style": style
            }
            if self.logo_changed:
                kwargs["logo"] = ImageManager.copy_logo(self.selected_logo_path, self.brand_id) if self.selected_logo_path else ""
            self.data_manager.update_brand(self.brand_id, **kwargs)
        else:
            brand = self.data_manager.add_brand(name, logo_path="", order=order, show_on_homepage=show_home,
                                                show_brand_description=show_desc, brand_description=brand_desc,
                                                brand_description_style=style)
            if self.selected_logo_path:
                logo_rel = ImageManager.copy_logo(self.selected_logo_path, brand.id)
                self.data_manager.update_brand(brand.id, logo=logo_rel)
        self.accept()