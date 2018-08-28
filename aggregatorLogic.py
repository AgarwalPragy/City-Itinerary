from typing import List, Dict
from collections import Counter
from collections import defaultdict
from jsonUtils import J
import json
import re
import random

from entities import *
from utilities import *
from siteRankings import alexa_ranking_orderedList, domain_avg_ranking
from tunable import pointAttributeWeights, orderWeightOfPolicies, orderBasedOn, avgRecommendedNumHours, avgOpenTime, avgCloseTime
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

# to convert time in only hours for example 2h 30 min => 2.5
def getRecommendedNumHoursInHour(pointAggregated):
    if pointAggregated.recommendedNumHours is None:
        return avgRecommendedNumHours
    else:
        result = 0
        timeString = pointAggregated.recommendedNumHours.strip().lower()

        hourRegex = re.compile('^([0-9]+)(h|h | hours| hour)+')

        hour = hourRegex.findall(timeString)
        if len(hour) > 0:
            result += int(hour[0][0])

        minutesRegex = re.compile('([0-9]+) min')
        minutes = minutesRegex.findall(timeString)

        if len(minutes) > 0:
            result += int(minutes[0]) / 60.0
        return result


# convert time in 24 hour format
def formatTime(timeString):
    if timeString == 'closed':
        return '$'

    amFormatData = timeString.split('am')

    if len(amFormatData) == 2:
        hourAndMinutes = amFormatData[0].split(':')
        hour = int(hourAndMinutes[0])
        minutes = 0
        if len(hourAndMinutes) == 2:
            minutes = int(hourAndMinutes[1])

        if hour == 12:
            if minutes == 0:
                result = 24
            else:
                result = minutes / 60.0
        else:
            result = hour + minutes / 60.0

        return result
    pmFormatData = timeString.split('pm')
    if len(pmFormatData) == 2:
        hourAndMinutes = pmFormatData[0].split(':')
        hour = int(hourAndMinutes[0])
        minutes = 0
        if len(hourAndMinutes) == 2:
            minutes = int(hourAndMinutes[1])

        if hour == 12:
            result = hour + minutes / 60.0
        else:
            result = 12 + hour + minutes / 60.0

        return result


def processPointAggregated(pointAggregated):
    hours = getRecommendedNumHoursInHour(pointAggregated)
    pointAggregated.recommendedNumHours = str(hours)

    # convert opening closing in 0-24 format

    formatedOpeningHour = ''
    formatedClosingHour = ''

    if pointAggregated.openingHour is not None:
        openingHourDayWiseData = pointAggregated.openingHour.split(',')
        for openTime in openingHourDayWiseData:
            processedOpenTime = formatTime(openTime.lower())
            if processedOpenTime is None:
                processedOpenTime = formatTime(avgOpenTime.lower())

            formatedOpeningHour += str(processedOpenTime) + ","
    else:
        openTime = avgOpenTime
        for i in range(7):
            formatedOpeningHour += str(formatTime(openTime.lower())) + ","

    if pointAggregated.closingHour is not None:
        closingHourDayWiseData = pointAggregated.closingHour.split(',')
        for closeTime in closingHourDayWiseData:
            processedCloseTime = formatTime(closeTime)
            if processedCloseTime is None:
                processedCloseTime = formatTime(closeTime.lower())
            formatedClosingHour += str(processedCloseTime) + ","
    else:
        closeTime = avgCloseTime
        for i in range(7):
            formatedClosingHour += str(formatTime(closeTime.lower())) + ","

    pointAggregated.openingHour = formatedOpeningHour[:-1]
    pointAggregated.closingHour = formatedClosingHour[:-1]

    return pointAggregated



def aggregateOnePointFromListings(jsonPointListings: List[J], bestCountryName: str, bestCityName: str, bestPointName: str) -> PointAggregated:
    finalPoint = PointAggregated(bestCountryName, bestCityName, bestPointName)
    if len(jsonPointListings) == 0:
        finalPoint.avgRating = 0
        finalPoint.ratingCount = 0
        return finalPoint

    ignoreAttributes = ['countryName', 'cityName', 'pointName', 'canStay',
                        'canEat', 'canTour', 'crawler', 'sourceURL', 'crawlTimestamp',
                        'avgRating', 'ratingCount', 'rank', 'notes', 'category',
                        '_uuid', '_listingType', 'website']

    attributesValueListByCrawler = defaultdict(lambda: defaultdict(list))

    avgRating, ratingCount = 0, 0
    avgRankNumerator, avgRankDenominator = 0, 0
    canStay, canTour, canEat = None, None, None
    notesData, contactData, websites = "", "", ""
    categoryData = []
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


        if listing['canStay'] is not None:
            if canStay is None:
                canStay = listing['canStay']
            else:
                canStay = canStay or listing['canStay']

        if listing['canEat'] is not None:
            if canEat is None:
                canEat = listing['canEat']
            else:
                canEat = canEat or listing['canEat']

        if listing['canTour'] is not None:
            if canTour is None:
                canTour = listing['canTour']
            else:
                canTour = canTour or listing['canTour']

        if listing['notes'] is not None:
            notesData += listing['notes']

        if listing['category'] is not None:
            categoryData.append(listing['category'])

        if "contact" in listing and listing['contact'] is not None:
            contactData += listing['contact'] + ","

        if listing['website'] is not None:
            websites += listing['website'] + ","

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

    if len(notesData) > 0:
        finalPoint.notes = notesData

    if len(categoryData) > 0:
        mergedCategory = ', '.join(set((', '.join(categoryData)).split(',')))
        finalPoint.category = mergedCategory

    if len(contactData) > 0:
        contactData = contactData[:-1]
        finalPoint.contact = contactData

    if len(websites) > 0:
        websites = websites[:-1]
        finalPoint.website = websites

    finalPoint.canEat = canEat
    finalPoint.canStay = canStay
    finalPoint.canTour = canTour

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
    finalPoint.description = description

    tripexpertScore = getBestAttributeValue(attributesValueListByCrawler['tripexpertScore'])
    finalPoint.tripexpertScore = tripexpertScore

    priceLevel = getBestAttributeValue(attributesValueListByCrawler['priceLevel'])
    finalPoint.priceLevel = priceLevel

    processedPointAggregated = processPointAggregated(finalPoint)
    return processedPointAggregated


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

    coordinatesValuesListByCrawler = defaultdict(list)

    avgRating, ratingCount = 0, 0
    daysNumerator, daysDenominator = 0, 0
    regionNameData = ""
    for listing in jsonCityListings:
        finalCity.sources.append(listing['_uuid'])

        if listing['avgRating'] is not None:
            if listing['ratingCount'] is not None:
                avgRating += listing['avgRating'] * listing['ratingCount']
                ratingCount += listing['ratingCount']
            else:
                avgRating += listing['avgRating'] # considered at least one person reviewed this listing
                ratingCount += 1

        if listing['recommendedNumDays'] is not None:
            daysNumerator += listing['recommendedNumDays'] * (1.0/domain_avg_ranking[listing['crawler']])
            daysDenominator += 1.0/domain_avg_ranking[listing['crawler']]

        if listing['regionName'] is not None:
            regionNameData += listing['regionName'] + ","


    if ratingCount != 0:
        finalCity.avgRating = avgRating/ratingCount
    else:
        finalCity.avgRating = 0

    if daysDenominator != 0:
        finalCity.recommendedNumDays = daysNumerator/daysDenominator

    if len(regionNameData) > 0:
        regionNameData = regionNameData[:-1]
        finalCity.regionName = regionNameData

    finalCity.ratingCount = ratingCount

    coordinates = getBestAttributeValue(coordinatesValuesListByCrawler)
    finalCity.coordinates = coordinates

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
