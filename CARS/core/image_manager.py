import os
from PIL import Image
import config

class ImageManager:
    @staticmethod
    def create_thumbnail(source_path: str, dest_dir: str, filename: str) -> str:
        """640x360 thumbnail oluşturur (16:9)."""
        os.makedirs(dest_dir, exist_ok=True)
        thumb_path = os.path.join(dest_dir, filename)
        img = Image.open(source_path).convert("RGB")
        img.thumbnail((640, 360), Image.LANCZOS)
        img.save(thumb_path, "webp", quality=85)
        return thumb_path

    @staticmethod
    def create_large_images(source_paths: list, dest_dir: str, base_filename: str) -> list:
        """1920x1080 büyük görseller oluşturur, relatif yol listesi döndürür."""
        os.makedirs(dest_dir, exist_ok=True)
        rel_paths = []
        for idx, src in enumerate(source_paths):
            filename = f"{base_filename}_{idx+1}.webp"
            large_path = os.path.join(dest_dir, filename)
            img = Image.open(src).convert("RGB")
            img.thumbnail((1920, 1080), Image.LANCZOS)
            img.save(large_path, "webp", quality=90)
            rel_paths.append(os.path.relpath(large_path, config.DATA_DIR).replace("\\", "/"))
        return rel_paths

    @staticmethod
    def copy_logo(source_path: str, brand_id: str) -> str:
        dest_dir = config.BRANDS_DIR
        filename = f"{brand_id}.webp"
        return ImageManager.create_thumbnail(source_path, dest_dir, filename)