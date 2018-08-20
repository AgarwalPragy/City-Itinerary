from typing import Optional, Dict, Any
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import dataclasses
import json

__all__ = ['Review', 'EntityListing', 'Coordinate', 'CountryListing', 'CityListing', 'PointListing', 'ImageResource']


class EnhancedJSONEncoder(json.JSONEncoder):
    # https://stackoverflow.com/a/51286749/2570622
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class Coordinate:
    pass


@dataclass
class EntityListing:
    crawler: str
    sourceURL: str
    crawlTimestamp: str
    _listingType: str = field(init=False)

    def jsonify(self) -> Dict[str, Any]:
        # TODO: Make this more efficient
        return json.loads(json.dumps(self, cls=EnhancedJSONEncoder))

    def __post_init__(self):
        self._listingType = 'undefined'


@dataclass
class CountryListing(EntityListing):
    countryName: str
    coordinates: Optional[Coordinate] = None

    def __post_init__(self):
        self._listingType = 'country'


@dataclass
class CityListing(EntityListing):
    countryName: str

    cityName: str
    # Note: A city should be uniquely identified by it's name and parent country.
    # Region is just extra info.
    regionName: Optional[str] = None
    coordinates: Optional[Coordinate] = None
    recommendedNumDays: Optional[int] = None
    avgRating: Optional[float] = None  # Ratings must be scaled to out-of-10 before logging
    ratingCount: Optional[int] = None

    def __post_init__(self):
        self._listingType = 'city'


@dataclass
class PointListing(EntityListing):
    countryName: str
    cityName: str

    pointName: str
    address: Optional[str] = None
    coordinates: Optional[Coordinate] = None
    openingHour: Optional[int] = None
    closingHour: Optional[int] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    canEat: Optional[bool] = None
    canStay: Optional[bool] = None
    canTour: Optional[bool] = None
    category: Optional[str] = None
    avgRating: Optional[float] = None  # Ratings must be scaled to out-of-10 before logging
    ratingCount: Optional[int] = None
    rank: Optional[int] = None
    recommendedNumHours: Optional[int] = None

    def __post_init__(self):
        self._listingType = 'point'


@dataclass
class ImageResource(EntityListing):
    countryName: str
    cityName: str
    pointName: str

    imageURL: str

    def __post_init__(self):
        self._listingType = 'imageResource'


@dataclass
class Review(EntityListing):
    countryName: str
    cityName: str
    pointName: Optional[str] = None

    date: Optional[str] = None
    content: Optional[str] = None
    rating: Optional[float] = None  # Ratings must be scaled to out-of-10 before logging

    def __post_init__(self):
        self._listingType = 'review'