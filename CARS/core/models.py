import json
from typing import List, Optional
from datetime import date

class Car:
    def __init__(
        self,
        id: str,
        name: str,
        year: int,
        thumbnail: str = "",
        large_images: Optional[List[str]] = None,
        order: int = 1,
        show_on_homepage: bool = True,
        homepage_order: int = 1,
        show_year: bool = True,
        show_description: bool = False,
        card_description: str = "",
        caption_style: Optional[dict] = None,
        price: str = "",
        fuel: str = "",
        engine: str = "",
        power: str = "",
        torque: str = "",
        transmission: str = "",
        drivetrain: str = "",
        trunk_volume: str = "",
        acceleration: str = "",
        max_speed: str = "",
        length: str = "",
        width: str = "",
        height: str = "",
        displacement: str = "",
        description: str = "",
        equipment: str = "",
        # YENİ LİSTE ALANLARI
        vehicle_types: Optional[List[str]] = None,
        fuel_types: Optional[List[str]] = None,
        transmissions_list: Optional[List[str]] = None,  # "transmissions" ile çakışmasın diye
        body_types: Optional[List[str]] = None,
        # Geriye uyumluluk
        image: Optional[str] = None,
        images: Optional[List[str]] = None
    ):
        self.id = id
        self.name = name
        self.year = year
        self.order = order
        self.show_on_homepage = show_on_homepage
        self.homepage_order = homepage_order
        self.show_year = show_year
        self.show_description = show_description
        self.card_description = card_description
        self.caption_style = caption_style or {}
        self.price = price
        self.fuel = fuel
        self.engine = engine
        self.power = power
        self.torque = torque
        self.transmission = transmission
        self.drivetrain = drivetrain
        self.trunk_volume = trunk_volume
        self.acceleration = acceleration
        self.max_speed = max_speed
        self.length = length
        self.width = width
        self.height = height
        self.displacement = displacement
        self.description = description
        self.equipment = equipment

        # Yeni liste alanları
        self.vehicle_types = vehicle_types if vehicle_types is not None else []
        self.fuel_types = fuel_types if fuel_types is not None else []
        self.transmissions_list = transmissions_list if transmissions_list is not None else []
        self.body_types = body_types if body_types is not None else []

        # Görsel yönetimi (mevcut)
        if thumbnail:
            self.thumbnail = thumbnail
        elif images and len(images) > 0:
            self.thumbnail = images[0]
        elif image:
            self.thumbnail = image
        else:
            self.thumbnail = ""

        if large_images:
            self.large_images = large_images
        elif images and len(images) > 1:
            self.large_images = images[1:]
        elif images and len(images) == 1:
            self.large_images = [images[0]]
        elif image:
            self.large_images = [image]
        else:
            self.large_images = []

    @property
    def image(self):
        return self.thumbnail

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "year": self.year,
            "thumbnail": self.thumbnail, "large_images": self.large_images,
            "order": self.order, "show_on_homepage": self.show_on_homepage,
            "homepage_order": self.homepage_order,
            "show_year": self.show_year, "show_description": self.show_description,
            "card_description": self.card_description, "caption_style": self.caption_style,
            "price": self.price, "fuel": self.fuel, "engine": self.engine,
            "power": self.power, "torque": self.torque, "transmission": self.transmission,
            "drivetrain": self.drivetrain, "trunk_volume": self.trunk_volume,
            "acceleration": self.acceleration, "max_speed": self.max_speed,
            "length": self.length, "width": self.width, "height": self.height,
            "displacement": self.displacement, "description": self.description,
            "equipment": self.equipment,
            "vehicle_types": self.vehicle_types,
            "fuel_types": self.fuel_types,
            "transmissions": self.transmissions_list,  # JSON'da "transmissions" olarak kaydet
            "body_types": self.body_types
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Car':
        return cls(
            id=data.get("id", ""), name=data.get("name", ""), year=data.get("year", 2026),
            thumbnail=data.get("thumbnail", ""), large_images=data.get("large_images", []),
            order=data.get("order", 1), show_on_homepage=data.get("show_on_homepage", True),
            homepage_order=data.get("homepage_order", 1),
            show_year=data.get("show_year", True), show_description=data.get("show_description", False),
            card_description=data.get("card_description", ""),
            caption_style=data.get("caption_style", {}),
            price=data.get("price", ""), fuel=data.get("fuel", ""), engine=data.get("engine", ""),
            power=data.get("power", ""), torque=data.get("torque", ""), transmission=data.get("transmission", ""),
            drivetrain=data.get("drivetrain", ""), trunk_volume=data.get("trunk_volume", ""),
            acceleration=data.get("acceleration", ""), max_speed=data.get("max_speed", ""),
            length=data.get("length", ""), width=data.get("width", ""), height=data.get("height", ""),
            displacement=data.get("displacement", ""), description=data.get("description", ""),
            equipment=data.get("equipment", ""),
            vehicle_types=data.get("vehicle_types", []),
            fuel_types=data.get("fuel_types", []),
            transmissions_list=data.get("transmissions", []),  # JSON'da "transmissions" anahtarı
            body_types=data.get("body_types", [])
        )


class Brand:
    def __init__(self, id: str, name: str, logo: str, order: int = 1,
                 show_on_homepage: bool = True,
                 show_brand_description: bool = False,
                 brand_description: str = "",
                 brand_description_style: Optional[dict] = None,
                 models: Optional[List[Car]] = None):
        self.id = id
        self.name = name
        self.logo = logo
        self.order = order
        self.show_on_homepage = show_on_homepage
        self.show_brand_description = show_brand_description
        self.brand_description = brand_description
        self.brand_description_style = brand_description_style or {
            "font_family": "Arial", "font_size": 14, "font_weight": "normal",
            "font_style": "normal", "color": "#1A1C1E", "text_align": "left",
            "effect": "none"
        }
        self.models = models if models is not None else []

    def add_model(self, car: Car): self.models.append(car)
    def remove_model(self, car_id: str) -> bool:
        for i, car in enumerate(self.models):
            if car.id == car_id: del self.models[i]; return True
        return False
    def get_model_by_id(self, car_id: str) -> Optional[Car]:
        for car in self.models:
            if car.id == car_id: return car
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "logo": self.logo, "order": self.order,
            "show_on_homepage": self.show_on_homepage,
            "show_brand_description": self.show_brand_description,
            "brand_description": self.brand_description,
            "brand_description_style": self.brand_description_style,
            "models": [car.to_dict() for car in self.models]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Brand':
        brand = cls(
            id=data.get("id", ""), name=data.get("name", ""), logo=data.get("logo", ""),
            order=data.get("order", 1), show_on_homepage=data.get("show_on_homepage", True),
            show_brand_description=data.get("show_brand_description", False),
            brand_description=data.get("brand_description", ""),
            brand_description_style=data.get("brand_description_style", {}),
        )
        for m in data.get("models", []): brand.models.append(Car.from_dict(m))
        brand.models.sort(key=lambda x: x.order)
        return brand


class DataStore:
    def __init__(self):
        self.version = 1
        self.updated_at = date.today().isoformat()
        self.brands: List[Brand] = []
        self.home_page_settings = {
            "background_color": "#F5F5F5",
            "title": {"text": "TÜM OTOMOBİLLER", "font_family": "Arial", "font_size": 24,
                      "font_weight": "bold", "color": "#222222", "text_align": "left"},
            "brand_header": {"font_family": "Arial", "font_size": 20, "font_weight": "bold",
                             "color": "#222222", "text_align": "left", "margin_bottom": 10},
            "card": {"width": 170, "image_height": 140, "background_color": "#FFFFFF",
                     "border_color": "#E5E5E5", "border_width": 1, "border_radius": 12,
                     "padding": 10, "shadow_enabled": True},
            "carousel": {"gap": 12, "scrollbar": False, "scroll_snap": True},
            "sections": {"vertical_gap": 20},
            "caption": {"margin_top": 8}
        }

    def add_brand(self, brand: Brand): self.brands.append(brand)
    def remove_brand(self, brand_id: str) -> bool:
        for i, brand in enumerate(self.brands):
            if brand.id == brand_id: del self.brands[i]; return True
        return False
    def get_brand_by_id(self, brand_id: str) -> Optional[Brand]:
        for brand in self.brands:
            if brand.id == brand_id: return brand
        return None
    def sort_brands(self): self.brands.sort(key=lambda x: x.order)

    def to_dict(self) -> dict:
        self.sort_brands()
        return {
            "version": self.version, "updated_at": self.updated_at,
            "home_page_settings": self.home_page_settings,
            "brands": [brand.to_dict() for brand in self.brands]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DataStore':
        store = cls()
        store.version = data.get("version", 1)
        store.updated_at = data.get("updated_at", date.today().isoformat())
        store.home_page_settings = data.get("home_page_settings", store.home_page_settings)
        for b in data.get("brands", []): store.brands.append(Brand.from_dict(b))
        store.sort_brands()
        return store

    def to_json(self) -> str: return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)