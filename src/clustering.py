import json
import sys
sys.path.append('.')
from collections import defaultdict
from sklearn.cluster import KMeans
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np

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


def getDayWiseClusteredListOfPoints(topPointsOfCity, numDays: int):
    dayWiseClusteredData = defaultdict(list)

    latLngToPoint = defaultdict()
    coordinatesData = []
    for point in topPointsOfCity:

        coordinates = point['coordinates']
        lat, lng = map(float, coordinates.split(','))

        key = coordinates
        latLngToPoint[key] = point

        coordinatesData.append([lat, lng])

    coordinatesInArrayFormat = np.array(coordinatesData)
    kMeans = KMeans(n_clusters=numDays, max_iter=1000, n_init=30, tol=1e-14).fit(coordinatesInArrayFormat)
    predictedClusters = kMeans.predict(coordinatesInArrayFormat)

    for index, value in enumerate(coordinatesData):
        [lat, lng] = value
        key = str(lat) + "," + str(lng)
        dayWiseClusteredData[predictedClusters[index]].append(latLngToPoint[key])

    for day in dayWiseClusteredData:
        print(day)
        for point in dayWiseClusteredData[day]:
            print(point['pointName'])
        print('\n\n')

    # print(coordinatesInArrayFormat[:, 0], coordinatesInArrayFormat[:, 1])
    plt.scatter(coordinatesInArrayFormat[:, 0], coordinatesInArrayFormat[:, 1], c=kMeans.labels_, cmap='rainbow')
    plt.show()

    return dayWiseClusteredData

if __name__ == '__main__':
    allData = readAllData('../aggregatedData/latest/data.json')
    countryName = "France"
    cityName = 'Paris'
    cityTopPoints = getTopPointsOfCity(allData, countryName, cityName)

    # for index,point in enumerate(cityTopPoints):
    #     print(str(index) + "\t" + point['pointName'])

    clusteredData = getDayWiseClusteredListOfPoints(cityTopPoints, 4)
