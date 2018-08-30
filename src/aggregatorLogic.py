from typing import List, Dict
from collections import Counter
from collections import defaultdict
from jsonUtils import J
import json
import re

from entities import *
from utilities import *
from siteRankings import alexa_ranking_orderedList, domain_avg_ranking
from tunable import pointAttributeWeights, orderWeightOfPolicies, orderBasedOn, avgRecommendedNumHours
from tunable import avgOpenTime, avgCloseTime, mScoreAvgRatingCount, mScoreAvgRating
from tunable import goodWordWeight, badWordWeight, okayWordWeight, titleWeight, categoryWeight
from tunable import okayCategoryTitleWords, goodCategoryTitleWords, badCategoryTitleWords, thresholdGoodWordCount
__all__ = ['getBestName', 'orderImages', 'orderReviews', 'orderPointsOfCity', 'aggregateOneCityFromListings', 'aggregateOneCountryFromListings', 'aggregateOnePointFromListings']

catTitleWeightAvgValue = 0
catTitleWeightCount = 0


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


def getCategoryTitleWeight(point):
    title = processName(point['pointName'])
    categories = processName((point['category'] if point['category'] else ''))
    score = 0
    goodWordCount = (sum(titleWeight for word in goodCategoryTitleWords if processName(word) in title)
                    +sum(categoryWeight for word in goodCategoryTitleWords if processName(word) in categories))
    badWordCount = (sum(titleWeight for word in badCategoryTitleWords if processName(word) in title)
                    +sum(categoryWeight for word in badCategoryTitleWords if processName(word) in categories))
    okayWordCount = (sum(titleWeight for word in okayCategoryTitleWords if processName(word) in title)
                    +sum(categoryWeight for word in okayCategoryTitleWords if processName(word) in categories))
    if goodWordCount >= thresholdGoodWordCount:
        return goodWordWeight * (goodWordCount ** 0.5)
    else:
        goodWordWeight * (goodWordCount ** 0.5) + badWordWeight * (badWordCount ** 0.5) + okayWordWeight * (okayWordCount ** 0.5)
    return score


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


def formatTime(timeString: str):
    """Converts time string to 24 hour format"""

    if timeString == 'closed': return '$'

    amFormatData = timeString.split('am')
    if len(amFormatData) == 2:
        hourAndMinutes = amFormatData[0].split(':')
        hour = int(hourAndMinutes[0])
        minutes = 0
        if len(hourAndMinutes) == 2:  # think about 8 am
            minutes = int(hourAndMinutes[1])
        if hour == 12:
            if minutes == 0:  # 12 am => 24
                result = 24
            else:   # 12:30 am => 0.5
                result = minutes / 60.0
        else:  # 3:30 am => 3.5
            result = hour + minutes / 60.0
        return result

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
            processedOpenTime = formatTime(openTime.lower())
            if processedOpenTime is None:                      # in case of openTime =  unavailable from tripExpert Data
                processedOpenTime = formatTime(avgOpenTime.lower())
            formattedOpeningHour += str(processedOpenTime) + ","
    else:
        openTime = avgOpenTime
        for i in range(7):
            formattedOpeningHour += str(formatTime(openTime.lower())) + ","

    if pointAggregated.closingHour is not None:
        closingHourDayWiseData = pointAggregated.closingHour.split(',')
        for closeTime in closingHourDayWiseData:
            processedCloseTime = formatTime(closeTime)
            if processedCloseTime is None:
                processedCloseTime = formatTime(avgCloseTime.lower())
            formattedClosingHour += str(processedCloseTime) + ","
    else:
        closeTime = avgCloseTime
        for i in range(7):
            formattedClosingHour += str(formatTime(closeTime.lower())) + ","

    pointAggregated.openingHour = formattedOpeningHour[:-1]
    pointAggregated.closingHour = formattedClosingHour[:-1]

    return pointAggregated



def aggregateOnePointFromListings(jsonPointListings: List[J], bestCountryName: str, bestCityName: str, bestPointName: str) -> PointAggregated:
    global catTitleWeightAvgValue, catTitleWeightCount

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
    notesData, contactData, websites = '', '', ''
    categoryData = []

    for listing in jsonPointListings:
        finalPoint.sources.append(listing['_uuid'])

        if listing['avgRating'] is not None:
            if listing['ratingCount'] is not None:
                avgRating += listing['avgRating'] * listing['ratingCount']
                ratingCount += listing['ratingCount']
            else:
                avgRating += listing['avgRating']  # considered at least one person reviewed this listing
                ratingCount += 1

        if listing['rank'] is not None:
            avgRankNumerator += listing['rank'] * (1.0 / domain_avg_ranking[listing['crawler']])
            avgRankDenominator += 1.0 / domain_avg_ranking[listing['crawler']]

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

    if avgRankDenominator != 0:
        finalPoint.rank = avgRankNumerator / avgRankDenominator

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

    # get best props value
    address = getBestAttributeValue(attributesValueListByCrawler['address'])
    coordinates = getBestAttributeValue(attributesValueListByCrawler['coordinates'])

    openingHour = getBestAttributeValue(attributesValueListByCrawler['openingHour'])
    closingHour = getBestAttributeValue(attributesValueListByCrawler['closingHour'])
    recommendedNumHours = getBestAttributeValue(attributesValueListByCrawler['recommendedNumHours'])
    description = getBestAttributeValue(attributesValueListByCrawler['description'])
    tripexpertScore = getBestAttributeValue(attributesValueListByCrawler['tripexpertScore'])
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

    catTitleWeightAvgValue += getCategoryTitleWeight(processedPointAggregated.jsonify())
    catTitleWeightCount += 1
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


def mayurScore(point):
    avgRating = point.avgRating
    ratingCount = point.ratingCount
    return (avgRating * ratingCount + mScoreAvgRating * mScoreAvgRatingCount) / (ratingCount + mScoreAvgRatingCount)  # inject fake ratings


def getWeightedOrderValueOverDiffPolices(pointAggregated: PointAggregated):
    result = 0
    jsonPointAggregated = pointAggregated.jsonify()
    if 'frequency' in orderWeightOfPolicies:
        result += len(jsonPointAggregated['sources']) * orderWeightOfPolicies['frequency']

    if 'rank' in orderWeightOfPolicies and jsonPointAggregated['rank'] is not None:
        result -= jsonPointAggregated['rank'] * orderWeightOfPolicies['rank']

    if 'wilsonScore' in orderWeightOfPolicies:
        result += getWilsonScore(jsonPointAggregated['avgRating']/10, jsonPointAggregated['ratingCount']) * orderWeightOfPolicies['wilsonScore']

    if 'pointAttributes' in orderWeightOfPolicies:
        pointAttrValue = 0
        for pointAttr in pointAttributeWeights:
            if jsonPointAggregated[pointAttr] is not None:
                pointAttrValue += pointAttributeWeights[pointAttr]

        result += pointAttrValue * orderWeightOfPolicies['pointAttributes']

    if 'tripexpertScore' in orderWeightOfPolicies and jsonPointAggregated['tripexpertScore'] is not None:
        result += jsonPointAggregated['tripexpertScore'] * orderWeightOfPolicies['tripexpertScore']/100

    if 'category' in orderWeightOfPolicies:
        catTitleAverage = catTitleWeightAvgValue*1.0 / catTitleWeightCount
        result += (getCategoryTitleWeight(jsonPointAggregated)/catTitleAverage) * orderWeightOfPolicies['category']

    if 'mayurScore' in orderWeightOfPolicies:
        result += mayurScore(pointAggregated) * orderWeightOfPolicies['mayurScore']/10

    return result


def orderPointsOfCity(pointsOfCity: List[PointAggregated]):
    keyFunction = {
        'frequency': pointFrequency,
        'wilsonScore': wilsonScoreLB,
        'weightedAvgRating': weightAvgRating,
        'frequencyWithWDomainRanking': freqWithWeightedDomainRanking,
        'mayurScore': mayurScore,
        'weightedOverDiffPolicies': getWeightedOrderValueOverDiffPolices
    }

    sortedPoints = sorted(pointsOfCity, key=keyFunction[orderBasedOn], reverse=True)
    scores = list(map(keyFunction[orderBasedOn], sortedPoints))
    return sortedPoints, scores


#######################################################################################################################
#######################################################################################################################




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


def orderImages(jsonImageListings: List[J]) -> List[J]:
    # TODO: Sort images by dimension/quality?
    # return as is for now
    return jsonImageListings


def orderReviews(jsonReviewListings: List[J]) -> List[J]:
    # TODO: Sort reviews by grammar, length, relevancy?
    # return as is for now
    return jsonReviewListings

