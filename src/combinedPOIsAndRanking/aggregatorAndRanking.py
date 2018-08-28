from typing import List, Dict, NewType, Any
import json
from fuzzywuzzy import fuzz
import sys
from collections import defaultdict
sys.path.append('.')

from entities import *
from utilities import *
from siteRankings import alexa_ranking, similar_web_ranking


acceptableFuzzyScore = 90

citiesToProcess = list(map(processName, ['london', 'dubai', 'bangkok']))
filesToProcess = ["specificCrawler/skyscanner.json", "specificCrawler/inspirock.json",
                  "specificCrawler/tripadvisor.json", "specificCrawler/viator.json"] #, 'specificCrawler/tripexpert.json']

crawlerToIndexMapping = {'skyscanner': 0, 'inspirock': 1, 'tripadvisor': 2, 'viator_v2': 3, 'tripexpert': 4}
priorityToIndexMapping = {'freqPriorityIndex' : 0, 'weightedRatingPriorityIndex': 1, 'freqWithALRankingPriorityIndex' : 2,
                         'freqWithSWGRankingPriorityIndex': 3, 'wilsonScorePriorityIndex' : 4, 'weightedPrioritiesIndex' : 5}

#index is same as priority Index
weightsOfPriority = [0.4, 0, 0.4, 0.1, 0.1]



#list1, list2 are priority value and data1, data2 are aggregated data
def compareBasedOnPriorityIndex(list1, list2, priorityIndex, priorityToIndexMapping):
    if (priorityIndex == priorityToIndexMapping['freqPriorityIndex']
                or priorityIndex == priorityToIndexMapping['weightedRatingPriorityIndex']
                or priorityIndex == priorityToIndexMapping['wilsonScorePriorityIndex']
                or priorityIndex == priorityToIndexMapping['weightedPrioritiesIndex']):
        return list1[priorityIndex] >= list2[priorityIndex]

    elif (priorityIndex == priorityToIndexMapping['freqWithALRankingPriorityIndex'] or
        priorityIndex == priorityToIndexMapping['freqWithSWGRankingPriorityIndex']):
        if list1[priorityToIndexMapping['freqPriorityIndex']] > list2[priorityToIndexMapping['freqPriorityIndex']]:
            return True
        elif list1[priorityToIndexMapping['freqPriorityIndex']] < list2[priorityToIndexMapping['freqPriorityIndex']]:
            return False
        else:
            return list2[priorityIndex] >= list1[priorityIndex] # want lower rank pois first


def merge(prioritiesListOfList, dataListOfList,priorityIndex,priorityToIndexMapping, low, mid, high):
    n1 = mid - low + 1
    n2 = high- mid

    # create temp arrays
    leftPrioritiesListOfList = []
    rightPrioritiesListOfList = []

    leftDtaListOfList = []
    rightdataListOfList = []

    # Copy data to temp arrays L[] and R[]
    for i in range(0 , n1):
        leftPrioritiesListOfList.append(prioritiesListOfList[low + i])
        leftDtaListOfList.append(dataListOfList[low+i])

    for j in range(0 , n2):
        rightPrioritiesListOfList.append(prioritiesListOfList[mid + 1 + j])
        rightdataListOfList.append(dataListOfList[mid + 1 + j])

    # Merge the temp arrays back into arr[l..r]
    i = 0    # Initial index of first subarray
    j = 0    # Initial index of second subarray
    k = low  # Initial index of merged subarray

    while i < n1 and j < n2 :
        if compareBasedOnPriorityIndex(leftPrioritiesListOfList[i],rightPrioritiesListOfList[j], priorityIndex,priorityToIndexMapping):
            prioritiesListOfList[k] = leftPrioritiesListOfList[i]
            dataListOfList[k] = leftDtaListOfList[i]
            i += 1
        else:
            prioritiesListOfList[k] = rightPrioritiesListOfList[j]
            dataListOfList[k] = rightdataListOfList[j]
            j += 1
        k += 1

    # Copy the remaining elements of Left[], if there
    # are any
    while i < n1:
        prioritiesListOfList[k] = leftPrioritiesListOfList[i]
        dataListOfList[k] = leftDtaListOfList[i]
        i += 1
        k += 1

    # Copy the remaining elements of Right[], if there
    # are any
    while j < n2:
        prioritiesListOfList[k] = rightPrioritiesListOfList[j]
        dataListOfList[k] = rightdataListOfList[j]
        j += 1
        k += 1


def mergeSort(prioritiesListOfList, dataListOfList,priorityIndex,priorityToIndexMapping, low, high):
    if low < high:
        mid = int((low+(high-1))/2)
        mergeSort(prioritiesListOfList, dataListOfList, priorityIndex,priorityToIndexMapping, low, mid)
        mergeSort(prioritiesListOfList, dataListOfList, priorityIndex, priorityToIndexMapping,mid+1, high)
        merge(prioritiesListOfList, dataListOfList, priorityIndex, priorityToIndexMapping, low, mid, high)

def savePOIs(fileName: str, pointAggregatedList: List[JPA]):
    data = json.dumps(pointAggregatedList, indent=4)
    with open(fileName, 'w') as f:
        f.write(data)


def loadOneFile(filename: str, citiesTOProcess) -> List[JPL]:
    with open(filename, 'r') as f:
        fileData = json.load(f)

    pointListingsForCrawler = []
    for item in fileData:
        if item['_listingType'] == 'point':
            cityName = item['cityName']
            if processName(cityName) in citiesToProcess:
                pointListingsForCrawler.append(item)
    return pointListingsForCrawler


def loadAllFiles(filenames: List[str], citiesToProcess) -> List[List[JPL]]:
    result = []
    for filename in filenames:
        result.append(loadOneFile(filename, citiesToProcess))
    return result


def combinePOIsByCity(crawlerPointListings: List[List[JPL]], acceptableFuzzyScore) -> Dict[str, List[List[JPL]]]:
    result = defaultdict(list)
    for i, pointListingsForCrawler1 in enumerate(crawlerPointListings):
        for j, pointListing1 in enumerate(pointListingsForCrawler1):
            processedCityName1 = processName(pointListing1['cityName'])
            processedPointName1 = processName(pointListing1['pointName'].lower())
            # countryName1 = pointListing['countryName'].lower()

            pointListingsToAggregate = [pointListing1]

            for k, pointListingsForCrawler2 in enumerate(crawlerPointListings[i+1:], start=i+1):
                maxFuzzyScore = 0
                maxScoreIndex = 0
                pointExactlyMatched = True

                # for l in range(len(crawlerPointListings[k])):
                #     newPointName = processName(pointListing1['cityName'].lower())
                #     if pointName == newPointName:
                #         temp.append(crawlerPointListings[k][l])
                #         crawlerPointListings[k].remove(crawlerPointListings[k][l])
                #         flag = False
                #         break

                if pointExactlyMatched:
                    for l, pointListing2 in enumerate(pointListingsForCrawler2):
                        processedCityName2 = processName(pointListing2['cityName'])
                        processedPointName2 = processName(pointListing2['pointName'])
                        # countryName2 = pointListing2['countryName'].lower()

                        if processedCityName1 == processedCityName2:  # and countryName == newCountryName:
                            tempFuzzyScore = fuzz.partial_ratio(processedPointName1, processedPointName2)

                            if tempFuzzyScore > maxFuzzyScore:
                                maxFuzzyScore = tempFuzzyScore
                                maxScoreIndex = l

                    # print("maxFuzzyScore " + str(maxFuzzyScore))
                    if maxFuzzyScore > acceptableFuzzyScore:
                        pointListingsToAggregate.append(pointListingsForCrawler2[maxScoreIndex])
                        pointListingsForCrawler2.remove(pointListingsForCrawler2[maxScoreIndex])  # TODO: make this more efficient

            key = processedCityName1  # + "," + countryName
            result[key].append(pointListingsToAggregate)
    return result

def getMaxRatingAndReviewCount(crawler: str, cityName: str, crawlerToIndexMapping,maxRatAndCountByCrawlerInCity):
    # TODO: Make this function pure
    processedCityName = processName(cityName)
    maxRating  = 0
    maxCount = 0
    pointListings = crawlerPointListings[crawlerToIndexMapping[crawler]]
    for pointListing in pointListings:
        if processName(pointListing['cityName']) == processedCityName:
            if pointListing['avgRating'] is not None and pointListing['avgRating'] > maxRating:
                maxRating = pointListing['avgRating']
                maxCount = pointListing['ratingCount']

    maxCount += 1
    if crawler in maxRatAndCountByCrawlerInCity:
        maxRatAndCountByCrawlerInCity[crawler][cityName] = {'maxRating' : maxRating, 'maxCount' : maxCount}
    else:
        maxRatAndCountByCrawlerInCity[crawler] = {}
        maxRatAndCountByCrawlerInCity[crawler][cityName] = {'maxRating' : maxRating, 'maxCount' : maxCount}
    return maxRatAndCountByCrawlerInCity

def getPrioritiesValue(combinedPOIsListByCity, weightsOfPriority, crawlerToIndexMapping,priorityToIndexMapping) -> Dict[str, list]:
    prioritiesOfPOIsByCity = {}
    maxRatAndCountByCrawlerInCity = {}
    for city in combinedPOIsListByCity:
        for combinedPOIs in combinedPOIsListByCity[city]:
            priority_list = [0] * len(priorityToIndexMapping)
            freq = len(combinedPOIs)
            ratingCount = 0
            avgRating = 0
            weightedAlexaNumerator = 0
            weightedAlexaDenominator = 0
            weightedSWebGNumerator = 0
            weightedSWebGDenominator = 0

            weightedPrioritiesScore = 0
            for pointListing in combinedPOIs:
                # weighted average rating
                processedCityName = processName(pointListing['cityName'])
                if pointListing['avgRating'] is not None:
                    if pointListing['ratingCount'] is not None:
                        avgRating += pointListing['avgRating'] * pointListing['ratingCount']
                        ratingCount += pointListing['ratingCount']
                    else:
                        avgRating += pointListing['avgRating'] * 1 # consider at least one person reviewed this POI
                        ratingCount += 1

                # alexa score 
                if pointListing['rank'] is not None:
                    weightedAlexaNumerator += pointListing['rank'] / (alexa_ranking[pointListing['crawler']] * 1.0)
                    weightedSWebGNumerator += pointListing['rank'] / (similar_web_ranking[pointListing['crawler']] * 1.0)

                else: #calculated rank from some linear function 
                    rating = 0
                    countOfRating = 1 # we are dividing by count to calculate the rank so we don't want it zero
                    if pointListing['avgRating'] is not None:
                        rating = pointListing['avgRating']
                    if pointListing['ratingCount'] is not None:
                        countOfRating = pointListing['ratingCount']

                    if pointListing['crawler'] in maxRatAndCountByCrawlerInCity:
                        if processedCityName not in maxRatAndCountByCrawlerInCity[pointListing['crawler']]:
                            maxRatAndCountByCrawlerInCity = getMaxRatingAndReviewCount(pointListing['crawler'], processedCityName,crawlerToIndexMapping,maxRatAndCountByCrawlerInCity)
                    else:
                        maxRatAndCountByCrawlerInCity = getMaxRatingAndReviewCount(pointListing['crawler'], processedCityName,crawlerToIndexMapping,maxRatAndCountByCrawlerInCity)
                        cityData = maxRatAndCountByCrawlerInCity[pointListing['crawler']][processedCityName]
                        maxRating = cityData['maxRating']
                        maxCount = cityData['maxCount']

                    #predict siteRankOfPOI if not given on site
                    siteRankOfPOI = (maxRating + 1 - rating) * maxCount / (1.0 * countOfRating)
                    weightedAlexaNumerator += siteRankOfPOI / (alexa_ranking[pointListing['crawler']])
                    weightedSWebGNumerator += siteRankOfPOI / (similar_web_ranking[pointListing['crawler']])
                weightedAlexaDenominator += 1.0/alexa_ranking[pointListing['crawler']]
                weightedSWebGDenominator += 1.0/similar_web_ranking[pointListing['crawler']]


            priority_list[priorityToIndexMapping['freqPriorityIndex']] = freq
            if ratingCount != 0:
                avgRating = avgRating / ratingCount
                wilsonScore = getWilsonScore(avgRating / 10.0, ratingCount)
                priority_list[priorityToIndexMapping['weightedRatingPriorityIndex']] = avgRating
                priority_list[priorityToIndexMapping['wilsonScorePriorityIndex']] = wilsonScore

            alexaScore = weightedAlexaNumerator / weightedAlexaDenominator
            swebScore = weightedSWebGNumerator / weightedSWebGDenominator

            priority_list[priorityToIndexMapping['freqWithALRankingPriorityIndex']] = alexaScore
            priority_list[priorityToIndexMapping['freqWithSWGRankingPriorityIndex']] = swebScore

            weightedPrioritiesScore = weightsOfPriority[priorityToIndexMapping['freqPriorityIndex']] * freq + \
                                      weightsOfPriority[priorityToIndexMapping['weightedRatingPriorityIndex']] * avgRating +\
                                      weightsOfPriority[priorityToIndexMapping['wilsonScorePriorityIndex']] * wilsonScore -\
                                      weightsOfPriority[priorityToIndexMapping['freqWithALRankingPriorityIndex']] * alexaScore - \
                                      weightsOfPriority[priorityToIndexMapping['freqWithSWGRankingPriorityIndex']]*swebScore

            priority_list[priorityToIndexMapping['weightedPrioritiesIndex']] = weightedPrioritiesScore
            if city in prioritiesOfPOIsByCity:
                prioritiesOfPOIsByCity[city].append(priority_list)
            else:
                prioritiesOfPOIsByCity[city] = [priority_list]

    return prioritiesOfPOIsByCity

# aggregate the top k points for each city and store same in the file

def combinePOIsInPointAggregated(listOfPOIs: List[JPL]) -> JPA:
    ignoreProperties = ['cityName', 'crawler', 'crawlTimestamp', 'sourceURL', 'countryName', 'pointName',
                   'avgRating', 'ratingCount', '_listingType', '_uuid']

    cityName = listOfPOIs[0]['cityName']
    countryName = listOfPOIs[0]['countryName']

    pointListingProperties = {} #key is property of pointList object except ignoreList properties
    for property in listOfPOIs[0]:
        if property not in ignoreProperties:
            pointListingProperties[property] = {}  # value will be data from different crawler with key = crawler Name

    maxLenPointName = ""
    avgRating = 0
    ratingCount = 1
    for point in listOfPOIs:
        if len(point['pointName']) > len(maxLenPointName):
            maxLenPointName = point['pointName']
        if point['avgRating'] is not None:
            if point['ratingCount'] is not None:
                avgRating += point['avgRating'] * point['ratingCount']
                ratingCount += point['ratingCount']
            else:
                avgRating += point['avgRating'] * 1  # consider at least one person reviewed it
                ratingCount += 1

        # for every point store property value in pointListingProperties dict.
        for property in point:
            if property not in ignoreProperties:
                pointListingProperties[property][point['crawler']] = point[property]

    avgRating = avgRating / ratingCount

    pointAggregated = PointAggregated(countryName=countryName, cityName=cityName, pointName=maxLenPointName,
                                      avgRating=avgRating, ratingCount=ratingCount).jsonify()

    # append all points uuid
    for point in listOfPOIs:
        pointAggregated['sources'].append(point['_uuid'])

    for point_prop in pointListingProperties:
        value = None
        if 'tripexpert' in pointListingProperties[point_prop]:
            value = pointListingProperties[point_prop]['tripexpert']

        if value is None and 'tripAdvisor' in pointListingProperties[point_prop]:
            value = pointListingProperties[point_prop]['tripAdvisor']

        if value is None and 'skyscanner' in pointListingProperties[point_prop]:
            value = pointListingProperties[point_prop]['skyscanner']

        if value is None and 'inspirock' in pointListingProperties[point_prop]:
            value = pointListingProperties[point_prop]['inspirock']

        if value is None and 'viator_v2' in pointListingProperties[point_prop]:
            value = pointListingProperties[point_prop]['viator_v2']

        pointAggregated[point_prop] = value

    return pointAggregated


def listOfPOIsToPointAggregators(amount: int) -> List[JPA]:
    """select the top 'amount' POIs per city. Aggregate and return those top POIs as a list"""
    # note: all top pois for all cities go into the same list
    topPoints = []
    for city in combinedPOIsListByCity:
        for i in range(len(combinedPOIsListByCity[city])):
            if i < amount:
                pointAggregated = combinePOIsInPointAggregated(combinedPOIsListByCity[city][i])
                topPoints.append(pointAggregated)
    return topPoints

def sortAllCitiesData(combinedPOIsListByCity,prioritiesOfPOIsByCity,priorityIndex,priorityToIndexMapping):
    for city in combinedPOIsListByCity:
        mergeSort(prioritiesOfPOIsByCity[city], combinedPOIsListByCity[city], priorityIndex,priorityToIndexMapping, 0, len(combinedPOIsListByCity[city]) - 1)
        outFile = open(city, 'w')
        for i in range(len(combinedPOIsListByCity[city])):
            for point in combinedPOIsListByCity[city][i]:
                outFile.write(str(point['pointName'].encode('utf-8')))
                outFile.write(",")
            outFile.write(str(prioritiesOfPOIsByCity[city][i][priorityIndex]))
            outFile.write("\n")
        outFile.close()
    return combinedPOIsListByCity;


crawlerPointListings: List[List[JPL]] = loadAllFiles(filesToProcess, citiesToProcess)
combinedPOIsListByCity: Dict[str, List[List[JPL]]] = combinePOIsByCity(crawlerPointListings, acceptableFuzzyScore)

prioritiesOfPOIsByCity = getPrioritiesValue(combinedPOIsListByCity, weightsOfPriority, crawlerToIndexMapping,priorityToIndexMapping)

priorityString = 'weightedPrioritiesIndex'
priorityIndex = priorityToIndexMapping[priorityString]

sortAllCitiesData(combinedPOIsListByCity, prioritiesOfPOIsByCity, priorityIndex, priorityToIndexMapping)

numAttractions = 50
aggregatorList = listOfPOIsToPointAggregators(numAttractions)

outFileName = "combinedPOIsAndRanking/Aggregated_Data/" + "priority:" + priorityString + ",sites:" + str(
    len(filesToProcess)) + ",numPointsEachCity" + str(numAttractions) + ",output_newAlR.json"

savePOIs(outFileName, aggregatorList)



