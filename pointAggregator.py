

def aggreagatePoints(pointCluster, countryName, cityName):
	return None
	# returns PointAggregated


def aggregateAllPointsOfCity(pointClustersOfCity, countryName, cityName):
	return [aggreagatePoints(cluster, countryName, cityName) for pointMainAlias, cluster in pointClustersOfCity.items()]

