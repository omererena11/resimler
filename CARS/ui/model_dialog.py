import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QFileDialog, QLabel, QSpinBox, QDialogButtonBox,
    QMessageBox, QTextEdit, QScrollArea, QWidget, QCheckBox, QFrame,
    QGroupBox, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
from PySide6.QtGui import QPixmap, QDrag, QMouseEvent
import config
from core.data_manager import DataManager
from core.image_manager import ImageManager

# Kategori seçenekleri
VEHICLE_TYPES = [
    ("Otomobil", "otomobil"),
    ("Arazi / SUV", "suv"),
    ("Elektrikli Araç", "elektrikli"),
    ("Hibrit", "hibrit")
]

FUEL_TYPES = [
    ("Benzin", "benzin"),
    ("Dizel", "dizel"),
    ("Hibrit", "hibrit"),
    ("Elektrik", "elektrik"),
    ("LPG", "lpg")
]

TRANSMISSIONS = [
    ("Manuel", "manuel"),
    ("Otomatik", "otomatik")
]

BODY_TYPES = [
    ("Cabrio", "cabrio"),
    ("Coupe", "coupe"),
    ("Coupe 4 kapı", "coupe_4"),
    ("Hatchback 3 kapı", "hatchback_3"),
    ("Hatchback 5 kapı", "hatchback_5"),
    ("Sedan", "sedan"),
    ("Station Wagon", "station_wagon"),
    ("MPV", "mpv"),
    ("Roadster", "roadster")
]


class DraggableImageFrame(QFrame):
    """Sürükle-bırak ile sıralanabilen büyük görsel çerçevesi."""
    order_changed = Signal(int, int)  # from_idx, to_idx

    def __init__(self, file_path, index, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.index = index
        self.setFixedSize(120, 100)
        self.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 4px; background: white; }")
        self.setAcceptDrops(True)
        self.drag_start_pos = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self.image_label = QLabel()
        self.image_label.setFixedSize(110, 70)
        self.image_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(file_path)
        self.image_label.setPixmap(pixmap.scaled(110, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(self.image_label)

        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedSize(20, 20)
        self.delete_btn.setStyleSheet("QPushButton { color: red; font-weight: bold; border: none; background: transparent; }")
        layout.addWidget(self.delete_btn, alignment=Qt.AlignRight)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton and self.drag_start_pos:
            if (event.pos() - self.drag_start_pos).manhattanLength() > 10:
                self.start_drag()
                self.drag_start_pos = None
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_start_pos = None
        super().mouseReleaseEvent(event)

    def start_drag(self):
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(str(self.index))
        drag.setMimeData(mime)
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(60, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        drag.exec(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.source() != self:
            event.acceptProposedAction()
            self.setStyleSheet("QFrame { border: 2px dashed #2563EB; border-radius: 4px; background: #EFF6FF; }")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 4px; background: white; }")

    def dropEvent(self, event):
        source_idx = int(event.mimeData().text())
        if source_idx != self.index:
            self.order_changed.emit(source_idx, self.index)
            event.acceptProposedAction()
        else:
            event.ignore()
        self.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 4px; background: white; }")


class ModelDialog(QDialog):
    def __init__(self, data_manager: DataManager, brand_id: str, car_id: str = None, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.brand_id = brand_id
        self.car_id = car_id
        self.brand = data_manager.data.get_brand_by_id(brand_id)
        self.car = self.brand.get_model_by_id(car_id) if car_id and self.brand else None

        # Görsel yönetimi
        self.thumb_path = None
        self.large_image_paths = []  # yeni seçilen dosya yolları
        self.large_image_frames = []  # DraggableImageFrame listesi
        self.existing_large_images = []  # mevcut rel_path'ler

        self.setWindowTitle("Model Düzenle" if self.car else "Yeni Model")
        self.setMinimumWidth(620)
        self.setMinimumHeight(700)
        self.setup_ui()
        if self.car:
            self.load_car_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # ===== TEMEL BİLGİLER =====
        basic_group = QGroupBox("Temel Bilgiler")
        basic_form = QFormLayout(basic_group)

        self.brand_label = QLabel(self.brand.name if self.brand else "")
        basic_form.addRow("Marka:", self.brand_label)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Model adı")
        basic_form.addRow("Model Adı:", self.name_edit)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(2026)
        basic_form.addRow("Yıl:", self.year_spin)

        self.price_edit = QLineEdit()
        self.price_edit.setPlaceholderText("örn: 1.850.000 TL")
        basic_form.addRow("Fiyat:", self.price_edit)

        scroll_layout.addWidget(basic_group)

        # ===== KATEGORİ BİLGİLERİ =====
        category_group = QGroupBox("Kategori Bilgileri")
        category_layout = QVBoxLayout(category_group)

        # Vasıta
        vehicle_label = QLabel("<b>Vasıta</b>")
        category_layout.addWidget(vehicle_label)
        self.vehicle_checkboxes = {}
        vehicle_grid = QGridLayout()
        for i, (label, value) in enumerate(VEHICLE_TYPES):
            cb = QCheckBox(label)
            self.vehicle_checkboxes[value] = cb
            vehicle_grid.addWidget(cb, i // 2, i % 2)
        category_layout.addLayout(vehicle_grid)

        # Yakıt
        fuel_label = QLabel("<b>Yakıt Tipi</b>")
        category_layout.addWidget(fuel_label)
        self.fuel_checkboxes = {}
        fuel_grid = QGridLayout()
        for i, (label, value) in enumerate(FUEL_TYPES):
            cb = QCheckBox(label)
            self.fuel_checkboxes[value] = cb
            fuel_grid.addWidget(cb, i // 3, i % 3)
        category_layout.addLayout(fuel_grid)

        # Vites
        transmission_label = QLabel("<b>Vites</b>")
        category_layout.addWidget(transmission_label)
        self.transmission_checkboxes = {}
        trans_layout = QHBoxLayout()
        for label, value in TRANSMISSIONS:
            cb = QCheckBox(label)
            self.transmission_checkboxes[value] = cb
            trans_layout.addWidget(cb)
        trans_layout.addStretch()
        category_layout.addLayout(trans_layout)

        # Kasa Tipi
        body_label = QLabel("<b>Kasa Tipi</b>")
        category_layout.addWidget(body_label)
        self.body_checkboxes = {}
        body_grid = QGridLayout()
        for i, (label, value) in enumerate(BODY_TYPES):
            cb = QCheckBox(label)
            self.body_checkboxes[value] = cb
            body_grid.addWidget(cb, i // 3, i % 3)
        category_layout.addLayout(body_grid)

        scroll_layout.addWidget(category_group)

        # ===== TEKNİK BİLGİLER =====
        tech_group = QGroupBox("Teknik Bilgiler")
        tech_form = QFormLayout(tech_group)

        self.fuel_edit = QLineEdit()
        self.fuel_edit.setPlaceholderText("örn: Hibrit, Benzin")
        tech_form.addRow("Yakıt:", self.fuel_edit)

        self.engine_edit = QLineEdit()
        self.engine_edit.setPlaceholderText("örn: 1.8")
        tech_form.addRow("Motor:", self.engine_edit)

        self.power_edit = QLineEdit()
        self.power_edit.setPlaceholderText("örn: 140 HP")
        tech_form.addRow("Güç:", self.power_edit)

        self.torque_edit = QLineEdit()
        self.torque_edit.setPlaceholderText("örn: 190 Nm")
        tech_form.addRow("Tork:", self.torque_edit)

        self.transmission_edit = QLineEdit()
        self.transmission_edit.setPlaceholderText("örn: e-CVT")
        tech_form.addRow("Şanzıman:", self.transmission_edit)

        self.drivetrain_edit = QLineEdit()
        self.drivetrain_edit.setPlaceholderText("örn: Önden Çekiş")
        tech_form.addRow("Çekiş Sistemi:", self.drivetrain_edit)

        self.trunk_edit = QLineEdit()
        self.trunk_edit.setPlaceholderText("örn: 361 L")
        tech_form.addRow("Bagaj Hacmi:", self.trunk_edit)

        self.acceleration_edit = QLineEdit()
        self.acceleration_edit.setPlaceholderText("örn: 9.1 sn")
        tech_form.addRow("0-100 km/s:", self.acceleration_edit)

        self.max_speed_edit = QLineEdit()
        self.max_speed_edit.setPlaceholderText("örn: 180 km/s")
        tech_form.addRow("Maksimum Hız:", self.max_speed_edit)

        size_layout = QHBoxLayout()
        self.length_edit = QLineEdit()
        self.length_edit.setPlaceholderText("Uzunluk")
        self.width_edit = QLineEdit()
        self.width_edit.setPlaceholderText("Genişlik")
        self.height_edit = QLineEdit()
        self.height_edit.setPlaceholderText("Yükseklik")
        size_layout.addWidget(self.length_edit)
        size_layout.addWidget(self.width_edit)
        size_layout.addWidget(self.height_edit)
        tech_form.addRow("Boyutlar (mm):", size_layout)

        self.displacement_edit = QLineEdit()
        self.displacement_edit.setPlaceholderText("örn: 1798 cc")
        tech_form.addRow("Motor Hacmi:", self.displacement_edit)

        scroll_layout.addWidget(tech_group)

        # ===== AÇIKLAMA =====
        desc_group = QGroupBox("Açıklama")
        desc_layout = QFormLayout(desc_group)

        self.card_desc_edit = QTextEdit()
        self.card_desc_edit.setMaximumHeight(60)
        self.card_desc_edit.setPlaceholderText("Kart açıklaması (kısa)...")
        desc_layout.addRow("Kart Açıklaması:", self.card_desc_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Detaylı açıklama...")
        desc_layout.addRow("Detay Açıklama:", self.description_edit)

        self.equipment_edit = QTextEdit()
        self.equipment_edit.setMaximumHeight(80)
        self.equipment_edit.setPlaceholderText("Donanım bilgileri...")
        desc_layout.addRow("Donanım:", self.equipment_edit)

        scroll_layout.addWidget(desc_group)

        # ===== GÖRSELLER =====
        image_group = QGroupBox("Görseller")
        image_layout = QVBoxLayout(image_group)

        # Thumbnail
        thumb_header = QHBoxLayout()
        thumb_header.addWidget(QLabel("<b>Thumbnail (640x360)</b>"))
        thumb_header.addStretch()
        thumb_btn = QPushButton("Seç")
        thumb_btn.clicked.connect(self.select_thumbnail)
        thumb_header.addWidget(thumb_btn)
        image_layout.addLayout(thumb_header)

        self.thumb_preview = QLabel()
        self.thumb_preview.setFixedSize(160, 90)
        self.thumb_preview.setAlignment(Qt.AlignCenter)
        self.thumb_preview.setStyleSheet("background: #eee; border: 1px solid #ccc; border-radius: 4px;")
        self.thumb_preview.setText("640×360")
        image_layout.addWidget(self.thumb_preview)

        # Büyük Görseller
        large_header = QHBoxLayout()
        large_header.addWidget(QLabel("<b>Büyük Görseller (1920x1080)</b>"))
        large_header.addStretch()
        add_large_btn = QPushButton("+ Görsel Ekle")
        add_large_btn.clicked.connect(self.add_large_images)
        large_header.addWidget(add_large_btn)
        image_layout.addLayout(large_header)

        self.large_images_container = QWidget()
        self.large_images_layout = QHBoxLayout(self.large_images_container)
        self.large_images_layout.setAlignment(Qt.AlignLeft)
        self.large_images_layout.setSpacing(8)
        image_layout.addWidget(self.large_images_container)

        scroll_layout.addWidget(image_group)

        # ===== ANASAYFA AYARLARI =====
        homepage_group = QGroupBox("Anasayfa Ayarları")
        homepage_layout = QFormLayout(homepage_group)

        self.homepage_check = QCheckBox("Anasayfada göster")
        self.homepage_check.setChecked(True)
        homepage_layout.addRow(self.homepage_check)

        self.show_year_check = QCheckBox("Yılı göster")
        self.show_year_check.setChecked(True)
        homepage_layout.addRow(self.show_year_check)

        self.show_desc_check = QCheckBox("Açıklamayı göster")
        self.show_desc_check.setChecked(False)
        homepage_layout.addRow(self.show_desc_check)

        self.order_spin = QSpinBox()
        self.order_spin.setMinimum(1)
        self.order_spin.setMaximum(999)
        max_order = max([c.order for c in self.brand.models], default=0) if self.brand else 0
        self.order_spin.setValue(max_order + 1)
        homepage_layout.addRow("Sıra:", self.order_spin)

        scroll_layout.addWidget(homepage_group)

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Butonlar
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def load_car_data(self):
        self.name_edit.setText(self.car.name)
        self.year_spin.setValue(self.car.year)
        self.price_edit.setText(self.car.price)
        self.fuel_edit.setText(self.car.fuel)
        self.engine_edit.setText(self.car.engine)
        self.power_edit.setText(self.car.power)
        self.torque_edit.setText(self.car.torque)
        self.transmission_edit.setText(self.car.transmission)
        self.drivetrain_edit.setText(self.car.drivetrain)
        self.trunk_edit.setText(self.car.trunk_volume)
        self.acceleration_edit.setText(self.car.acceleration)
        self.max_speed_edit.setText(self.car.max_speed)
        self.length_edit.setText(self.car.length)
        self.width_edit.setText(self.car.width)
        self.height_edit.setText(self.car.height)
        self.displacement_edit.setText(self.car.displacement)
        self.card_desc_edit.setPlainText(self.car.card_description)
        self.description_edit.setPlainText(self.car.description)
        self.equipment_edit.setPlainText(self.car.equipment)

        self.homepage_check.setChecked(self.car.show_on_homepage)
        self.show_year_check.setChecked(self.car.show_year)
        self.show_desc_check.setChecked(self.car.show_description)
        self.order_spin.setValue(self.car.order)

        # Kategori checkbox'larını yükle
        for value, cb in self.vehicle_checkboxes.items():
            cb.setChecked(value in self.car.vehicle_types)
        for value, cb in self.fuel_checkboxes.items():
            cb.setChecked(value in self.car.fuel_types)
        for value, cb in self.transmission_checkboxes.items():
            cb.setChecked(value in self.car.transmissions_list)
        for value, cb in self.body_checkboxes.items():
            cb.setChecked(value in self.car.body_types)

        # Mevcut thumbnail
        if self.car.thumbnail:
            thumb_full = os.path.join(config.DATA_DIR, self.car.thumbnail)
            if os.path.exists(thumb_full):
                self.thumb_preview.setPixmap(QPixmap(thumb_full).scaled(160, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        # Mevcut büyük görseller
        for rel_path in self.car.large_images:
            full_path = os.path.join(config.DATA_DIR, rel_path)
            if os.path.exists(full_path):
                self.existing_large_images.append(rel_path)
                frame = self.create_large_image_frame(full_path, len(self.existing_large_images) - 1, is_existing=True)
                self.large_images_layout.addWidget(frame)
                self.large_image_frames.append(frame)

    def select_thumbnail(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Thumbnail Seç (640x360)", "",
            "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.webp);;Tüm Dosyalar (*)"
        )
        if file_path:
            self.thumb_path = file_path
            self.thumb_preview.setPixmap(QPixmap(file_path).scaled(160, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def add_large_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Büyük Görseller Seç (1920x1080)", "",
            "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.webp);;Tüm Dosyalar (*)"
        )
        for f in files:
            self.large_image_paths.append(f)
            idx = len(self.large_image_frames)
            frame = self.create_large_image_frame(f, idx)
            self.large_images_layout.addWidget(frame)
            self.large_image_frames.append(frame)

    def create_large_image_frame(self, file_path, index, is_existing=False):
        frame = DraggableImageFrame(file_path, index)
        frame.delete_btn.clicked.connect(lambda: self.remove_large_image(frame, is_existing))
        frame.order_changed.connect(self.reorder_large_images)
        return frame

    def remove_large_image(self, frame, is_existing):
        self.large_images_layout.removeWidget(frame)
        frame.deleteLater()
        if frame in self.large_image_frames:
            idx = self.large_image_frames.index(frame)
            self.large_image_frames.remove(frame)
            if not is_existing and idx < len(self.large_image_paths):
                self.large_image_paths.pop(idx)
            elif is_existing and idx < len(self.existing_large_images):
                self.existing_large_images.pop(idx)
        # İndeksleri güncelle
        for i, f in enumerate(self.large_image_frames):
            f.index = i

    def reorder_large_images(self, from_idx, to_idx):
        # existing listeleri yeniden sırala
        if from_idx < len(self.existing_large_images):
            item = self.existing_large_images.pop(from_idx)
            self.existing_large_images.insert(to_idx, item)
        elif from_idx < len(self.existing_large_images) + len(self.large_image_paths):
            new_idx = from_idx - len(self.existing_large_images)
            item = self.large_image_paths.pop(new_idx)
            insert_pos = to_idx - len(self.existing_large_images)
            self.large_image_paths.insert(insert_pos, item)

        # Frame'leri yeniden sırala
        frame = self.large_image_frames.pop(from_idx)
        self.large_image_frames.insert(to_idx, frame)

        # Layout'u yeniden oluştur
        while self.large_images_layout.count():
            child = self.large_images_layout.takeAt(0)
            if child.widget():
                self.large_images_layout.removeWidget(child.widget())

        for i, f in enumerate(self.large_image_frames):
            f.index = i
            self.large_images_layout.addWidget(f)

    def on_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Model adı boş olamaz.")
            return

        year = self.year_spin.value()

        # Kategori değerlerini topla
        vehicle_types = [v for v, cb in self.vehicle_checkboxes.items() if cb.isChecked()]
        fuel_types = [v for v, cb in self.fuel_checkboxes.items() if cb.isChecked()]
        transmissions = [v for v, cb in self.transmission_checkboxes.items() if cb.isChecked()]
        body_types = [v for v, cb in self.body_checkboxes.items() if cb.isChecked()]

        car_data = {
            "name": name,
            "year": year,
            "price": self.price_edit.text().strip(),
            "fuel": self.fuel_edit.text().strip(),
            "engine": self.engine_edit.text().strip(),
            "power": self.power_edit.text().strip(),
            "torque": self.torque_edit.text().strip(),
            "transmission": self.transmission_edit.text().strip(),
            "drivetrain": self.drivetrain_edit.text().strip(),
            "trunk_volume": self.trunk_edit.text().strip(),
            "acceleration": self.acceleration_edit.text().strip(),
            "max_speed": self.max_speed_edit.text().strip(),
            "length": self.length_edit.text().strip(),
            "width": self.width_edit.text().strip(),
            "height": self.height_edit.text().strip(),
            "displacement": self.displacement_edit.text().strip(),
            "card_description": self.card_desc_edit.toPlainText().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "equipment": self.equipment_edit.toPlainText().strip(),
            "show_on_homepage": self.homepage_check.isChecked(),
            "show_year": self.show_year_check.isChecked(),
            "show_description": self.show_desc_check.isChecked(),
            "order": self.order_spin.value(),
            "homepage_order": 1,
            "vehicle_types": vehicle_types,
            "fuel_types": fuel_types,
            "transmissions_list": transmissions,  # parametre adı transmissions_list
            "body_types": body_types
        }

        if self.car_id:  # Düzenleme
            # Thumbnail
            if self.thumb_path:
                thumb_rel = os.path.relpath(
                    ImageManager.create_thumbnail(self.thumb_path,
                        os.path.join(config.CARS_DIR, self.brand_id),
                        f"{self.car_id}_thumb.webp"),
                    config.DATA_DIR).replace("\\", "/")
                car_data["thumbnail"] = thumb_rel

            # Büyük görselleri birleştir
            final_large = self.existing_large_images.copy()
            if self.large_image_paths:
                large_rels = ImageManager.create_large_images(
                    self.large_image_paths,
                    os.path.join(config.CARS_DIR, self.brand_id),
                    self.car_id
                )
                final_large.extend(large_rels)
            car_data["large_images"] = final_large

            self.data_manager.update_car(self.brand_id, self.car_id, car_data)
        else:  # Yeni ekleme
            new_car = self.data_manager.add_car(self.brand_id, car_data)
            if not new_car:
                QMessageBox.critical(self, "Hata", "Model eklenemedi.")
                return

            # Thumbnail
            if self.thumb_path:
                thumb_rel = os.path.relpath(
                    ImageManager.create_thumbnail(self.thumb_path,
                        os.path.join(config.CARS_DIR, self.brand_id),
                        f"{new_car.id}_thumb.webp"),
                    config.DATA_DIR).replace("\\", "/")
                self.data_manager.update_car(self.brand_id, new_car.id, {"thumbnail": thumb_rel})

            # Büyük görseller
            if self.large_image_paths:
                large_rels = ImageManager.create_large_images(
                    self.large_image_paths,
                    os.path.join(config.CARS_DIR, self.brand_id),
                    new_car.id
                )
                self.data_manager.update_car(self.brand_id, new_car.id, {"large_images": large_rels})

        self.accept()