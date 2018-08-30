import json
import sys
import random
from math import radians, sin, cos, atan2, sqrt
sys.path.append('.')
from utilities import getWilsonScore, roundUpTime


def gratificationScoreOfSequence(pointsInOrder):
    # TODO: improve this?
    return sum(point['gratificationScore'] for point in pointsInOrder)



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


def getBestSequence(sequences, totalTime):
    maxGScore = -float('inf')
    maxGScoreSequence = []
    print('Number of sequences to check for gratification:', len(sequences))
    for sequence in sequences:
        gScore = gratificationScoreOfSequence([item['point'] for item in sequence])
        if gScore > maxGScore:
            maxGScore = gScore
            maxGScoreSequence = sequence

    return maxGScoreSequence, maxGScore

# assume start point is already added in currentSequence
def possibleSequencesBWStartPointAndEndTime(listOfPoints, visitedPoints, startPoint, currentSequence,
                                            startPointExitTime, endTime, dayNum, possibleSequences):
    possibleSequences.append(currentSequence)
    for index, point in enumerate(listOfPoints):
        if not visitedPoints[index]:
            travelTime = getTravelTime(startPoint, point)
            visitingTime = roundUpTime(float(point['recommendedNumHours']))
            pointEnterTime = roundUpTime(startPointExitTime + travelTime)
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


# it will add only endpoint always and other point before endpoint only when possible
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
    allData = readAllData('../aggregatedData/latest/data.json')

    countryName = "United States of America"
    cityName = 'New York City'
    cityTopPoints = getTopPointsOfCity(allData, countryName, cityName)

    cityTopPointsWithLatlng = []
    for point in cityTopPoints:
        if point['coordinates'] is not None:
            cityTopPointsWithLatlng.append(point)


    numPoints=7
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