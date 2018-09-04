from scipy import stats
import numpy as np
from typing import List
import sys
sys.path.append('.')
from tunable import outlierSelectionThreshold
from entities import PointAggregated


def getOutlierIndex(listOfPoints: List[PointAggregated]):
    coordinatesData = []
    for point in listOfPoints:
        lat, lng = map(float, point.coordinates.split(','))
        coordinatesData.append([lat, lng])

    z_score = np.abs(stats.zscore(coordinatesData))
    outliers = np.where(z_score > outlierSelectionThreshold)
    outliersIndex = list(set(outliers[0]))
    return outliersIndex


def getCenterOfCity(listOfPoints: List[PointAggregated]):
    pointsWithCoordinates = [point for point in listOfPoints if point.coordinates is not None]
    outliersIndex = getOutlierIndex(pointsWithCoordinates)
    centerLat = 0
    centerLng = 0
    for index, point in enumerate(pointsWithCoordinates):
        if index not in outliersIndex:
            lat, lng = map(float, point.coordinates.split(','))
            centerLat += lat
            centerLng += lng

    if len(pointsWithCoordinates) != len(outliersIndex):
        centerLat = centerLat/(len(pointsWithCoordinates) - len(outliersIndex))
        centerLng = centerLng/(len(pointsWithCoordinates) - len(outliersIndex))
    else:
        centerLat = None
        centerLng = None

    return [centerLat, centerLng]
