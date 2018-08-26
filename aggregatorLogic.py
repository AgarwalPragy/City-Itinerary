from typing import List, Dict
from collections import Counter
from collections import defaultdict
from jsonUtils import J
import json
import random

from entities import *
from utilities import *
from siteRankings import alexa_ranking_orderedList, domain_avg_ranking
from tunable import pointAttributeWeights, orderWeightOfPolicies, orderBasedOn
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
        finalPoint.avgRating = 0
        finalPoint.ratingCount = 0
        return finalPoint

    ignoreAttributes = ['countryName', 'cityName', 'pointName',
                        'crawler', 'sourceURL', 'crawlTimestamp',
                        'avgRating', 'ratingCount', 'rank',
                        '_uuid', '_listingType']

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
            avgRankNumerator += listing['rank'] * (1.0 / domain_avg_ranking[listing['crawler']])
        else:
            # decide rank based on wilson score: higher wilson score => lower rank
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


#######################################################################################################################
#######################################################################################################################

def pointFrequency(point):
    return len(point.sources)


def wilsonScoreLB(point):
    return getWilsonScore(point.avgRating/10, point.ratingCount)


def freqWithWeightedDomainRanking(point):
    rank = (-point.rank) if point.rank else -float('inf')  # lower rank is better
    return len(point.sources), rank                        # first sort on len, then on rank


def weightAvgRating(point):
    return point.avgRating


def orderPointsOfCity(pointsOfCity: List[PointAggregated]) -> List[PointAggregated]:
    keyFunction = {
        'frequency': pointFrequency,
        'wilsonScore': wilsonScoreLB,
        'weightedAvgRating': weightAvgRating,
        'frequencyWithWDomainRanking': freqWithWeightedDomainRanking,
        'weightedOverDiffPolicies': getWeightedOrderValueOverDiffPolices
    }
    return sorted(pointsOfCity, key=keyFunction[orderBasedOn], reverse=True)


#######################################################################################################################
#######################################################################################################################

def getWeightedOrderValueOverDiffPolices(pointAggregated: PointAggregated):
    result = 0
    jsonPointAggregated = pointAggregated.jsonify()
    if 'frequency' in orderWeightOfPolicies:
        result += len(jsonPointAggregated['sources']) * orderWeightOfPolicies['frequency']

    if 'rank' in orderWeightOfPolicies:
        if jsonPointAggregated['rank'] is not None:
            result -= jsonPointAggregated['rank'] * orderWeightOfPolicies['rank']

    if 'wilsonScore' in orderWeightOfPolicies:
        result += getWilsonScore(jsonPointAggregated['avgRating']/10, jsonPointAggregated['ratingCount']) * orderWeightOfPolicies['wilsonScore']

    if 'pointAttributes' in orderWeightOfPolicies:
        pointAttrValue = 0
        for pointAttr in pointAttributeWeights:
            if jsonPointAggregated[pointAttr] is not None:
                pointAttrValue += pointAttributeWeights[pointAttr]
        result += pointAttrValue * orderWeightOfPolicies['pointAttributes']

    if 'tripexpertScore' in orderWeightOfPolicies:
        if jsonPointAggregated['tripexpertScore'] is not None:
            result += jsonPointAggregated['tripexpertScore'] * orderWeightOfPolicies['tripexpertScore']

    return result


def aggregateOneCityFromListings(jsonCityListings: List[J], bestCountryName: str, bestCityName: str) -> CityAggregated:
    finalCity = CityAggregated(bestCountryName, bestCityName)

    ignoreAttributes = ['countryName', 'cityName',
                        'crawler', 'sourceURL', 'crawlTimestamp',
                        'avgRating', 'ratingCount',
                        '_uuid', '_listingType']

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
