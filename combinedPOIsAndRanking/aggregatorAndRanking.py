from typing import List, Dict, NewType, Any
import json
from fuzzywuzzy import fuzz
import sys
from collections import defaultdict
sys.path.append('.')

from entities import *
from utilities import *
from siteRankings import alexa_ranking, similar_web_ranking

JPL = NewType('JPL', Any) # Jsonified Point Listing
JPA = NewType('JPA', Any) # Jsonified Point Aggregated

acceptableFuzzyScore = 90

citiesToProcess = list(map(processName, ['london', 'dubai', 'bangkok']))
filesToProcess = ["specificCrawler/skyscanner.json", "specificCrawler/inspirock.json",
                  "specificCrawler/tripadvisor.json", "specificCrawler/viator.json", 'specificCrawler/tripexpert.json']
prioritiesOfPOIsByCity = {}

crawlerToIndex = {'skyscanner': 0, 'inspirock': 1, 'tripadvisor': 2, 'viator_v2': 3, 'tripexpert': 4}
priorityFreqIndex = 0
priorityWeightedRatingIndex = 1
priorityFreqWithAlexaRanking = 2
priorityFreWithSimilarWebGranking = 3
priorityWisonScoreIndex = 4
priorityWithWeigths = 5
numOfPriorities = 6

freqWeight = 0.4
wilsonScoreWeight = 0.4
alexaRankWeight = 0.1
swebRankWeight = 0.1
maxRatAndCountByCrawlerInCity = {}



#list1, list2 are priority value and data1, data2 are aggregated data
def compareBasedOnPriorityIndex(list1, list2, priorityIndex):
    if (priorityIndex == priorityFreqIndex
                or priorityIndex == priorityWeightedRatingIndex
                or priorityIndex == priorityWisonScoreIndex
                or priorityIndex == priorityWithWeigths):
        return list1[priorityIndex] >= list2[priorityIndex]

    elif priorityIndex == priorityFreqWithAlexaRanking or priorityIndex == priorityFreWithSimilarWebGranking:
        if list1[priorityFreqIndex] > list2[priorityFreqIndex]:
            return True
        elif list1[priorityFreqIndex] < list2[priorityFreqIndex]:
            return False
        else:
            return list2[priorityIndex] >= list1[priorityIndex] # want lower rank pois first


def merge(prioritiesListOfList, dataListOfList,priorityIndex, low, mid, high):
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
        if compareBasedOnPriorityIndex(leftPrioritiesListOfList[i],rightPrioritiesListOfList[j], priorityIndex):
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


def mergeSort(prioritiesListOfList, dataListOfList,priorityIndex, low, high):
    if low < high:
        mid = int((low+(high-1))/2)
        mergeSort(prioritiesListOfList, dataListOfList, priorityIndex, low, mid)
        mergeSort(prioritiesListOfList, dataListOfList, priorityIndex, mid+1, high)
        merge(prioritiesListOfList, dataListOfList, priorityIndex, low, mid, high)

def savePOIs(fileName: str, pointAggregatedList: List[JPA]):
    data = json.dumps(pointAggregatedList, indent=4)
    with open(fileName, 'w') as f:
        f.write(data)


def loadOneFile(filename: str) -> List[JPL]:
    with open(filename, 'r') as f:
        fileData = json.load(f)

    pointListingsForCrawler = []
    for item in fileData:
        if item['_listingType'] == 'point':
            cityName = item['cityName']
            if processName(cityName) in citiesToProcess:
                pointListingsForCrawler.append(item)
    return pointListingsForCrawler


def loadAllFiles(filenames: List[str]) -> List[List[JPL]]:
    result = []
    for filename in filenames:
        result.append(loadOneFile(filename))
    return result


def combinePOIsByCity(crawlerPointListings: List[List[JPL]]) -> Dict[str, List[List[JPL]]]:
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


crawlerPointListings: List[List[JPL]] = loadAllFiles(filesToProcess)
combinedPOIsListByCity: Dict[str, List[List[JPL]]] = combinePOIsByCity(crawlerPointListings)


def getMaxRatingAndReviewCount(crawler: str, cityName: str):
    # TODO: Make this function pure
    processedCityName = processName(cityName)
    maxRating  = 0
    maxCount = 0
    pointListings = crawlerPointListings[crawlerToIndex[crawler]]
    for pointListing in pointListings:
        if processName(pointListing['cityName']) == processedCityName:
            if pointListing['avgRating'] and pointListing['avgRating'] > maxRating:
                maxRating = pointListing['avgRating']
                maxCount = pointListing['ratingCount']

    maxCount += 1
    if crawler in maxRatAndCountByCrawlerInCity:
        maxRatAndCountByCrawlerInCity[crawler][cityName] = {'maxRating' : maxRating, 'maxCount' : maxCount}
    else:
        maxRatAndCountByCrawlerInCity[crawler] = {}
        maxRatAndCountByCrawlerInCity[crawler][cityName] = {'maxRating' : maxRating, 'maxCount' : maxCount}

def getPrioritiesValue():
    for key in combinedPOIsListByCity:
        for POI_combination in combinedPOIsListByCity[key]:
            priority_list = [0] * numOfPriorities
            freq = len(POI_combination)
            rating = 0
            # print('\nName: ' + str(len(POI_combination)))
            ratingCount = 0
            avgRating = 0
            weightedAlexaNumerator = 0
            weightedAlexaDenominator = 0
            weightedSWebGNumerator = 0
            weightedSWebGDenominator = 0

            overAllWeightedScore = 0
            for POI in POI_combination:
                #print(POI['pointName'])

                # weighted average of POIs
                if POI['avgRating'] is not None:
                    if POI['ratingCount'] is not None:
                        avgRating += POI['avgRating'] * POI['ratingCount']
                        ratingCount += POI['ratingCount']
                    else:
                        avgRating += POI['avgRating'] * 1 # consider at least one person reviewed this POI
                        ratingCount += 1

                # alexa ranking code
                if POI['rank'] is not None:
                    weightedAlexaNumerator += POI['rank'] / (alexa_ranking[POI['crawler']] * 1.0)
                    weightedSWebGNumerator += POI['rank'] / (similar_web_ranking[POI['crawler']] * 1.0)

                else:
                    rating = 0
                    ratingPoints = 1
                    if POI['avgRating'] is not None:
                        rating = POI['avgRating']
                    if POI['ratingCount'] is not None:
                        ratingPoints = POI['ratingCount']

                    if POI['crawler'] in maxRatAndCountByCrawlerInCity:
                        if POI['cityName'].strip() not in maxRatAndCountByCrawlerInCity[POI['crawler']]:
                            getMaxRatingAndReviewCount(POI['crawler'], POI['cityName'].strip())
                    else:
                        cityData = {}
                        getMaxRatingAndReviewCount(POI['crawler'], POI['cityName'])

                        cityData = maxRatAndCountByCrawlerInCity[POI['crawler']][POI['cityName']]
                        maxRating = cityData['maxRating']
                        maxCount = cityData['maxCount']

                    #predict siteRankOfPOI if not given on site
                    siteRankOfPOI = (maxRating + 1 - rating) * maxCount / (1.0 * ratingPoints)
                    weightedAlexaNumerator += siteRankOfPOI / (alexa_ranking[POI['crawler']]) # comsidering POI as a worst
                    weightedSWebGNumerator += siteRankOfPOI / (similar_web_ranking[POI['crawler']])
                weightedAlexaDenominator += 1.0/alexa_ranking[POI['crawler']]
                weightedSWebGDenominator += 1.0/similar_web_ranking[POI['crawler']]


            priority_list[priorityFreqIndex] = freq
            overAllWeightedScore += freq * freqWeight
            if ratingCount != 0:
                avgRating = avgRating / ratingCount
                wilsonScore = getWilsonScore(avgRating / 10.0, ratingCount)
                priority_list[priorityWeightedRatingIndex] = avgRating
                priority_list[priorityWisonScoreIndex] = wilsonScore
                overAllWeightedScore += wilsonScore * wilsonScoreWeight

            alexaScore = weightedAlexaNumerator / weightedAlexaDenominator
            swebScore = weightedSWebGNumerator / weightedSWebGDenominator
            # need to normalize data assumed 500 rank at max
            overAllWeightedScore -= alexaScore * alexaRankWeight
            overAllWeightedScore -= swebScore * swebRankWeight
            priority_list[priorityFreqWithAlexaRanking] = alexaScore
            priority_list[priorityFreWithSimilarWebGranking] = swebScore
            priority_list[priorityWithWeigths] = overAllWeightedScore
            if key in prioritiesOfPOIsByCity:
                prioritiesOfPOIsByCity[key].append(priority_list)
            else:
                prioritiesOfPOIsByCity[key] = [priority_list]



getPrioritiesValue()

# printing data and sorting based on priority index value
priority = "Freq"
# overlAllDataFile = open("combinedPOIsAndRanking/Aggregated_Data/topPOIs" + priority, 'w')
priorityIndex = priorityFreqIndex
for key in combinedPOIsListByCity:

    mergeSort(prioritiesOfPOIsByCity[key], combinedPOIsListByCity[key], priorityIndex, 0,
              len(combinedPOIsListByCity[key]) - 1)
    outPutFile = open("combinedPOIsAndRanking/Aggregated_Data/city:" + key + ",sites:" + str(
        len(filesToProcess)) + ",priority:" + priority + ",fuzzyScore:" + str(acceptableFuzzyScore), 'w')
    for i in range(len(combinedPOIsListByCity[key])):
        maxLenPOIName = ""
        for POI in combinedPOIsListByCity[key][i]:
            #outPutFile.write(POI['pointName'] + ", ")
            if len(maxLenPOIName) < len(POI['pointName']):
                maxLenPOIName = POI['pointName']
        # if(len(combinedPOIsListByCity[key][i]) >= 2):
        # overlAllDataFile.write(combinedPOIsListByCity[key][i][0]['countryName'] + "\t" +combinedPOIsListByCity[key][i][0]['cityName'] + "\t" +maxLenPOIName+"\n")
        outPutFile.write(str(prioritiesOfPOIsByCity[key][i][priorityFreqIndex]) + ", " + str(
            prioritiesOfPOIsByCity[key][i][priorityIndex]) + "\n")
    outPutFile.close()



numAttraction = 50
# aggregate the top k points for each city and store same in the file

def combinePOIsInPointAggregated(listOfPOIs: List[JPL]) -> JPA:
    ignoreList = ['cityName', 'crawler', 'rank', 'crawlTimestamp', 'sourceURL', 'countryName', 'pointName',
                   'avgRating', 'ratingCount', '_listingType', '_uuid']

    cityName = listOfPOIs[0]['cityName']
    countryName = listOfPOIs[0]['countryName']

    pointListingPropBycrawler = {}
    for key in listOfPOIs[0]:
        if key not in ignoreList:
            pointListingPropBycrawler[key] = {}

    maxLenPointName = ""
    avgRating = 0
    ratingCount = 1
    for POI in listOfPOIs:
        if len(POI['pointName']) > len(maxLenPointName):
            maxLenPointName = POI['pointName']
        if POI['avgRating'] is not None:
            if POI['ratingCount'] is not None:
                avgRating += POI['avgRating'] * POI['ratingCount']
                ratingCount += POI['ratingCount']
            else:
                avgRating += POI['avgRating'] * 1  # consider at least one person reviewed it
                ratingCount += 1

        for key in POI:
            if key not in ignoreList:
                pointListingPropBycrawler[key][POI['crawler']] = POI[key]

    # print(pointListingPropBycrawler)
    avgRating = avgRating / ratingCount

    pointAggregated = PointAggregated(countryName=countryName, cityName=cityName, pointName=maxLenPointName,
                                      avgRating=avgRating, ratingCount=ratingCount).jsonify()

    for POI in listOfPOIs:
        pointAggregated['sources'].append(POI['_uuid'])

    for point_prop in pointListingPropBycrawler:
        value = None
        if 'tripexpert' in pointListingPropBycrawler[point_prop]:
            value = pointListingPropBycrawler[point_prop]['tripexpert']

        if value is None and 'tripAdvisor' in pointListingPropBycrawler[point_prop]:
            value = pointListingPropBycrawler[point_prop]['tripAdvisor']

        if value is None and 'skyscanner' in pointListingPropBycrawler[point_prop]:
            value = pointListingPropBycrawler[point_prop]['skyscanner']

        if value is None and 'inspirock' in pointListingPropBycrawler[point_prop]:
            value = pointListingPropBycrawler[point_prop]['inspirock']

        if value is None and 'viator_v2' in pointListingPropBycrawler[point_prop]:
            value = pointListingPropBycrawler[point_prop]['viator_v2']

        pointAggregated[point_prop] = value

    return pointAggregated


def listOfPOIsToPointAggregators(amount: int) -> List[JPA]:
    """select the top 'amount' POIs per city. Aggregate and return those top POIs as a list"""
    # note: all top pois for all cities go into the same list
    topPoints = []

    for key, aggregatedPointListings in combinedPOIsListByCity.items():
        for i in range(len(aggregatedPointListings)):
            if i < amount:
                pointAggregated = combinePOIsInPointAggregated(aggregatedPointListings[i])
                topPoints.append(pointAggregated)
    return topPoints

aggregatorList = listOfPOIsToPointAggregators(numAttraction)
outFileName = "combinedPOIsAndRanking/Aggregated_Data/" + "priority:" + str(priority) + ",sites:" + str(
    len(filesToProcess)) + ",numPoints:" + str(numAttraction) + ",output.json"
savePOIs(outFileName, aggregatorList)


# overlAllDataFile.close()








