import json
import sys
import random
from math import radians, sin, cos, atan2, sqrt
import re
from collections import defaultdict
from sklearn.cluster import KMeans
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np

sys.path.append('.')
from utilities import getWilsonScore, roundUpTime


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


# this will return enterTime of place based on opening and closing hour if possible otherwise it will return -1
def getEnterTimeBasedOnOpeningHour(point, enterTime, exitTime, dayNum):
    openHourOfDay = point['openingHour'].split(',')[dayNum]

    closeHourOfDay = point['closingHour'].split(',')[dayNum]

    if openHourOfDay == '$' or closeHourOfDay == '$': #closed for that day
        return -1
    else:
        openHourOfDay = float(openHourOfDay)
        closeHourOfDay = float(closeHourOfDay)

    if enterTime >= openHourOfDay and exitTime <= closeHourOfDay:
        return enterTime
    elif enterTime < openHourOfDay and exitTime < closeHourOfDay:
        return openHourOfDay
    else:
        return -1


def getDistance(point1, point2):
    # approximate radius of earth in km
    R = 6373.0
    [lat1, lon1] = point1['coordinates'].split(',')
    [lat2, lon2] = point2['coordinates'].split(',')
    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return distance * 2 # to make approximate same as path distance


def getTravelTime(point1, point2):
    distance = getDistance(point1, point2)
    return roundUpTime(distance/40.0)  # assumed avg speed 40km/hr


def gratificationScoreOfSeq(sequenceOfPoints, totalTime):
    gScore = 0
    travelTime = 0
    avgWilsonScore  = 0
    avgRank = 0
    for index, seqData in enumerate(sequenceOfPoints):

        avgWilsonScore += getWilsonScore(seqData['point']['avgRating'] / 10, seqData['point']['ratingCount'])

        avgRank += seqData['point']['rank']  # normalize between 0-10

        if index < len(sequenceOfPoints) - 1:
            travelTime += sequenceOfPoints[index+1]['enterTime'] - seqData['exitTime']

    gScore -= avgRank/(5*len(sequenceOfPoints))
    gScore += avgWilsonScore*10/len(sequenceOfPoints)
    gScore -= (travelTime / totalTime) * 10  # normalize between 0-10
    # want more number of attraction
    gScore += len(sequenceOfPoints)  #normalize bw 1-10 since each we are considering max 10 points

    return gScore


def getBestSequence(sequences, totalTime):
    maxGScore = -float('inf')
    maxGScoreSequence = []
    for sequence in sequences:
        gScore = gratificationScoreOfSeq(sequence, totalTime)
        if gScore > maxGScore:
            maxGScore = gScore
            maxGScoreSequence = sequence

    return maxGScoreSequence, maxGScore


def getDayWiseClusteredListOfPoints(pointsOfCity, numDays: int):
    dayWiseClusteredData = defaultdict(list)
    latLngToPoint = defaultdict()
    coordinatesData = []
    for point in pointsOfCity:

        coordinates = point['coordinates']
        [lat, lng] = coordinates.split(',')

        key = str(lat) + ", " + str(lng)
        latLngToPoint[key] = point

        coordinatesData.append([lat, lng])

    coordinatesInArrayFormat = np.array(coordinatesData)

    #
    kMeans = KMeans(n_clusters=numDays, max_iter=500).fit(coordinatesInArrayFormat)

    predictedClusters = kMeans.predict(coordinatesInArrayFormat)

    for index, value in enumerate(coordinatesData):
        [lat, lng] = value
        key = str(lat) + ", " + str(lng)
        dayWiseClusteredData[predictedClusters[index]].append(latLngToPoint[key])


    for day in dayWiseClusteredData:
        print(day)
        for point in dayWiseClusteredData[day]:
            print(point['pointName'])
        print('\n\n')

    print(coordinatesInArrayFormat[:, 0], coordinatesInArrayFormat[:, 1])
    plt.scatter(coordinatesInArrayFormat[:, 0], coordinatesInArrayFormat[:, 1], c=kMeans.labels_, cmap='rainbow')
    plt.show()

    return dayWiseClusteredData


# assume start point is already added in currentSequence
def possibleSequencesBWStartPointAndEndTime(listOfPoints, visitedPoints, startPoint, currentSequence,
                                            startPointExitTIme, endTime, dayNum, possibleSequences):
    possibleSequences.append(currentSequence)
    for index, point in enumerate(listOfPoints):
        if not visitedPoints[index]:
            travelTime = getTravelTime(startPoint, point)
            visitingTime = roundUpTime(float(point['recommendedNumHours']))
            pointEnterTime = roundUpTime(startPointExitTIme + travelTime)
            pointExitTime = roundUpTime(pointEnterTime + visitingTime)

            pointEnterTimeBasedOnOpeningHour = getEnterTimeBasedOnOpeningHour(point, pointEnterTime, pointExitTime, dayNum)

            if pointEnterTimeBasedOnOpeningHour < 0:
                continue
            else:
                pointEnterTime = roundUpTime(pointEnterTimeBasedOnOpeningHour)
                pointExitTime = roundUpTime(pointEnterTime + visitingTime)

            if pointExitTime < endTime:
                newVisitedList = visitedPoints[:]
                newVisitedList[index] = True
                newSequence = currentSequence[:]
                pointInSeqFormat = {'point': point, 'enterTime': pointEnterTime, 'exitTime': pointExitTime}
                newSequence.append(pointInSeqFormat)

                possibleSequencesBWStartPointAndEndTime(listOfPoints, newVisitedList, point, newSequence,
                                                        pointExitTime, endTime, dayNum, possibleSequences)


# assume start point is already added in currentSequence
def possibleSequencesBWStartAndEndPoint(listOfPoints, visitedPoints, startPoint, startPointExitTIme, endPoint,
                                        endPointEnterTime, endPointExitTime, currentSequence, dayNum, possibleSequences):
    # case 1
    newSequence = currentSequence[:]
    endPointInSeqFormat = {'point': endPoint, 'enterTime': endPointEnterTime, 'exitTime': endPointExitTime}
    newSequence.append(endPointInSeqFormat)
    possibleSequences.append(newSequence)

    # case 2
    for index, point in enumerate(listOfPoints):
        if not visitedPoints[index]:
            travelTimeStartPointToPoint = getTravelTime(startPoint, point)
            visitingTimeOfPoint = roundUpTime(float(point['recommendedNumHours']))
            travelTimePointToEndPoint = getTravelTime(point, endPoint)

            pointEnterTime = roundUpTime(startPointExitTIme + travelTimeStartPointToPoint)
            pointExitTime = roundUpTime(pointEnterTime + visitingTimeOfPoint)

            pointEnterTimeBasedOnOpeningHour = getEnterTimeBasedOnOpeningHour(point, pointEnterTime, pointExitTime, dayNum)

            if pointEnterTimeBasedOnOpeningHour < 0:
                continue
            else:
                pointEnterTime = roundUpTime(pointEnterTimeBasedOnOpeningHour)
                pointExitTime = roundUpTime(pointEnterTime + visitingTimeOfPoint)

            if pointExitTime + travelTimePointToEndPoint < endPointEnterTime:
                newVisitedList = visitedPoints[:]
                newVisitedList[index] = True

                newSequence = currentSequence[:]
                pointInSeqFormat = {'point': point, 'enterTime': pointEnterTime, 'exitTime': pointExitTime}
                newSequence.append(pointInSeqFormat)

                possibleSequencesBWStartAndEndPoint(listOfPoints, newVisitedList, point, pointExitTime, endPoint,
                                                    endPointEnterTime, endPointExitTime, newSequence, dayNum, possibleSequences)


# it will add only endpoint always and other point only when possible
def possibleSequencesBWStartTimeAndEndPoint(listOfPoints, visitedPoints, currentSequence, endPoint, startTime,
                                            endPointEnterTime, endPointExitTime, dayNum):
    possibleSequences = []
    for index, startPoint in enumerate(listOfPoints):
        if not visitedPoints[index]:
            visitingTimeOfPoint = roundUpTime(float(startPoint['recommendedNumHours']))
            travelTimeToEndPoint = getTravelTime(startPoint, endPoint)

            pointEnterTime = roundUpTime(startTime)
            pointExitTime = roundUpTime(startTime + visitingTimeOfPoint)

            pointEnterTimeBasedOnOpeningHour = getEnterTimeBasedOnOpeningHour(point, pointEnterTime, pointExitTime, dayNum)

            if pointEnterTimeBasedOnOpeningHour < 0:
                continue
            else:
                pointEnterTime = roundUpTime(pointEnterTimeBasedOnOpeningHour)
                pointExitTime = roundUpTime(pointEnterTime + visitingTimeOfPoint)

            if pointExitTime + travelTimeToEndPoint < endPointEnterTime:
                newVisitedList = visitedPoints[:]
                newVisitedList[index] = True

                newSequence = currentSequence[:]

                pointInSeqFormat = {'point': startPoint, 'enterTime': pointEnterTime, 'exitTime': pointExitTime}
                newSequence.append(pointInSeqFormat)
                # this will add all possible sequence which end with endPoint and have some points in starting
                possibleSequencesBWStartAndEndPoint(listOfPoints, newVisitedList, startPoint, pointExitTime,
                                                    endPoint, endPointEnterTime, endPointExitTime, newSequence,
                                                    dayNum, possibleSequences)

    # we also need to add only endPoint no any other points
    pointInSeqFormat = {'point': endPoint, 'enterTime': endPointEnterTime, 'exitTime': endPointExitTime}
    possibleSequences.append([pointInSeqFormat])

    return possibleSequences


def getDayItinerary(listOfPoints, mustVisitPoints, mustVisitPlaceEnterExitTime, mustNotVisitPoints, dayStartTime,
                    dayEndTime, dayNum):
    possibleSequences = []
    visitedPoints = [False] * len(listOfPoints)

    for notVisitPoint in mustNotVisitPoints:
        visitedPoints[listOfPoints.index(notVisitPoint)] = True

    if len(mustVisitPoints) == 0:
        # we can choose any start point
        for index, startPoint in enumerate(listOfPoints):
            if not visitedPoints[index]:
                startPointEnterTime = roundUpTime(dayStartTime)
                startPointVisitingTime = roundUpTime(float(startPoint['recommendedNumHours']))
                startPointExitTime = roundUpTime(startPointEnterTime + startPointVisitingTime)

                pointEnterTimeBasedOnOpeningHour = getEnterTimeBasedOnOpeningHour(startPoint, startPointEnterTime, startPointExitTime, dayNum)

                if pointEnterTimeBasedOnOpeningHour < 0:
                    continue
                else:
                    startPointEnterTime = roundUpTime(pointEnterTimeBasedOnOpeningHour)
                    startPointExitTime = roundUpTime(startPointEnterTime + startPointVisitingTime)

                visitedPointsForStartPoint = visitedPoints[:]
                visitedPointsForStartPoint[index] = True

                currentSequence = [{'point': startPoint, 'enterTime': startPointEnterTime, 'exitTime': startPointExitTime}]

                possibleSequencesBWStartPointAndEndTime(listOfPoints, visitedPointsForStartPoint, startPoint,
                                                        currentSequence, startPointExitTime, dayEndTime, dayNum, possibleSequences)
    else:
        for mustVisitPoint in mustVisitPoints:
            visitedPoints[listOfPoints.index(mustVisitPoint)] = True
        #we can also add point before must visit first point if we can't then this function will add first point in sequence
        firstPointEnterTime = mustVisitPlaceEnterExitTime[0][0]
        firstPointExitTime = mustVisitPlaceEnterExitTime[0][1]
        endPoint = mustVisitPoints[0]
        possibleSequences = possibleSequencesBWStartTimeAndEndPoint(listOfPoints, visitedPoints, [], endPoint,
                                                                    dayStartTime, firstPointEnterTime,
                                                                    firstPointExitTime, dayNum)

        for index, startPoint in enumerate(mustVisitPoints):
            startPointExitTime = mustVisitPlaceEnterExitTime[index][1]  # end Time will be now start time for sequence

            possibleSequencesAfterIter = []  # each iteration of loop will create new possible sequence based on previous iteration possibleSequences
            if index < len(mustVisitPoints) - 1:  # for this we have start point and end point always
                for sequence in possibleSequences:
                    visitedPointsForSeq = visitedPoints[:]

                    for seqPointData in sequence:
                        visitedPointsForSeq[listOfPoints.index(seqPointData['point'])] = True

                    endPoint = mustVisitPoints[index + 1]
                    endPointEnterTime = mustVisitPlaceEnterExitTime[index + 1][0]
                    endPointExitTime = mustVisitPlaceEnterExitTime[index + 1][1]

                    possibleSequencesBWStartAndEndPoint(listOfPoints, visitedPointsForSeq, startPoint,
                                                        startPointExitTime, endPoint, endPointEnterTime,
                                                        endPointExitTime, sequence, dayNum, possibleSequencesAfterIter)

            else:
                for sequence in possibleSequences:
                    visitedPointsForSeq = visitedPoints[:]

                    for seqPointData in sequence:
                        visitedPointsForSeq[listOfPoints.index(seqPointData['point'])] = True

                    possibleSequencesBWStartPointAndEndTime(listOfPoints, visitedPointsForSeq, startPoint, sequence,
                                                            startPointExitTime, dayEndTime, dayNum, possibleSequencesAfterIter)

            possibleSequences = possibleSequencesAfterIter[:]


    bestSequence = getBestSequence(possibleSequences, dayEndTime - dayStartTime)

    return bestSequence


def printSequence(sequence, startTime, GScore, dayNum):
    print("Sequence: Gscore: " + str(GScore))
    print("startTime: " + str(startTime))
    previousPoint = []
    for index, seqData in enumerate(sequence):
        print(str(index) + "\t" + seqData['point']['pointName'] + "\tEnterTime: " + str(
            seqData['enterTime']) + "\t" + "ExitTime: " + str(seqData['exitTime']) +
              "\tOpenHour: "+seqData['point']['openingHour'].split(',')[dayNum] + "\tCloseHour: "+
              seqData['point']['closingHour'].split(',')[dayNum])

        visitingTime = float(seqData['point']['recommendedNumHours'])
        print("visitingTime: " + str(visitingTime))

        if index >= 1:
            distance = getDistance(seqData['point'], previousPoint)
            print("distance: " + str(distance))
            travelTime = getTravelTime(seqData['point'], previousPoint)
            print("travelling Time: " + str(travelTime) + " hour")

        previousPoint = seqData['point']
        print('\n\n')




if __name__ == '__main__':
    allData = readAllData('../aggregatedData/frequency/data.json')

    countryName = "United Kingdom"
    cityName = 'London'
    cityTopPoints = getTopPointsOfCity(allData, countryName, cityName)

    for point in cityTopPoints:
        if point['coordinates'] is None:
            lat = random.uniform(51, 51.5)  # london lat range
            lng = random.uniform(-0.2, 0.2)  # london lng range
            point['coordinates'] = str(lat) + "," + str(lng)
    #cityTopPoints = preprocessPoints(cityTopPoints)

    # dayWiseClusteredData = getDayWiseClusteredListOfPoints(cityTopPoints, 5)
    #
    #
    # for day in dayWiseClusteredData:
    #     print(day)
    #     for point in dayWiseClusteredData[day]:
    #         print(point['pointName'])
    #     print('\n\n')
    #
    # exit(0)



    numPoints=10
    listOfPoints = cityTopPoints[:numPoints]



    print("points: ")
    for index, point in enumerate(listOfPoints):
        print(str(index) + "\t" + point['pointName'])
        
    startTime = 10
    endTime = 22
    dayNum = 0
    mustVisitPoints = []#[listOfPoints[0], listOfPoints[2]]  # , listOfPoints[3], listOfPoints[4]]

    mustVisitPointsTime = [[13, 14], [16, 17]]  # , [16.5, 17.5], [21, 22]]

    mustNotVisitPoints = []#[listOfPoints[5], listOfPoints[4]]

    print("\nMust Visit Points: ")
    for index, point in enumerate(mustVisitPoints):
        print(point['pointName'])
        print(mustVisitPointsTime[index])

    print("\nmust not visit points:")
    for index, point in enumerate(mustNotVisitPoints):
        print(point['pointName'])

    print('\n\n')
    bestSequence, maxGScore = getDayItinerary(listOfPoints, mustVisitPoints, mustVisitPointsTime, mustNotVisitPoints,
                                              startTime, endTime, dayNum)
    printSequence(bestSequence, startTime, maxGScore, dayNum)