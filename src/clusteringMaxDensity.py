import json
import sys
sys.path.append('.')
from collections import defaultdict
from sklearn.cluster import KMeans
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
from math import radians, sin, cos, atan2, sqrt
import math
from tunable import weightOfDistancePointSelection, weightOfGscorePointSelection
import time

def readAllData(filePath: str):
    with open(filePath, 'r') as f:
        allData = json.loads(f.read())
        return allData
    # countries = data.values()
    # cities = [city for country in countries for city in country['cities'].values()]
    # points = [point for city in cities for point in city['points'].values()]


def getTopPointsOfCity(allData, countryName, cityName, amount=50):
    topnames = allData[countryName]['cities'][cityName]['pointsOrder']

    #TODO: get cooridnates of point from API
    topPoints = []
    addedAmount = 0
    for name in topnames:
        point = allData[countryName]['cities'][cityName]['points'][name]
        if addedAmount < amount:
            if point['coordinates'] is not None:
                topPoints.append(point)
                addedAmount += 1
        else:
            break
    return topPoints

def getDistance(lat1, lon1, lat2, lon2):
    # approximate radius of earth in km
    R = 6373.0
    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

def getGScoreAndDistanceWeightedValue(point, centerOfCluster):
    [lat, lng] = map(float, point['coordinates'].split(','))
    [centerX, centerY] = centerOfCluster

    distance = getDistance(lat, lng, centerX, centerY)
    gScore = point['gratificationScore']

    return -weightOfDistancePointSelection*distance + weightOfGscorePointSelection*gScore

def getPointsFromMaxPointsCluster(listOfPoints, numDays: int, numPoints: int):
    dayWiseClusteredData = defaultdict(list)

    coordinatesData = []
    for point in listOfPoints:
        coordinates = point['coordinates']
        lat, lng = map(float, coordinates.split(','))
        coordinatesData.append([lat, lng])

    coordinatesInArrayFormat = np.array(coordinatesData)

    kMeans = KMeans(n_clusters=numDays, max_iter=10, n_init=4, tol=1e-6).fit(coordinatesInArrayFormat)
    #print('iter: ', kMeans.n_iter_)

    for point in listOfPoints:
        coordinates = point['coordinates']
        lat, lng = map(float, coordinates.split(','))
        clusterNumber = kMeans.predict([[lat, lng]])[0]
        dayWiseClusteredData[clusterNumber].append(point)

    maxDensityClusterIndex = 0
    maxDensityClusterNumPoints = len(dayWiseClusteredData[0])
    for day in dayWiseClusteredData:
        if maxDensityClusterNumPoints < len(dayWiseClusteredData[day]):
            maxDensityClusterIndex = day
            maxDensityClusterNumPoints = len(dayWiseClusteredData[day])

    maxDensityClusterCenter = kMeans.cluster_centers_[maxDensityClusterIndex]
    maxDensityClusterPoints = dayWiseClusteredData[maxDensityClusterIndex]
    takenPoints = [False] * len(maxDensityClusterPoints)

    # plt.scatter(coordinatesInArrayFormat[:, 0], coordinatesInArrayFormat[:, 1], c=kMeans.labels_, cmap='rainbow')
    # plt.show()
    if len(maxDensityClusterPoints) <= numPoints:
        return maxDensityClusterPoints
    else:
        result = []
        while len(result) < numPoints:
            maxIndex = 0
            maxValue = -float('inf')
            for index, point in enumerate(maxDensityClusterPoints):
                if not takenPoints[index]:
                    value = getGScoreAndDistanceWeightedValue(point, maxDensityClusterCenter)
                    if maxValue < value:
                        maxValue = value
                        maxIndex = index
            result.append(maxDensityClusterPoints[maxIndex])
            takenPoints[maxIndex] = True
        return result



if __name__ == '__main__':
    allData = readAllData('../aggregatedData/latest/data.json')
    countryName = "India"
    cityName = 'Mumbai (Bombay)'
    cityTopPoints = getTopPointsOfCity(allData, countryName, cityName)
    numDays = 7

    # tstart = time.time()
    for day in range(numDays):
        clusteredPoints = getPointsFromMaxPointsCluster(cityTopPoints, numDays-day, 7)

        for point in clusteredPoints:
            #print(point['pointName'])
            cityTopPoints.remove(point)

    # tend = time.time()
    # print('Clustering took {} seconds'.format(tend - tstart))
