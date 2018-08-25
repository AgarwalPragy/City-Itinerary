from typing import Optional, Dict, NewType, List, TypeVar, Union, NamedTuple

from dataclasses import dataclass, field
import json
from uuid import uuid4

from jsonUtils import J, EnhancedJSONEncoder

__all__ = [
    'Review', 'ImageResource',
    'CityID', 'CountryID', 'PointID',
    'JEA', 'JEL', 'JPA', 'JPL', 'JKA', 'JKL', 'JCA', 'JCL', 'JIL', 'JRL',
    'EntityListing', 'CountryListing', 'CityListing', 'PointListing',
    'EntityAggregated', 'CountryAggregated', 'CityAggregated', 'PointAggregated'
]

JKA = NewType('JKA', J)  # Kountry
JKL = NewType('JKL', J)

JCA = NewType('JCA', J)  # City
JCL = NewType('JCL', J)

JPA = NewType('JPA', J)  # Point
JPL = NewType('JPL', J)

JIL = NewType('JIL', J)  # Image
JRL = NewType('JRL', J)  # Review

JEA = Union[JKA, JCA, JPA]  # Entity
JEL = Union[JKL, JCL, JPL, JIL, JRL]


class CountryID(NamedTuple):
    countryName: str


class CityID(NamedTuple):
    countryName: str
    cityName: str


class PointID(NamedTuple):
    countryName: str
    cityName: str
    pointName: str


@dataclass
class EntityAggregated:
    _entityType: str = field(init=False)
    _uuid: str = field(init=False)
    sources: List[str] = field(init=False)  # this will be a list of UUIDs of listings

    def jsonify(self) -> JEA:
        # TODO: Make this more efficient
        return json.loads(json.dumps(self, cls=EnhancedJSONEncoder))

    def __post_init__(self):
        self._entityType = 'undefined'
        self._uuid = 'none'
        self.sources = []


@dataclass
class EntityListing:
    crawler: str
    sourceURL: str
    crawlTimestamp: str
    _listingType: str = field(init=False)
    _uuid: str = field(init=False)

    def jsonify(self) -> JEL:
        # TODO: Make this more efficient
        return json.loads(json.dumps(self, cls=EnhancedJSONEncoder))

    def __post_init__(self):
        self._listingType = 'undefined'
        self._uuid = 'none'


@dataclass
class Country:
    countryName: str
    coordinates: Optional[str] = None


@dataclass
class City:
    countryName: str

    cityName: str
    # Note: A city should be uniquely identified by it's name and parent country.
    # Region is just extra info.
    regionName: Optional[str] = None
    coordinates: Optional[str] = None
    recommendedNumDays: Optional[int] = None
    avgRating: Optional[float] = None  # Ratings must be scaled to out-of-10 before logging
    ratingCount: Optional[int] = None


@dataclass
class Point:
    countryName: str
    cityName: str

    pointName: str
    address: Optional[str] = None
    coordinates: Optional[str] = None
    openingHour: Optional[str] = None
    closingHour: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    canEat: Optional[bool] = None
    canStay: Optional[bool] = None
    canTour: Optional[bool] = None
    category: Optional[str] = None
    tripexpertScore: Optional[int] = None # out of 100
    website: Optional[str] = None
    avgRating: Optional[float] = None  # Ratings must be scaled to out-of-10 before logging
    ratingCount: Optional[int] = None
    rank: Optional[int] = None
    priceLevel: Optional[str] = None
    contact: Optional[str] = None 
    recommendedNumHours: Optional[int] = None


@dataclass
class ImageResource(EntityListing):
    countryName: str
    imageURL: str

    cityName: Optional[str] = None
    pointName: Optional[str] = None

    def __post_init__(self):
        self._listingType = 'imageResource'
        self._uuid = str(uuid4())


@dataclass
class Review(EntityListing):
    countryName: str
    cityName: Optional[str] = None
    pointName: Optional[str] = None

    date: Optional[str] = None
    content: Optional[str] = None
    rating: Optional[float] = None  # Ratings must be scaled to out-of-10 before logging

    def __post_init__(self):
        self._listingType = 'review'
        self._uuid = str(uuid4())
# ------------------------------------------------------------------------------


@dataclass
class CountryAggregated(Country, EntityAggregated):
    def __post_init__(self):
        self._entityType = 'country'
        self._uuid = str(uuid4())
        self.sources = []


@dataclass
class CountryListing(Country, EntityListing):
    def __post_init__(self):
        self._listingType = 'country'
        self._uuid = str(uuid4())


@dataclass
class CityAggregated(City, EntityAggregated):
    def __post_init__(self):
        self._entityType = 'city'
        self._uuid = str(uuid4())
        self.sources = []


@dataclass
class CityListing(City, EntityListing):
    def __post_init__(self):
        self._listingType = 'city'
        self._uuid = str(uuid4())


@dataclass
class PointAggregated(Point, EntityAggregated):
    def __post_init__(self):
        self._entityType = 'point'
        self._uuid = str(uuid4())
        self.sources = []


@dataclass
class PointListing(Point, EntityListing):
    def __post_init__(self):
        self._listingType = 'point'
        self._uuid = str(uuid4())

