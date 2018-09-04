from scipy import stats
import numpy as np
import json
import sys
sys.path.append('.')
from tunable import outlierSelectionThreshold

def readAllData(filePath: str):
    with open(filePath, 'r') as f:
        allData = json.loads(f.read())
        return allData
    # countries = data.values()
    # cities = [city for country in countries for city in country['cities'].values()]
    # points = [point for city in cities for point in city['points'].values()]


def getTopPointsOfCity(allData, countryName, cityName, amount=50):
    topnames = allData[countryName]['cities'][cityName]['pointsOrder'][:amount]
    return [allData[countryName]['cities'][cityName]['points'][name] for name in topnames]

def getOutlierIndex(listOfPoints):
    coordinatesData = []
    for point in listOfPoints:
        lat, lng = map(float, point['coordinates'].split(','))
        coordinatesData.append([lat, lng])

    z_score = np.abs(stats.zscore(coordinatesData))
    outliers = np.where(z_score > outlierSelectionThreshold)
    outliersIndex = list(set(outliers[0]))
    return outliersIndex

def getCenterOfCity(listOfPoints):
    pointsWithCoordinates = [point for point in listOfPoints if point['coordinates'] is not None]
    outliersIndex = getOutlierIndex(pointsWithCoordinates)
    if outliersIndex:
        print(outliersIndex, 'pointName: ', listOfPoints[outliersIndex[0]]['pointName'])
    centerLat = 0
    centerLng = 0
    for index, point in enumerate(pointsWithCoordinates):
        if index not in outliersIndex:
            lat, lng = map(float, point['coordinates'].split(','))
            centerLat += lat
            centerLng += lng

    if len(pointsWithCoordinates) != len(outliersIndex):
        centerLat = centerLat/(len(pointsWithCoordinates) - len(outliersIndex))
        centerLng = centerLng/(len(pointsWithCoordinates) - len(outliersIndex))
    else:
        centerLat = None
        centerLng = None

    return [centerLat, centerLng]



if __name__ == '__main__':
    allData = readAllData('../aggregatedData/latest/data.json')
    countryName = "India"
    cityName = 'Mumbai'

    cityTopPoints = getTopPointsOfCity(allData, countryName, cityName, amount=100)

    center = getCenterOfCity(cityTopPoints)

    print(center)