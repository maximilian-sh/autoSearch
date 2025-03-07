from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class CarListing:
    id: str
    make: str
    model: str
    price: int
    year: int
    kilometers: int
    location: str
    url: str
    first_seen: datetime
    last_seen: datetime
    title: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self):
        return {
            'id': self.id,
            'make': self.make,
            'model': self.model,
            'price': self.price,
            'year': self.year,
            'kilometers': self.kilometers,
            'location': self.location,
            'url': self.url,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'title': self.title,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: dict):
        data['first_seen'] = datetime.fromisoformat(data['first_seen'])
        data['last_seen'] = datetime.fromisoformat(data['last_seen'])
        return cls(**data) 