from typing import List, Dict
from collections import Counter
from jsonUtils import J
import json

from entities import *
from utilities import *

__all__ = ['getBestName', 'orderImages', 'orderReviews', 'orderPointsOfCity', 'aggregateOneCityFromListings', 'aggregateOneCountryFromListings', 'aggregateOnePointFromListings']


def getBestName(names: List[str], strictness: int=3) -> str:
    """returns the longest name which occurs sufficiently enough
    strictness: [1..100]"""

    # sufficiently enough: in order to remove long but incorrect names
    counts = Counter(names)
    numUnique = len(counts)
    sufficientAmount = counts.most_common(1 + numUnique//strictness)[-1][1]
    
    # get the longest name that occurs atleast sufficientAmount times
    sortedNames = sorted(names, key=len, reverse=True)
    for name in sortedNames:
        if counts[name] >= sufficientAmount:
            return sanitizeName(name)

    # this shouldn't be reached
    # return longest name as a failsafe
    print('CHECK YOUR LOGIC HERE')
    return sanitizeName(sortedNames[0])


def orderImages(jsonImageListings: List[J]) -> List[J]:
    # TODO: Sort images by dimension/quality?
    # return as is for now
    return jsonImageListings


def orderReviews(jsonReviewListings: List[J]) -> List[J]:
    # TODO: Sort reviews by grammar, length, relevancy?
    # return as is for now
    return jsonReviewListings


def aggregateOnePointFromListings(jsonPointListings: List[J], bestCountryName: str, bestCityName: str, bestPointName: str) -> PointAggregated:
    finalPoint = PointAggregated(bestCountryName, bestCityName, bestPointName)
    for listing in jsonPointListings:
        finalPoint.sources.append(listing['_uuid'])

    # DEEPAK: Add logic for aggregating point from listings

    return finalPoint


def orderPointsOfCity(pointsOfCity: List[PointAggregated]) -> List[PointAggregated]:
    # DEEPAK: You have a list of PointAggregated objects.
    # You need to sort this based on your logic
    return pointsOfCity


def aggregateOneCityFromListings(jsonCityListings: List[J], bestCountryName: str, bestCityName: str) -> CityAggregated:
    finalCity = CityAggregated(bestCountryName, bestCityName)
    for listing in jsonCityListings:
        finalCity.sources.append(listing['_uuid'])

    # DEEPAK: Add logic for aggregating city from listings

    return finalCity


def aggregateOneCountryFromListings(jsonCountryListings: List[J], bestCountryName: str) -> CountryAggregated:
    finalCountry = CountryAggregated(bestCountryName)
    for listing in jsonCountryListings:
        finalCountry.sources.append(listing['_uuid'])

    # DEEPAK: Add logic for aggregating country from listings

    return finalCountry
