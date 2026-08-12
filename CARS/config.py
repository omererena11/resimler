"""
Sabit yapılandırma değerleri.
"""
import os
import sys

APP_NAME = "OtomobilYonetim"

# Proje ana dizinini bul (main.py'nin olduğu klasör)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Veri dizini: proje/web/data
BASE_DIR = os.path.join(PROJECT_ROOT, "web", "data")

# Alt dizinler
DATA_DIR = BASE_DIR
JSON_FILE = os.path.join(DATA_DIR, "data.json")
BRANDS_DIR = os.path.join(DATA_DIR, "brands")
CARS_DIR = os.path.join(DATA_DIR, "cars")

# Desteklenen görüntü formatları
ALLOWED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

# Fotoğraf optimizasyonu
MAX_IMAGE_WIDTH = 1200
MAX_IMAGE_HEIGHT = 800
IMAGE_QUALITY = 85
THUMBNAIL_SIZE = (200, 150)

# GitHub (ileride kullanılacak)
GITHUB_REPO = ""
GITHUB_BRANCH = "main"

# GitHub Credentials (güvenli saklama)
CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, ".github_credentials")