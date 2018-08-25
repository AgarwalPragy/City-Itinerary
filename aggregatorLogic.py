from typing import List, Dict
from collections import Counter
from collections import defaultdict
from jsonUtils import J
import json

from entities import *
from utilities import *
from siteRankings import alexa_ranking_orderedList
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

def getBestAttributeValue(valueListByCrawler: Dict[str, List]):
    result = None
    for crawler in alexa_ranking_orderedList:
        for value in valueListByCrawler[crawler]:
            if value is not None:
                result = value
                return result
    return result


def aggregateOnePointFromListings(jsonPointListings: List[J], bestCountryName: str, bestCityName: str, bestPointName: str) -> PointAggregated:
    finalPoint = PointAggregated(bestCountryName, bestCityName, bestPointName)

    ignoreAttributes = ['countryName', 'cityName', 'pointName', 'crawler','avgRating', 'ratingCount', 'sourceURL', 'crawlTimestamp', '_uuid', '_listingType']
    attributesValueListByCrawler = defaultdict(lambda: defaultdict(list))

    avgRating, ratingCount = 0, 0
    for listing in jsonPointListings:
        finalPoint.sources.append(listing['_uuid'])

        if listing['avgRating'] is not None:
            if listing['ratingCount'] is not None:
                avgRating += listing['avgRating'] * listing['ratingCount']
                ratingCount += listing['ratingCount']
            else:
                avgRating += listing['avgRating'] # considered at least one person reviewed this listing
                ratingCount += 1

        for attr in listing:
            if attr not in ignoreAttributes:
                if listing['crawler'] in attributesValueListByCrawler[attr]:
                    attributesValueListByCrawler[attr][listing['crawler']].append(listing[attr])
                else:
                    attributesValueListByCrawler[attr][listing['crawler']] = [listing[attr]]

    if ratingCount != 0:
        finalPoint.avgRating = avgRating/ratingCount
    else:
        finalPoint.avgRating = 0
    finalPoint.ratingCount = ratingCount
    # get best props value
    address = getBestAttributeValue(attributesValueListByCrawler['address'])
    coordinates = getBestAttributeValue(attributesValueListByCrawler['coordinates'])
    finalPoint.address = address
    finalPoint.coordinates = coordinates

    openingHour = getBestAttributeValue(attributesValueListByCrawler['openingHour'])
    closingHour = getBestAttributeValue(attributesValueListByCrawler['closingHour'])
    recommendedNumHours = getBestAttributeValue(attributesValueListByCrawler['recommendedNumHours'])
    finalPoint.openingHour = openingHour
    finalPoint.closingHour = closingHour
    finalPoint.recommendedNumHours = recommendedNumHours

    description = getBestAttributeValue(attributesValueListByCrawler['description'])
    notes = getBestAttributeValue(attributesValueListByCrawler['notes'])
    finalPoint.description = description
    finalPoint.notes = notes

    canEat = getBestAttributeValue(attributesValueListByCrawler['canEat'])
    canStay = getBestAttributeValue(attributesValueListByCrawler['canStay'])
    canTour = getBestAttributeValue(attributesValueListByCrawler['canTour'])
    category = getBestAttributeValue(attributesValueListByCrawler['category'])
    finalPoint.canEat = canEat
    finalPoint.canStay = canStay
    finalPoint.canTour = canTour
    finalPoint.category = category

    tripexpertScore = getBestAttributeValue(attributesValueListByCrawler['tripexpertScore'])
    website = getBestAttributeValue(attributesValueListByCrawler['website'])
    rank = getBestAttributeValue(attributesValueListByCrawler['rank'])
    finalPoint.tripexpertScore = tripexpertScore
    finalPoint.website = website
    finalPoint.rank = rank

    priceLevel = getBestAttributeValue(attributesValueListByCrawler['priceLevel'])
    contact = getBestAttributeValue(attributesValueListByCrawler['contact'])
    finalPoint.priceLevel = priceLevel
    finalPoint.contact = contact

    return finalPoint


def orderPointsOfCity(pointsOfCity: List[PointAggregated]) -> List[PointAggregated]:
    # DEEPAK: You have a list of PointAggregated objects.
    # You need to sort this based on your logic
    return pointsOfCity


def aggregateOneCityFromListings(jsonCityListings: List[J], bestCountryName: str, bestCityName: str) -> CityAggregated:
    finalCity = CityAggregated(bestCountryName, bestCityName)

    ignoreAttributes = ['countryName', 'cityName', 'crawler','avgRating', 'ratingCount', 'sourceURL', 'crawlTimestamp', '_uuid', '_listingType']
    attributesValueListByCrawler = defaultdict(lambda: defaultdict(list))

    avgRating, ratingCount = 0, 0
    for listing in jsonCityListings:
        finalCity.sources.append(listing['_uuid'])

        if listing['avgRating'] is not None:
            if listing['ratingCount'] is not None:
                avgRating += listing['avgRating'] * listing['ratingCount']
                ratingCount += listing['ratingCount']
            else:
                avgRating += listing['avgRating'] # considered at least one person reviewed this listing
                ratingCount += 1

        for attr in listing:
            if attr not in ignoreAttributes:
                if listing['crawler'] in attributesValueListByCrawler[attr]:
                    attributesValueListByCrawler[attr][listing['crawler']].append(listing[attr])
                else:
                    attributesValueListByCrawler[attr][listing['crawler']] = [listing[attr]]


    regionName = getBestAttributeValue(attributesValueListByCrawler['regionName'])
    coordinates = getBestAttributeValue(attributesValueListByCrawler['coordinates'])
    recommendedNumDays = getBestAttributeValue(attributesValueListByCrawler['recommendedNumDays'])

    if ratingCount != 0:
        finalCity.avgRating = avgRating/ratingCount
    else:
        finalCity.avgRating = 0
    finalCity.ratingCount = ratingCount
    finalCity.regionName = regionName
    finalCity.coordinates = coordinates
    finalCity.recommendedNumDays = recommendedNumDays

    return finalCity


def aggregateOneCountryFromListings(jsonCountryListings: List[J], bestCountryName: str) -> CountryAggregated:
    finalCountry = CountryAggregated(bestCountryName)
    
    coordinatesListByCrawler = defaultdict(list)

    for listing in jsonCountryListings:
        finalCountry.sources.append(listing['_uuid'])
        coordinatesListByCrawler[listing['crawler']].append(listing['coordinates'])

    coordinates = getBestAttributeValue(coordinatesListByCrawler)
    finalCountry.coordinates = coordinates
    return finalCountry
