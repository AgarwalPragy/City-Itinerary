import json
import sys
sys.path.append('.')
from collections import defaultdict
from sklearn.cluster import KMeans
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
import time
from tunable import weightOfMaxGscoreClusterSelection, weightOfAvgGscoreClusterSelection, weightOfNumPointsClusterSelection
from tunable import weightOfDistancePointSelection, weightOfGscorePointSelection
from tunable import clientDefaultStartTime, clientDefaultEndTime, pFactorMore, pFactorLess
from itineraryPlanner import getDayItinerary
from utilities import latlngDistance

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
            topPoints.append(point)
            addedAmount += 1
        else:
            break
    return topPoints

def getGScoreOfPoint(point, pFactor):
    if pFactor == 'less':
        return point['gratificationScore']**pFactorLess
    else:
        return point['gratificationScore']**pFactorMore


def getAvgMaxGscore(listOfPoints, pFactor):
    maxGscore = -float('inf')
    avgGscore = 0

    for point in listOfPoints:
        gscoreOfPoint = getGScoreOfPoint(point, pFactor)
        avgGscore += gscoreOfPoint
        if maxGscore < gscoreOfPoint:
            maxGscore = gscoreOfPoint

    avgGscore = avgGscore/len(listOfPoints)
    return maxGscore, avgGscore


def getWeightedScoreOfCluster(listOfPoints, pFactor):
    maxGscore, avgGscore = getAvgMaxGscore(listOfPoints, pFactor)
    numPoints = len(listOfPoints)

    return weightOfAvgGscoreClusterSelection*avgGscore + weightOfMaxGscoreClusterSelection*maxGscore + weightOfNumPointsClusterSelection*numPoints


def getWeightedScoreOfPoint(point, centerOfCluster, pFactor):
    [lat, lng] = map(float, point['coordinates'].split(','))
    [centerX, centerY] = centerOfCluster
    distance = latlngDistance(lat, lng, centerX, centerY)
    pointGscore = getGScoreOfPoint(point, pFactor)
    return -weightOfDistancePointSelection*distance + weightOfGscorePointSelection * pointGscore

# allSelectedPoints: already selected points
def getBestPoints(listOfPoints, allSelectedPoints, numDays: int, numPoints: int, pFactor, Debug=False):
    dayWiseClusteredData = defaultdict(list)

    coordinatesData = []
    for point in listOfPoints:
        coordinates = point['coordinates']
        lat, lng = map(float, coordinates.split(','))
        coordinatesData.append([lat, lng])

    coordinatesInArrayFormat = np.array(coordinatesData)
    try:
        kMeans = KMeans(n_clusters=numDays, max_iter=100, n_init=10, tol=1e-6).fit(coordinatesInArrayFormat)
    except Exception as e:
        print('Error:', e)
        return listOfPoints
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
        weightedValue = getWeightedScoreOfCluster(dayWiseClusteredData[day], pFactor)
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
                    weightedScore = getWeightedScoreOfPoint(point, maxWeightClusterCenter, pFactor)
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
    countryName = "France"
    cityName = 'Paris'
    cityTopPoints = getTopPointsOfCity(allData, countryName, cityName, amount=100)

    cityTopPoints = [point for point in cityTopPoints if point['coordinates'] is not None][:50]
    numDays = 5

    # tstart = time.time()
    selectedPoints = []
    itinerayLabels = []
    Debug = False
    pFactor = 'more'
    numPoints = 8
    itineraryDayWiseCoordinates = []
    for day in range(numDays):
        print('day: ', day)
        clusteredPoints = getBestPoints(cityTopPoints, selectedPoints, numDays-day, numPoints, pFactor, Debug)

        print('clustered points: ')
        for index, point in enumerate(clusteredPoints):
            print(index, point['pointName'])

        itinerarySeq, maxGscore = getDayItinerary(clusteredPoints, [], [], clientDefaultStartTime, clientDefaultEndTime, day, pFactor)

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