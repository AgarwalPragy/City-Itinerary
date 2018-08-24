from typing import List, TypeVar, Any, Dict, Tuple

from collections import defaultdict
from utilities import processName

from pointAggregator import aggregateAllPointsOfCity
from utilities import getBestCityName, doesFuzzyMatch


def readListingsFromFile() -> List[Any]:
	# TODO
	###################################
	###################################
	###################################
	###################################
	###################################
	###################################
	###################################
	return []


def getCityIdentifier(listing: Any) -> str:
	return '{}/{}'.format(listing["countryName"], listing["cityName"])


def getCityClusters(listings: List[Any]) -> Dict[str, List[str]]:
	"""Given all listings, returns a clustering of city names. {mainAlias -> [alias]}"""
	allCitiesAliases: List[str] = [
		getCityIdentifier(listing)
		for listing in listings
		if listing['_listingType'] in ['point']
	]
	chosenAlready = [False] * len(allCitiesAliases)

	cityClusters: Dict[str, List[str]] = defaultdict(list) # final city name -> list of city aliases


	for index1, cityAlias1 in enumerate(allCitiesAliases):
		if chosenAlready[index1]:
			continue

		for index2, cityAlias2 in enumerate(allCitiesAliases[index1+1:], index1+1):
			if doesFuzzyMatch(cityAlias1, cityAlias2):
				cityClusters[cityAlias1].append(cityAlias2)
				chosenAlready[index2] = True

	return cityClusters



def makeReverseCityIndex(cityClusters: Dict[str, List[str]]) -> Dict[str, str]:
	"""Retuns a mapping from an arbitrary city alias to its corresponding main alias"""
	cityAliasToMainalais: Dict[str, str] = {}
	for mainAlias, cluster in cityClusters.items():
		for alias in cluster:
			cityAliasToMainalais[alias] = mainAlias
	return cityAliasToMainalais


def getPointsForEachCity(cityAliasToMainalais: Dict[str, str], listings: List[Any]):
	"""Returns a mapping from cityMainAlias to list of points in all aliases of that city"""
	pointsOfEachCity: Dict[str, List[Any]] = defaultdict(list)

	for listing in listings:
		if listing['_listingType'] != 'point':
			continue

		cityAlias = getCityIdentifier(listing)
		mainAlias = cityAliasToMainalais[cityAlias]

		pointsOfEachCity[mainAlias].append(listing)

	return pointsOfEachCity


def getPointClusters(pointsOfOneCity: List[Any]):
	"""Returns a mapping from pointMainAlias to list of all points that match"""
	chosenAlready = [False] * len(pointsOfOneCity)
	pointClusters: Dict[str, List[Any]] = defaultdict(list) # final city name -> list of city aliases

	for index1, point1 in enumerate(pointsOfOneCity):
		if chosenAlready[index1]:
			continue

		for index2, point2 in enumerate(pointsOfOneCity[index1+1:], index1+1):
			if doesFuzzyMatch(point1['pointName'], point2['pointName']):
				pointClusters[point1['pointName']].append(point2)
				chosenAlready[index2] = True
	return pointClusters



if __name__ == '__main__':
	listings: List[Any] = readListingsFromFile()
	cityClusters = getCityClusters(listings)
	cityAliasToMainalais = makeReverseCityIndex(cityClusters)
	pointsOfEachCity = getPointsForEachCity(cityAliasToMainalais, listings)

	for cityMainAlias, pointsInThisCity in pointsOfEachCity.items():
		pointClusters = getPointClusters(pointsInThisCity)

		countryName, cityName = getBestCityName(cityClusters[cityMainAlias])

		aggregatedPointsOfCity = aggregateAllPointsOfCity(pointClusters, countryName, cityName)








