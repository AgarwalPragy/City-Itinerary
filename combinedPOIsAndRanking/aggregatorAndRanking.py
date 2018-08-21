import json 
from fuzzywuzzy import fuzz
import sys
sys.path.append('.')

from entities import *
from utilities import *

from rankingOfSites import alexa_ranking, similar_web_ranking

cities = ['london', 'dubai', 'bangkok']
files = ["specificCrawler/skyscanner.json", "specificCrawler/inspirock.json","specificCrawler/tripadvisor.json", "specificCrawler/viator.json"]
json_objects = []

combinedPOIsListByCity = {} 
prioritiesOfPOIsByCity = {}

acceptableFuzzyScore = 90


crawlerToIndex = {'skyscanner' : 0, 'inspirock' : 1, 'tripadvisor' : 2, 'viator_v2' : 3}
priorityFreqIndex = 0
priorityWeightedRatingIndex = 1
priorityFreqWithAlexaRanking = 2
priorityFreWithSimilarWebGranking = 3
priorityWisonScoreIndex = 4
numOfPriorities = 5


maxRatAndCountByCrawlerInCity = {}

def getMaxRatingAndReviewCount(crawler, cityName):
	maxRating  = 0
	maxCount = 0
	for POI in json_objects[crawlerToIndex[crawler]]:
		if POI['cityName'] == cityName:
			if POI['avgRating'] is not None:
				if(POI['avgRating'] > maxRating):
					maxRating = POI['avgRating']
					maxCount = POI['ratingCount']

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
			#print('\nName: ' + str(len(POI_combination)))
			ratingCount = 0
			avgRating = 0
			weightedAlexaNumerator = 0
			weightedAlexaDenominator = 0
			weightedSWebGNumerator = 0
			weightedSWebGDenominator = 0
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
					weightedSWebGNumerator += POI['rank'] / (similar_web_ranking[POI['crawler']]['gRank'] * 1.0)

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
					weightedSWebGNumerator += siteRankOfPOI / (similar_web_ranking[POI['crawler']]['gRank'])
				weightedAlexaDenominator += 1.0/alexa_ranking[POI['crawler']]
				weightedSWebGDenominator += 1.0/similar_web_ranking[POI['crawler']]['gRank']


			priority_list[priorityFreqIndex] = freq
			if ratingCount != 0:
				avgRating = avgRating / ratingCount
				wilsonScore = getWilsonScore(avgRating / 10.0, ratingCount)
				priority_list[priorityWeightedRatingIndex] = avgRating
				priority_list[priorityWisonScoreIndex] = wilsonScore

			priority_list[priorityFreqWithAlexaRanking] = weightedAlexaNumerator/weightedAlexaDenominator
			if key in prioritiesOfPOIsByCity:
				prioritiesOfPOIsByCity[key].append(priority_list)
			else:
				prioritiesOfPOIsByCity[key] = [priority_list]

def isGreaterOrEqual(a, b):
	return a >= b

#list1, list2 are priority value and data1, data2 are aggregated data
def compareBasedOnPriorityIndex(list1, list2, priorityIndex):
	if priorityIndex == priorityFreqIndex or priorityIndex == priorityWeightedRatingIndex or priorityIndex == priorityWisonScoreIndex:
		return isGreaterOrEqual(list1[priorityIndex], list2[priorityIndex])
	elif priorityIndex == priorityFreqWithAlexaRanking or priorityIndex == priorityFreWithSimilarWebGranking:
		if list1[priorityFreqIndex] > list2[priorityFreqIndex]:
			return True
		elif list1[priorityFreqIndex] < list2[priorityFreqIndex]:
			return False
		else:
			return isGreaterOrEqual(list2[priorityIndex], list1[priorityIndex]) # want lower rank pois first



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
	i = 0	 # Initial index of first subarray
	j = 0	 # Initial index of second subarray
	k = low	 # Initial index of merged subarray

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




for file in files:
	with open(file, 'r') as f:
		json_obj = json.load(f)
		temp_obj = []

		for i in range(len(json_obj)):
			if json_obj[i]['_listingType'] == 'point':
				cityName = json_obj[i]['cityName'].lower().strip()

				if cityName in cities:
					temp_obj.append(json_obj[i])
		json_objects.append(temp_obj)


counter = [0] * len(files)
for i in range(len(json_objects)):
	for j in range(len(json_objects[i])):
		if json_objects[i][j]['_listingType'] == 'point':
			cityName = json_objects[i][j]['cityName'].lower()
			#countryName = json_objects[i][j]['countryName'].lower()
			pointName = json_objects[i][j]['pointName'].lower()

			temp = []
			temp.append(json_objects[i][j])

			for k in range(i+1, len(json_objects)):
				maxFuzzyScore = 0
				maxScoreIndex = 0
				for l in range(len(json_objects[k])):
					if json_objects[k][l]['_listingType'] == 'point':
						newCityName = json_objects[k][l]['cityName'].lower()
						#newCountryName = json_objects[k][l]['countryName'].lower()
						newPointName = json_objects[k][l]['pointName'].lower()

						if cityName == newCityName:# and countryName == newCountryName:
							tempFuzzyScore = fuzz.partial_ratio(pointName, newPointName)

							if tempFuzzyScore > maxFuzzyScore:
								maxFuzzyScore = tempFuzzyScore
								maxScoreIndex = l 
				#print("maxFuzzyScore " + str(maxFuzzyScore))
				if(maxFuzzyScore > acceptableFuzzyScore):
					temp.append(json_objects[k][maxScoreIndex])
					json_objects[k].remove(json_objects[k][maxScoreIndex])
			counter[len(temp) - 1] += 1
			key = cityName# + "," + countryName
			if key in combinedPOIsListByCity:
				combinedPOIsListByCity[key].append(temp)
			else:
				combinedPOIsListByCity[key] = [temp]


def combinePOIsInPointAggregated(listOfPOIs):
	ingnoreList = ['cityName','crawler','rank', 'crawlTimestamp', 'sourceURL', 'countryName', 'pointName', 'avgRating', 'ratingCount', '_listingType', '_uuid']
	cityName = listOfPOIs[0]['cityName']
	countryName = listOfPOIs[0]['countryName']

	pointListingPropBycrawler = {}
	for key in listOfPOIs[0]:
		if key not in ingnoreList:
			pointListingPropBycrawler[key] = {}

	maxLenPointName = ""
	avgRating = 0
	ratingCount = 0
	for POI in listOfPOIs:
		if len(POI['pointName']) > len(maxLenPointName):
			maxLenPointName = POI['pointName']
		if POI['avgRating'] is not None:
			if POI['ratingCount'] is not None:
				avgRating += POI['avgRating'] * POI['ratingCount']
				ratingCount += POI['ratingCount']
			else:
				avgRating += POI['avgRating'] * 1 # consider at least one person reviewed it 
				ratingCount += 1

		for key in POI:
			if key not in ingnoreList:
				pointListingPropBycrawler[key][POI['crawler']] = POI[key]

	#print(pointListingPropBycrawler)
	avgRating = avgRating / ratingCount

	pointAggregated = PointAggregated(countryName=countryName, cityName=cityName, pointName=maxLenPointName,
	avgRating=avgRating, ratingCount=ratingCount).jsonify()

	for POI in listOfPOIs:
		pointAggregated['sources'].append(POI['_uuid'])

	for point_prop in pointListingPropBycrawler:
		value = None
		if 'tripAdvisor' in pointListingPropBycrawler[point_prop]:
			value = pointListingPropBycrawler[point_prop]['tripAdvisor']

		if value is None and 'skyscanner' in pointListingPropBycrawler[point_prop]:
			value = pointListingPropBycrawler[point_prop]['skyscanner']

		if value is None and 'inspirock' in pointListingPropBycrawler[point_prop]:
			value = pointListingPropBycrawler[point_prop]['inspirock']


		if value is None and 'viator_v2' in pointListingPropBycrawler[point_prop]:
			value = pointListingPropBycrawler[point_prop]['viator_v2']
	
		pointAggregated[point_prop] = value

	return pointAggregated


def savePOIs(fileName, pointAggregatedList, ):
	data = json.dumps(pointAggregatedList, indent=4)
	
	with open(fileName, 'w') as f:
		f.write(data)

#slect top k number of pois per city by topPOIs = k
def listOfPOIsToPointAggregators(numTopPOIs):
	result = []

	for key in combinedPOIsListByCity:
		for i in range(len(combinedPOIsListByCity[key])):
			if i < numTopPOIs:
				pointAggregated  = combinePOIsInPointAggregated(combinedPOIsListByCity[key][i])
				result.append(pointAggregated)
	return result





print(counter)
counter = [0] * len(files)

for key in combinedPOIsListByCity:
	print(key)
	print(len(combinedPOIsListByCity[key]))
	for POI_comb in combinedPOIsListByCity[key]:
		counter[len(POI_comb) - 1] += 1


print(counter)

getPrioritiesValue()




# printing data and sorting based on priority index value
priority = "weightedAvg"
#overlAllDataFile = open("combinedPOIsAndRanking/Aggregated_Data/topPOIs" + priority, 'w')
priorityIndex = priorityWeightedRatingIndex
for key in combinedPOIsListByCity:
	mergeSort(prioritiesOfPOIsByCity[key], combinedPOIsListByCity[key],priorityIndex , 0, len(combinedPOIsListByCity[key]) - 1)
	outPutFile = open("combinedPOIsAndRanking/Aggregated_Data/city:"+key + ",sites:"+str(len(files))+",priority:"+priority+",fuzzyScore:" + str(acceptableFuzzyScore), 'w')
	for i in range(len(combinedPOIsListByCity[key])):
		maxLenPOIName = ""
		for POI in combinedPOIsListByCity[key][i]:
			outPutFile.write(POI['pointName'] + ", ")
			if len(maxLenPOIName) < len(POI['pointName']):
				maxLenPOIName = POI['pointName']
		#if(len(combinedPOIsListByCity[key][i]) >= 2):
			#overlAllDataFile.write(combinedPOIsListByCity[key][i][0]['countryName'] + "\t" +combinedPOIsListByCity[key][i][0]['cityName'] + "\t" +maxLenPOIName+"\n")
		outPutFile.write(str(prioritiesOfPOIsByCity[key][i][priorityFreqIndex]) +", " +str(prioritiesOfPOIsByCity[key][i][priorityIndex]) + "\n")
	outPutFile.close()


numAttraction = 50
# aggregate the top k points for each city and store same in the file 
aggregatorList = listOfPOIsToPointAggregators(numAttraction)
outFileName = "combinedPOIsAndRanking/Aggregated_Data/" + "priority:" + str(priority) + ",numPoints:" + str(numAttraction) + ",output.json"
savePOIs(outFileName, aggregatorList)


#overlAllDataFile.close()








