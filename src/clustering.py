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
from tunable import weightOfMaxGscoreClusterSelection, weightOfAvgGscoreClusterSelection, weightOfNumPointsClusterSelection
from tunable import weightOfDistancePointSelection, weightOfGscorePointSelection
import time
from itineraryPlanner import getDayItinerary
from tunable import clientDefaultStartTime, clientDefaultEndTime
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


def getAvgMaxGscore(listOfPoints):
    maxGscore = -float('inf')
    avgGscore = 0

    for point in listOfPoints:
        avgGscore += point['gratificationScore']
        if maxGscore < point['gratificationScore']:
            maxGscore = point['gratificationScore']

    avgGscore = avgGscore/len(listOfPoints)
    return maxGscore, avgGscore


def getWeightedScoreOfCluster(listOfPoints):
    maxGscore, avgGscore = getAvgMaxGscore(listOfPoints)
    numPoints = len(listOfPoints)

    return weightOfAvgGscoreClusterSelection*avgGscore + weightOfMaxGscoreClusterSelection*maxGscore + weightOfNumPointsClusterSelection*numPoints


def getWeightedScoreOfPoint(point, centerOfCluster):
    [lat, lng] = map(float, point['coordinates'].split(','))
    [centerX, centerY] = centerOfCluster
    distance = getDistance(lat, lng, centerX, centerY)
    pointGscore = point['gratificationScore']
    return -weightOfDistancePointSelection*distance + weightOfGscorePointSelection * pointGscore

# allSelectedPoints: already selected points
def getBestPoints(listOfPoints, allSelectedPoints, numDays: int, numPoints: int, Debug=False):
    dayWiseClusteredData = defaultdict(list)

    coordinatesData = []
    for point in listOfPoints:
        coordinates = point['coordinates']
        lat, lng = map(float, coordinates.split(','))
        coordinatesData.append([lat, lng])

    coordinatesInArrayFormat = np.array(coordinatesData)

    kMeans = KMeans(n_clusters=numDays, max_iter=100, n_init=10, tol=1e-6).fit(coordinatesInArrayFormat)
    # print('iter: ', kMeans.n_iter_)
    # plot clustered data
    if Debug:
        plt.scatter(coordinatesInArrayFormat[:, 0], coordinatesInArrayFormat[:, 1], c=kMeans.labels_, cmap='rainbow')
        plt.title('clustered Data')
        plt.show()

    # predict cluster for points
    for point in listOfPoints:
        coordinates = point['coordinates']
        lat, lng = map(float, coordinates.split(','))
        clusterNumber = kMeans.predict([[lat, lng]])[0]
        dayWiseClusteredData[clusterNumber].append(point)


    # get maxWeighted Score cluster
    maxWeightedScoreIndex = 0
    maxWeightedScore = -float('inf')
    for day in dayWiseClusteredData:
        weightedValue = getWeightedScoreOfCluster(dayWiseClusteredData[day])
        if weightedValue > maxWeightedScore:
            maxWeightedScore = weightedValue
            maxWeightedScoreIndex = day
    maxWeightCluster = dayWiseClusteredData[maxWeightedScoreIndex]
    maxWeightClusterCenter = kMeans.cluster_centers_[maxWeightedScoreIndex]

    # max weighted cluster
    if Debug:
        print('cluster: ', maxWeightedScoreIndex, 'points: ', len(maxWeightCluster), 'center: ', maxWeightClusterCenter)
    # plot listOfPoints with already selected data
        alreadySelectedPointsCoordinates = []
        for point in allSelectedPoints:
            coordinates = point['coordinates']
            lat, lng = map(float, coordinates.split(','))
            alreadySelectedPointsCoordinates.append([lat, lng])
        allSelectedPointsCoordinatesArrayFormat = np.array(alreadySelectedPointsCoordinates)

        if alreadySelectedPointsCoordinates:
            plt.scatter(coordinatesInArrayFormat[:, 0], coordinatesInArrayFormat[:, 1], c=kMeans.labels_, cmap='rainbow')
            plt.scatter(allSelectedPointsCoordinatesArrayFormat[:, 0], allSelectedPointsCoordinatesArrayFormat[:, 1], color='#000000')
            plt.title('clustered data with already selected points')
            plt.show()

    result = []
    if len(maxWeightCluster) <= numPoints:
        result = maxWeightCluster
    else:
        takenPoints = [False] * len(maxWeightCluster)
        while len(result) < numPoints:
            maxWeightedScoreIndex = 0
            maxWeightedScore = -float('inf')

            for index, point in enumerate(maxWeightCluster):
                if not takenPoints[index]:
                    weightedScore = getWeightedScoreOfPoint(point, maxWeightClusterCenter)
                    if weightedScore > maxWeightedScore:
                        maxWeightedScore = weightedScore
                        maxWeightedScoreIndex = index

            result.append(maxWeightCluster[maxWeightedScoreIndex])
            takenPoints[maxWeightedScoreIndex] = True

    # plot all selected points
    if Debug:
        selectedPointsCoordinates = []
        for point in result:
            coordinates = point['coordinates']
            lat, lng = map(float, coordinates.split(','))
            selectedPointsCoordinates.append([lat, lng])

        selectedPointsCoordinatesInArrayFormat = np.array(selectedPointsCoordinates)
        plt.scatter(coordinatesInArrayFormat[:, 0], coordinatesInArrayFormat[:, 1], c=kMeans.labels_, cmap='rainbow')
        plt.scatter(selectedPointsCoordinatesInArrayFormat[:, 0], selectedPointsCoordinatesInArrayFormat[:, 1], color='#000000')
        plt.title('selected points')
        plt.show()

    return result

if __name__ == '__main__':
    allData = readAllData('../aggregatedData/latest/data.json')
    countryName = "India"
    cityName = 'Mumbai'
    cityTopPoints = getTopPointsOfCity(allData, countryName, cityName, amount=50)
    numDays = 5

    # tstart = time.time()
    selectedPoints = []
    itinerayLabels = []
    Debug = False
    numPoints = 10
    itineraryDayWiseCoordinates = []
    for day in range(numDays):
        print('day: ', day)
        clusteredPoints = getBestPoints(cityTopPoints, selectedPoints, numDays-day, numPoints, Debug)
        itinerarySeq, maxGscore = getDayItinerary(clusteredPoints, [], [], clientDefaultStartTime, clientDefaultEndTime, day)

        for index, seqData in enumerate(itinerarySeq):
            point = seqData['point']
            print(index, 'pointName: ', point['pointName'], 'enterTime: ', seqData['enterTime'], 'exitTime: ', seqData['exitTime'])
            [lat, lng] = map(float, point['coordinates'].split(','))
            itineraryDayWiseCoordinates.append([lat, lng])
            itinerayLabels.append(day)
            selectedPoints.append(point)
            cityTopPoints.remove(point)
    # tend = time.time()
    # print('Clustering took {} seconds'.format(tend - tstart))
    if Debug:
        itineraryDayWiseCoordinatesInArrayFormat = np.array(itineraryDayWiseCoordinates)
        plt.scatter(itineraryDayWiseCoordinatesInArrayFormat[:, 0], itineraryDayWiseCoordinatesInArrayFormat[:, 1], c=itinerayLabels, cmap='rainbow')
        plt.title('selected Clusters')
        plt.show()