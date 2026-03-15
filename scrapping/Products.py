from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class Product:
    """Product data structure"""
    brand: str
    name: str
    mrp: float
    cur_price: float
    rating: Optional[float]
    review_count: int
    url: str
    review_summary: Optional[str]
    reviews: list
    platform: str
    
    # New fields
    weight: Optional[str] = None
    net_quantity: Optional[str] = None
    form: Optional[str] = None
    manufacturer: Optional[str] = None
    ingredient_type: Optional[str] = None
    dimension: Optional[str] = None
    country_of_origin: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'brand': self.brand,
            'name': self.name,
            'cur_price': self.cur_price,
            'mrp': self.mrp,
            'rating': self.rating,
            'review_count': self.review_count,
            'url': self.url,
            'review_summary': self.review_summary,
            'platform': self.platform,
            'weight': self.weight,
            'net_quantity': self.net_quantity,
            'form': self.form,
            'manufacturer': self.manufacturer,
            'ingredient_type': self.ingredient_type,
            'dimension': self.dimension,
            'country_of_origin': self.country_of_origin,
            'reviews': self.reviews
        }
