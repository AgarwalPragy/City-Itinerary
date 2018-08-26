from typing import List, Dict
from collections import Counter
from collections import defaultdict
from jsonUtils import J
import json
import random

from entities import *
from utilities import *
from siteRankings import alexa_ranking_orderedList, domain_avg_ranking
from tunable import pointAttributeWeights, orderWeightOfPolicies
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
    if len(jsonPointListings) == 0:
        return finalPoint

    ignoreAttributes = ['countryName', 'cityName', 'pointName', 'crawler','avgRating', 'ratingCount', 'rank', 'sourceURL', 'crawlTimestamp', '_uuid', '_listingType']
    attributesValueListByCrawler = defaultdict(lambda: defaultdict(list))

    avgRating, ratingCount = 0, 0
    avgRankNumerator, avgRankDenominator = 0, 0
    for listing in jsonPointListings:
        finalPoint.sources.append(listing['_uuid'])

        currentRating, currentRatingCount = 0, 0
        if listing['avgRating'] is not None:
            if listing['ratingCount'] is not None:
                currentRating = listing['avgRating']
                currentRatingCount = listing['ratingCount']
                avgRating += currentRating * currentRatingCount
                ratingCount += currentRatingCount
            else:
                currentRating = listing['avgRating']
                currentRatingCount = 1
                avgRating += currentRating # considered at least one person reviewed this listing
                ratingCount += currentRatingCount


        if listing['rank'] is not None:
            avgRankNumerator += listing['rank'] * (1.0/ domain_avg_ranking[listing['crawler']])
        else:
            #decide rank based on wilson score: higher wilson score => lower rank
            currentPointWilsonScore = getWilsonScore(currentRating/10.0, currentRatingCount)
            siteRankOfPoint = random.randint(50, 200)*(1.0 - currentPointWilsonScore)
            avgRankNumerator += siteRankOfPoint*(1.0/domain_avg_ranking[listing['crawler']])
        avgRankDenominator += 1.0/domain_avg_ranking[listing['crawler']]

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

    finalPoint.rank = avgRankNumerator / avgRankDenominator
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
    finalPoint.tripexpertScore = tripexpertScore
    finalPoint.website = website

    priceLevel = getBestAttributeValue(attributesValueListByCrawler['priceLevel'])
    contact = getBestAttributeValue(attributesValueListByCrawler['contact'])
    finalPoint.priceLevel = priceLevel
    finalPoint.contact = contact

    return finalPoint

def cmp_to_key(comparator):
    'Convert a cmp= function into a key= function'
    class K:
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return comparator(self.obj, other.obj) < 0
        def __gt__(self, other):
            return comparator(self.obj, other.obj) > 0
        def __eq__(self, other):
            return comparator(self.obj, other.obj) == 0
        def __le__(self, other):
            return comparator(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return comparator(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return comparator(self.obj, other.obj) != 0
    return K


def freqComparator(pointAggregated1: PointAggregated, pointAggregated2:  PointAggregated):
    if len(pointAggregated1.sources) > len(pointAggregated2.sources):
        return 1
    elif len(pointAggregated1.sources) < len(pointAggregated2.sources):
        return -1
    else:
        return 0

def wilsonScoreLBComparator(pointAggregated1: PointAggregated, pointAggregated2:  PointAggregated):
    wilsonScore1 = getWilsonScore(pointAggregated1['avgRating'], pointAggregated2['ratingCount'])
    wilsonScore2 = getWilsonScore(pointAggregated2['avgRating'], pointAggregated2['ratingCount'])

    if wilsonScore1 > wilsonScore2:
        return 1
    elif wilsonScore1 < wilsonScore2:
        return -1
    else:
        return 0

def freqWithWeightedDomainRankingComparator(pointAggregated1: PointAggregated, pointAggregated2:  PointAggregated):
    if len(pointAggregated1.sources) > len(pointAggregated2.sources):
        return 1
    elif len(pointAggregated1.sources) < len(pointAggregated2.sources):
        return -1
    elif pointAggregated1.rank <= pointAggregated2.rank:
        return 1
    else:
        return -1

def weightAvgRatingComparator(pointAggregated1: PointAggregated, pointAggregated2: PointAggregated):
    if pointAggregated1.avgRating > pointAggregated2.rank:
        return 1
    elif pointAggregated1.avgRating < pointAggregated2.rank:
        return -1
    else:
        return 0


def orderPointsOfCity(pointsOfCity: List[PointAggregated]) -> List[PointAggregated]:
    # DEEPAK: You have a list of PointAggregated objects.
    # You need to sort this based on your logic
    sortedPointsOfCity = sorted(pointsOfCity, key=cmp_to_key(freqComparator), reverse=True)
    return sortedPointsOfCity


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
