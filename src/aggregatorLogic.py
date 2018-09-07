from typing import List, Dict
from collections import Counter
from operator import attrgetter
from collections import defaultdict
from jsonUtils import J
import json
import re
import math

from entities import *
from utilities import *
from siteRankings import alexa_ranking_orderedList, domain_avg_ranking
from tunable import avgRecommendedNumHours, avgOpenTime, avgCloseTime, injectedBestNames
from gratify import gratificationScoreOfPoint
from cityCenter import getCenterOfCity

__all__ = ['getBestName', 'orderImages', 'orderReviews', 'orderPointsOfCity', 'aggregateOneCityFromListings', 'aggregateOneCountryFromListings', 'aggregateOnePointFromListings']

catTitleWeightAvgValue = 0
catTitleWeightCount = 0


def getBestName(names: List[str], strictness: int=3) -> str:
    """returns the median length name which occurs sufficiently enough
    strictness: [1..100]"""
    # sufficiently enough: in order to remove incorrect names
    names = sorted(names, key=len)
    counts = Counter(names)
    numUnique = len(counts)
    sufficientAmount = counts.most_common(1 + numUnique//strictness)[-1][1]

    popularNames = ('####'.join('####'.join([name]*count) for name, count in counts.most_common() if count >= sufficientAmount)).split('####')
    # of all the names that occur sufficiently many times, choose the median length one
    if len(popularNames) == 1:
        bestName = popularNames[0]
    else:
        sortedNames = sorted(popularNames, key=len)
        bestName = sanitizeName(sortedNames[math.ceil(len(sortedNames)/2)])
    if len(names) > 4:
        print('#######################', bestName, names)

    if 'botanique' in bestName.lower():
        print(bestName, names)

    bestName = injectedBestNames.get(bestName, bestName)

    return bestName


def getMinMaxAttributeValue(valueListByCrawler: Dict[str, List], func):
    result = None
    for crawler in alexa_ranking_orderedList:
        values = [val for val in valueListByCrawler[crawler] if val is not None]
        if values:
            result = func(values)
    return result


def getBestAttributeValue(valueListByCrawler: Dict[str, List]):
    result = None
    for crawler in alexa_ranking_orderedList:
        for value in valueListByCrawler[crawler]:
            if value is not None:
                return value
    return result


def getRecommendedNumHoursInHour(pointAggregated: PointAggregated):
    """Converts time from string to float hours.
    example 2h 30 min -> 2.5"""

    if pointAggregated.recommendedNumHours is None:
        return avgRecommendedNumHours
    elif 'hour' in pointAggregated.recommendedNumHours or 'min' in pointAggregated.recommendedNumHours:
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
    else:
        return pointAggregated.recommendedNumHours


def formatTime(timeString: str, isOpen):
    """Converts time string to 24 hour format"""
    timeString = timeString.lower()
    if timeString == 'closed':
        return '$'
    if 'am' not in timeString and 'pm' not in timeString:
        return None

    result = None

    if 'am' in timeString:
        amFormatData = timeString.split('am')
        if len(amFormatData) == 2:
            hourAndMinutes = amFormatData[0].split(':')
            hour = int(hourAndMinutes[0])
            minutes = 0
            if len(hourAndMinutes) == 2:  # think about 8 am
                minutes = int(hourAndMinutes[1])
            if hour == 12:
                result = minutes / 60.0
            else:  # 3:30 am => 3.5
                result = hour + minutes / 60.0
    elif 'pm' in timeString:
        pmFormatData = timeString.split('pm')
        if len(pmFormatData) == 2:
            hourAndMinutes = pmFormatData[0].split(':')
            hour = int(hourAndMinutes[0])
            minutes = 0
            if len(hourAndMinutes) == 2: # think 9 pm
                minutes = int(hourAndMinutes[1])

            if hour == 12:  # 12;30 pm => 12.5
                result = hour + minutes / 60.0
            else:  # 10:30 pm => 22.5
                result = 12 + hour + minutes / 60.0

    if isOpen and result > 22:
        return 6

    elif not isOpen and result < 8:
        return 24

    return result


def processPointAggregated(pointAggregated: PointAggregated):
    hours = getRecommendedNumHoursInHour(pointAggregated)
    pointAggregated.recommendedNumHours = str(hours)

    # convert opening closing in 0-24 format
    formattedOpeningHour = ''
    formattedClosingHour = ''

    if pointAggregated.openingHour is not None:
        openingHourDayWiseData = pointAggregated.openingHour.split(',')
        for openTime in openingHourDayWiseData:
            processedOpenTime = formatTime(openTime.lower(), isOpen=True)
            if processedOpenTime is None:                      # in case of openTime =  unavailable from tripExpert Data
                processedOpenTime = formatTime(avgOpenTime.lower(), isOpen=True)
            formattedOpeningHour += str(processedOpenTime) + ","
    else:
        openTime = avgOpenTime
        for i in range(7):
            formattedOpeningHour += str(formatTime(openTime.lower(), isOpen=True)) + ","

    if pointAggregated.closingHour is not None:
        closingHourDayWiseData = pointAggregated.closingHour.split(',')
        for closeTime in closingHourDayWiseData:
            processedCloseTime = formatTime(closeTime, isOpen=False)
            if processedCloseTime is None:
                processedCloseTime = formatTime(avgCloseTime.lower(), isOpen=False)
            formattedClosingHour += str(processedCloseTime) + ","
    else:
        closeTime = avgCloseTime
        for i in range(7):
            formattedClosingHour += str(formatTime(closeTime.lower(), isOpen=False)) + ","

    pointAggregated.openingHour = formattedOpeningHour[:-1]
    pointAggregated.closingHour = formattedClosingHour[:-1]

    return pointAggregated



def aggregateOnePointFromListings(jsonPointListings: List[J], bestCountryName: str, bestCityName: str, bestPointName: str) -> PointAggregated:
    global catTitleWeightAvgValue, catTitleWeightCount

    finalPoint = PointAggregated(bestCountryName, bestCityName, bestPointName)
    if len(jsonPointListings) == 0:
        finalPoint.avgRating = 0
        finalPoint.ratingCount = 0
        finalPoint.gratificationScore = 0
        return finalPoint

    ignoreAttributes = ['countryName', 'cityName', 'pointName', 'canStay',
                        'canEat', 'canTour', 'crawler', 'sourceURL', 'crawlTimestamp',
                        'avgRating', 'ratingCount', 'notes', 'category', 'rank',
                        '_uuid', '_listingType', 'website']

    attributesValueListByCrawler = defaultdict(lambda: defaultdict(list))

    avgRating, ratingCount = 0, 0
    canStay, canTour, canEat = None, None, None
    notesData, contactData, websites = '', '', ''
    categoryData = []

    for listing in jsonPointListings:
        finalPoint.sources.append(listing['_uuid'])
        if listing['crawler'] not in finalPoint.sources_crawlers:
            finalPoint.sources_crawlers.append(listing['crawler'])

        if listing['avgRating'] is not None:
            if listing['ratingCount'] is not None:
                avgRating += listing['avgRating'] * listing['ratingCount']
                ratingCount += listing['ratingCount']
            else:
                avgRating += listing['avgRating']  # considered at least one person reviewed this listing
                ratingCount += 1

        if listing['rank'] is not None:
            attributesValueListByCrawler['rank'][listing['crawler']].append(float(listing['rank']))

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
            notesData += '\n' + listing['notes']

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

    if notesData:
        finalPoint.notes = notesData

    if categoryData:
        finalPoint.category = ', '.join(set((', '.join(categoryData)).split(',')))

    if contactData:
        finalPoint.contact = contactData[:-1]

    if websites:
        finalPoint.website = websites[:-1]

    finalPoint.canEat = canEat
    finalPoint.canStay = canStay
    finalPoint.canTour = canTour


    rankNumerator = 0
    rankDenominator = 0
    for crawler, rankValuesList in attributesValueListByCrawler['rank'].items():
        rankMinValue = None
        if rankValuesList:
            rankMinValue = min(rankValuesList)

        if rankMinValue:
            rankNumerator += rankMinValue / domain_avg_ranking[crawler]
            rankDenominator += 1/domain_avg_ranking[crawler]

    if rankDenominator != 0:
        rankNumerator = max(1, rankNumerator)
        finalPoint.rank = rankNumerator / rankDenominator


    # get best props value
    address = getBestAttributeValue(attributesValueListByCrawler['address'])
    coordinates = getBestAttributeValue(attributesValueListByCrawler['coordinates'])

    openingHour = getBestAttributeValue(attributesValueListByCrawler['openingHour'])
    closingHour = getBestAttributeValue(attributesValueListByCrawler['closingHour'])
    recommendedNumHours = getBestAttributeValue(attributesValueListByCrawler['recommendedNumHours'])
    description = getBestAttributeValue(attributesValueListByCrawler['description'])
    tripexpertScore = getMinMaxAttributeValue(attributesValueListByCrawler['tripexpertScore'], max)
    priceLevel = getBestAttributeValue(attributesValueListByCrawler['priceLevel'])

    finalPoint.address = address
    finalPoint.coordinates = coordinates
    finalPoint.openingHour = openingHour
    finalPoint.closingHour = closingHour
    finalPoint.recommendedNumHours = recommendedNumHours
    finalPoint.description = description
    finalPoint.tripexpertScore = tripexpertScore
    finalPoint.priceLevel = priceLevel

    processedPointAggregated = processPointAggregated(finalPoint)

    processedPointAggregated.gratificationScore = gratificationScoreOfPoint(processedPointAggregated)
    return processedPointAggregated


def orderPointsOfCity(pointsOfCity: List[PointAggregated]):
    sortedPoints = sorted(pointsOfCity, key=attrgetter('gratificationScore'), reverse=True)
    return sortedPoints


def aggregateOneCityFromListings(jsonCityListings: List[J], bestCountryName: str, bestCityName: str, listOfPoints: List[PointAggregated]) -> CityAggregated:
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
    coordinates = None

    if listOfPoints:
        coordinates = getCenterOfCity(listOfPoints)
        if coordinates:
            coordinates = ','.join(map(str, coordinates))

    if not coordinates:
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


def orderImages(jsonImageListings: List[J]) -> List[J]:
    # TODO: Sort images by dimension/quality?
    # return as is for now
    return jsonImageListings


def orderReviews(jsonReviewListings: List[J]) -> List[J]:
    # TODO: Sort reviews by grammar, length, relevancy?
    # return as is for now
    return jsonReviewListings

