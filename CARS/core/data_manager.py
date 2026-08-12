import json, os, re, unicodedata
from datetime import date
from typing import Optional
from .models import DataStore, Brand, Car
import config

class DataManager:
    def __init__(self, data_dir: str = config.DATA_DIR):
        self.data_dir = data_dir
        self.json_path = config.JSON_FILE
        self.brands_dir = config.BRANDS_DIR
        self.cars_dir = config.CARS_DIR
        self.data: Optional[DataStore] = None

    def initialize(self):
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.brands_dir, exist_ok=True)
        os.makedirs(self.cars_dir, exist_ok=True)
        self.load()

    def load(self):
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self.data = DataStore.from_dict(raw)
            except:
                self.data = DataStore()
        else:
            self.data = DataStore()
            self.save()

    def save(self):
        if self.data is None:
            self.data = DataStore()
        self.data.sort_brands()
        for brand in self.data.brands:
            brand.models.sort(key=lambda x: x.order)
        self.data.updated_at = date.today().isoformat()
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.data.to_dict(), f, ensure_ascii=False, indent=2)

    @staticmethod
    def slugify(text: str) -> str:
        text = str(text).lower().strip()
        tr_map = {'ç':'c','ğ':'g','ı':'i','ö':'o','ş':'s','ü':'u',
                  'Ç':'c','Ğ':'g','İ':'i','Ö':'o','Ş':'s','Ü':'u'}
        for tr, en in tr_map.items():
            text = text.replace(tr, en)
        text = unicodedata.normalize('NFKD', text).encode('ascii','ignore').decode('ascii')
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        text = re.sub(r'[\s]+', '-', text)
        text = re.sub(r'-+', '-', text)
        return text.strip('-')

    def generate_brand_id(self, name: str) -> str:
        base = self.slugify(name) or "marka"
        ids = [b.id for b in self.data.brands] if self.data else []
        if base not in ids:
            return base
        i = 1
        while f"{base}-{i}" in ids:
            i += 1
        return f"{base}-{i}"

    def generate_car_id(self, brand_id: str, car_name: str, year: int) -> str:
        base = f"{self.slugify(car_name)}-{year}" if self.slugify(car_name) else f"model-{year}"
        brand = self.data.get_brand_by_id(brand_id) if self.data else None
        existing = [c.id for c in brand.models] if brand else []
        if base not in existing:
            return base
        i = 1
        while f"{base}-{i}" in existing:
            i += 1
        return f"{base}-{i}"

    def add_brand(self, name: str, logo_path: str = "", order: int = None,
                  show_on_homepage: bool = True,
                  show_brand_description: bool = False,
                  brand_description: str = "",
                  brand_description_style: dict = None) -> Brand:
        if self.data is None:
            self.initialize()
        brand_id = self.generate_brand_id(name)
        if not logo_path:
            logo_path = f"brands/{brand_id}.webp"
        if order is None:
            max_order = max([b.order for b in self.data.brands], default=0)
            order = max_order + 1
        brand = Brand(id=brand_id, name=name, logo=logo_path, order=order,
                      show_on_homepage=show_on_homepage,
                      show_brand_description=show_brand_description,
                      brand_description=brand_description,
                      brand_description_style=brand_description_style or {})
        self.data.add_brand(brand)
        self.save()
        return brand

    def update_brand(self, brand_id: str, **kwargs) -> Optional[Brand]:
        brand = self.data.get_brand_by_id(brand_id)
        if not brand:
            return None
        for k, v in kwargs.items():
            if hasattr(brand, k):
                setattr(brand, k, v)
        self.save()
        return brand

    def delete_brand(self, brand_id: str) -> bool:
        if not self.data.get_brand_by_id(brand_id):
            return False
        self.data.remove_brand(brand_id)
        self.save()
        return True

    def add_car(self, brand_id: str, car_data: dict) -> Optional[Car]:
        brand = self.data.get_brand_by_id(brand_id)
        if not brand:
            return None
        car_id = self.generate_car_id(brand_id, car_data.get("name", "Yeni Model"),
                                      car_data.get("year", 2026))
        if "order" not in car_data:
            car_data["order"] = max([c.order for c in brand.models], default=0) + 1
        if "homepage_order" not in car_data:
            car_data["homepage_order"] = 1
        # Yeni liste alanları için varsayılan
        car_data.setdefault("vehicle_types", [])
        car_data.setdefault("fuel_types", [])
        car_data.setdefault("transmissions_list", [])
        car_data.setdefault("body_types", [])
        car_fields = Car.__init__.__code__.co_varnames
        filtered = {k: v for k, v in car_data.items() if k in car_fields}
        car = Car(id=car_id, **filtered)
        brand.add_model(car)
        self.save()
        return car

    def update_car(self, brand_id: str, car_id: str, car_data: dict) -> Optional[Car]:
        brand = self.data.get_brand_by_id(brand_id)
        if not brand:
            return None
        car = brand.get_model_by_id(car_id)
        if not car:
            return None
        for key, value in car_data.items():
            if hasattr(car, key):
                setattr(car, key, value)
        self.save()
        return car

    def delete_car(self, brand_id: str, car_id: str) -> bool:
        brand = self.data.get_brand_by_id(brand_id)
        if not brand:
            return False
        ok = brand.remove_model(car_id)
        if ok:
            self.save()
        return ok

    def reorder_brands(self, ordered_ids: list):
        for order, bid in enumerate(ordered_ids, start=1):
            b = self.data.get_brand_by_id(bid)
            if b:
                b.order = order
        self.save()

    def reorder_cars(self, brand_id: str, ordered_ids: list):
        brand = self.data.get_brand_by_id(brand_id)
        if not brand:
            return
        for order, cid in enumerate(ordered_ids, start=1):
            c = brand.get_model_by_id(cid)
            if c:
                c.order = order
        self.save()