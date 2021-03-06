import json
import sys
from math import radians, sin, cos, atan2, sqrt
sys.path.append('.')
from utilities import roundUpTime, latlngDistance, floatCompare
from tunable import avgSpeedOfTravel, pFactorLess, pFactorMore
import time

def gratificationScoreOfSequence(pointsInOrder, pFactor):
    # TODO: improve this?
    if pFactor == 'less':
        gscore = sum(point['gratificationScore']**pFactorLess for point in pointsInOrder)
    else:
        gscore = sum(point['gratificationScore']**pFactorMore for point in pointsInOrder)
    return gscore


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
def getEnterTimeBasedOnOpeningHour(point, enterTime, exitTime, weekDay):
    openHourOfDay = point['openingHour'].split(',')[weekDay]

    closeHourOfDay = point['closingHour'].split(',')[weekDay]

    if openHourOfDay == '$' or closeHourOfDay == '$':#closed for that day
        return -1
    else:
        openHourOfDay = float(openHourOfDay)
        closeHourOfDay = float(closeHourOfDay)


    if enterTime >= openHourOfDay and exitTime <= closeHourOfDay:
        return enterTime
    elif enterTime < openHourOfDay and (exitTime - enterTime) + openHourOfDay <= closeHourOfDay:
        return openHourOfDay
    else:
        return -1


def getDistance(point1, point2):
    [lat1, lon1] = point1['coordinates'].split(',')
    [lat2, lon2] = point2['coordinates'].split(',')
    return latlngDistance(lat1, lon1, lat2, lon2)



def getTravelTime(point1, point2):
    distance = getDistance(point1, point2)
    return roundUpTime(distance/avgSpeedOfTravel)  # assumed avg speed 40km/hr


def getBestSequence(sequences, pFactor):
    maxGScore = -99999
    maxGScoreSequences = []
    print('Number of sequences to check for gratification:', len(sequences))
    for sequence in sequences:
        gScore = gratificationScoreOfSequence([seqData['point'] for seqData in sequence], pFactor)
        if gScore > maxGScore:
            maxGScore = gScore
            maxGScoreSequences = [sequence]
        elif floatCompare(gScore, maxGScore):
            maxGScoreSequences.append(sequence)

    print('Number of sequences:', len(maxGScoreSequences), 'with same gratification:', maxGScore)
    if len(maxGScoreSequences) == 0:
        maxGScoreSequence = []
    elif len(maxGScoreSequences) == 1:
        maxGScoreSequence = maxGScoreSequences[0]
    else:
        minTravelledDistance = float('inf')
        maxGScoreSequence = None
        for sequence in maxGScoreSequences:
            lastPoint = sequence[0]['point']
            travelledDistance = 0
            for index in range(1, len(sequence)):
                currentPoint = sequence[index]['point']
                travelledDistance += latlngDistance(*lastPoint['coordinates'].split(','), *currentPoint['coordinates'].split(','))
                lastPoint = currentPoint
            if floatCompare(travelledDistance, minTravelledDistance) and maxGScoreSequence is not None:
                points1 = [visit['point']['pointName'] for visit in sequence]
                points2 = [visit['point']['pointName'] for visit in maxGScoreSequence]
                if points1 < points2:
                    maxGScoreSequence = sequence
            elif travelledDistance < minTravelledDistance:
                minTravelledDistance = travelledDistance
                maxGScoreSequence = sequence


        print('Travelled distance in best sequence: ', minTravelledDistance)
    return maxGScoreSequence, maxGScore

# assume start point is already added in currentSequence and marked true in visitedPoints
def possibleSequencesBWStartPointAndEndTime(listOfPoints, visitedPoints, startPoint, currentSequence,
                                            startPointExitTime, endTime, weekDay, possibleSequences):
    possibleSequences.append(currentSequence)
    for index, point in enumerate(listOfPoints):
        pointName = point['pointName']
        if pointName not in visitedPoints:
            travelTime = getTravelTime(startPoint, point)
            visitingTime = roundUpTime(float(point['recommendedNumHours']))
            pointEnterTime = roundUpTime(startPointExitTime + travelTime)
            pointExitTime = roundUpTime(pointEnterTime + visitingTime)

            pointEnterTimeBasedOnOpeningHour = getEnterTimeBasedOnOpeningHour(point, pointEnterTime, pointExitTime, weekDay)

            if pointEnterTimeBasedOnOpeningHour < 0:
                continue
            else:
                pointEnterTime = roundUpTime(pointEnterTimeBasedOnOpeningHour)
                pointExitTime = roundUpTime(pointEnterTime + visitingTime)

            if pointExitTime <= endTime:
                visitedListForPoint = visitedPoints.copy()
                visitedListForPoint[pointName] = 1

                sequenceForPoint = currentSequence[:]
                pointInSeqFormat = {'point': point, 'enterTime': pointEnterTime, 'exitTime': pointExitTime}
                sequenceForPoint.append(pointInSeqFormat)

                possibleSequencesBWStartPointAndEndTime(listOfPoints=listOfPoints, visitedPoints=visitedListForPoint, startPoint=point,
                                                        currentSequence=sequenceForPoint, startPointExitTime=pointExitTime, endTime=endTime,
                                                        weekDay=weekDay, possibleSequences=possibleSequences)


# assume start point is already added in currentSequence
# startpoint and endpoint are marked true in list before calling this function
def possibleSequencesBWStartAndEndPoint(listOfPoints, visitedPoints, startPoint, startPointExitTIme, endPoint,
                                        endPointEnterTime, endPointExitTime, currentSequence, weekDay, possibleSequences):
    # case 1
    sequenceForEndPoint = currentSequence[:]
    endPointInSeqFormat = {'point': endPoint, 'enterTime': endPointEnterTime, 'exitTime': endPointExitTime}
    sequenceForEndPoint.append(endPointInSeqFormat)
    possibleSequences.append(sequenceForEndPoint)

    # case 2
    for index, point in enumerate(listOfPoints):
        pointName = point['pointName']
        if pointName not in visitedPoints:
            travelTimeStartPointToPoint = getTravelTime(startPoint, point)
            visitingTimeOfPoint = roundUpTime(float(point['recommendedNumHours']))
            travelTimePointToEndPoint = getTravelTime(point, endPoint)

            pointEnterTime = roundUpTime(startPointExitTIme + travelTimeStartPointToPoint)
            pointExitTime = roundUpTime(pointEnterTime + visitingTimeOfPoint)

            pointEnterTimeBasedOnOpeningHour = getEnterTimeBasedOnOpeningHour(point, pointEnterTime, pointExitTime, weekDay)

            if pointEnterTimeBasedOnOpeningHour < 0:
                continue
            else:
                pointEnterTime = roundUpTime(pointEnterTimeBasedOnOpeningHour)
                pointExitTime = roundUpTime(pointEnterTime + visitingTimeOfPoint)

            if pointExitTime + travelTimePointToEndPoint <= endPointEnterTime:
                visitedListForPoint = visitedPoints.copy()
                visitedListForPoint[pointName] = 1

                sequenceForPoint = currentSequence[:]
                pointInSeqFormat = {'point': point, 'enterTime': pointEnterTime, 'exitTime': pointExitTime}
                sequenceForPoint.append(pointInSeqFormat)

                possibleSequencesBWStartAndEndPoint(listOfPoints=listOfPoints, visitedPoints=visitedListForPoint, startPoint=point,
                                                    startPointExitTIme=pointExitTime, endPoint=endPoint,endPointEnterTime=endPointEnterTime,
                                                    endPointExitTime=endPointExitTime, currentSequence=sequenceForPoint, weekDay=weekDay,
                                                    possibleSequences=possibleSequences)


# it will add only endpoint always and other point before endpoint only when possible
# end point is marked true in visitedPoints before calling this function
def possibleSequencesBWStartTimeAndEndPoint(listOfPoints, visitedPoints, currentSequence, endPoint,
                                            endPointEnterTime, endPointExitTime, startTime, weekDay):
    possibleSequences = []
    for index, startPoint in enumerate(listOfPoints):
        pointName = startPoint['pointName']
        if pointName not in visitedPoints:
            visitingTimeOfPoint = roundUpTime(float(startPoint['recommendedNumHours']))
            travelTimeToEndPoint = getTravelTime(startPoint, endPoint)

            pointEnterTime = roundUpTime(startTime)
            pointExitTime = roundUpTime(pointEnterTime + visitingTimeOfPoint)

            pointEnterTimeBasedOnOpeningHour = getEnterTimeBasedOnOpeningHour(startPoint, pointEnterTime, pointExitTime, weekDay)
            if pointEnterTimeBasedOnOpeningHour < 0:
                continue
            else:
                pointEnterTime = roundUpTime(pointEnterTimeBasedOnOpeningHour)
                pointExitTime = roundUpTime(pointEnterTime + visitingTimeOfPoint)

            if pointExitTime + travelTimeToEndPoint <= endPointEnterTime:
                visitedListForPoint = visitedPoints.copy()
                visitedListForPoint[pointName] = 1

                sequenceForPoint = currentSequence[:]

                pointInSeqFormat = {'point': startPoint, 'enterTime': pointEnterTime, 'exitTime': pointExitTime}
                sequenceForPoint.append(pointInSeqFormat)
                # this will add all possible sequence which end with endPoint and have some points in starting
                possibleSequencesBWStartAndEndPoint(listOfPoints=listOfPoints, visitedPoints=visitedListForPoint, startPoint=startPoint,
                                                    startPointExitTIme=pointExitTime, endPoint=endPoint, endPointEnterTime=endPointEnterTime,
                                                    endPointExitTime=endPointExitTime, currentSequence=sequenceForPoint, weekDay=weekDay,
                                                    possibleSequences=possibleSequences)

    # we also need to add only endPoint no any other points
    pointInSeqFormat = {'point': endPoint, 'enterTime': endPointEnterTime, 'exitTime': endPointExitTime}
    sequenceForOnlyEndPoint = [pointInSeqFormat]
    possibleSequences.append(sequenceForOnlyEndPoint)

    return possibleSequences


def getDayItinerary(listOfPoints, mustVisitPoints, mustVisitPlaceEnterExitTime, dayStartTime,
                    dayEndTime, weekDay, pFactor):
    possibleSequences = []
    visitedPoints = {}
    if len(mustVisitPoints) == 0:
        # we can choose any start point
        for index, startPoint in enumerate(listOfPoints):
            pointName = startPoint['pointName']
            startPointEnterTime = roundUpTime(dayStartTime)
            startPointVisitingTime = roundUpTime(float(startPoint['recommendedNumHours']))
            startPointExitTime = roundUpTime(startPointEnterTime + startPointVisitingTime)

            pointEnterTimeBasedOnOpeningHour = getEnterTimeBasedOnOpeningHour(startPoint, startPointEnterTime, startPointExitTime, weekDay)

            if pointEnterTimeBasedOnOpeningHour < 0:
                continue
            else:
                startPointEnterTime = roundUpTime(pointEnterTimeBasedOnOpeningHour)
                startPointExitTime = roundUpTime(startPointEnterTime + startPointVisitingTime)

            if startPointExitTime <= dayEndTime:
                visitedPointsForStartPoint = visitedPoints.copy()
                visitedPointsForStartPoint[pointName] = 1

                currentSequence = [{'point': startPoint, 'enterTime': startPointEnterTime, 'exitTime': startPointExitTime}]

                possibleSequencesBWStartPointAndEndTime(listOfPoints=listOfPoints, visitedPoints=visitedPointsForStartPoint,
                                                        startPoint=startPoint, currentSequence=currentSequence, startPointExitTime=startPointExitTime,
                                                        endTime=dayEndTime, weekDay=weekDay, possibleSequences=possibleSequences)
    else:
        # points can be added before first must visit point, if it is not possible to add points before first must visit point this function will add only
        # first must visit point in possibleSequences
        firstPointEnterTime = mustVisitPlaceEnterExitTime[0][0]
        firstPointExitTime = mustVisitPlaceEnterExitTime[0][1]
        endPoint = mustVisitPoints[0]
        possibleSequences = possibleSequencesBWStartTimeAndEndPoint(listOfPoints=listOfPoints, visitedPoints=visitedPoints, currentSequence=[],
                                                                    endPoint=endPoint, endPointEnterTime=firstPointEnterTime, endPointExitTime=firstPointExitTime,
                                                                   startTime=dayStartTime, weekDay=weekDay)

        for index, startPoint in enumerate(mustVisitPoints):
            startPointExitTime = mustVisitPlaceEnterExitTime[index][1]  # end Time will be now start time for sequence
            possibleSequencesAfterIter = []  # each iteration of loop will create new possible sequence based on previous iteration possibleSequences
            if index < len(mustVisitPoints) - 1:  # for this we have start point and end point always
                for sequence in possibleSequences:
                    visitedPointsForSeq = visitedPoints.copy()

                    for seqData in sequence:
                        visitedPointsForSeq[seqData['point']['pointName']] = 1

                    endPoint = mustVisitPoints[index + 1]
                    endPointEnterTime = mustVisitPlaceEnterExitTime[index + 1][0]
                    endPointExitTime = mustVisitPlaceEnterExitTime[index + 1][1]

                    possibleSequencesBWStartAndEndPoint(listOfPoints=listOfPoints, visitedPoints=visitedPointsForSeq, startPoint=startPoint,
                                                        startPointExitTIme=startPointExitTime, endPoint=endPoint, endPointEnterTime=endPointEnterTime,
                                                        endPointExitTime=endPointExitTime, currentSequence=sequence, weekDay=weekDay,
                                                        possibleSequences=possibleSequencesAfterIter)

            else:
                for sequence in possibleSequences:
                    visitedPointsForSeq = visitedPoints.copy()

                    for seqData in sequence:
                        visitedPointsForSeq[seqData['point']['pointName']] = 1

                    possibleSequencesBWStartPointAndEndTime(listOfPoints=listOfPoints, visitedPoints=visitedPointsForSeq,
                                                            startPoint=startPoint, currentSequence=sequence, startPointExitTime=startPointExitTime,
                                                            endTime=dayEndTime, weekDay=weekDay, possibleSequences=possibleSequencesAfterIter)

            possibleSequences = possibleSequencesAfterIter[:]

    bestSequence = getBestSequence(possibleSequences, pFactor)

    # for sequence in possibleSequences:
    #     print('gScore: ', gratificationScoreOfSequence([seqData['point'] for seqData in sequence], pFactor))
    #     for seqData in sequence:
    #         print(seqData['point']['pointName'])
    #     print()
    return bestSequence


def printSequence(sequence, dayStartTime, GScore, weekDay):
    print("Sequence: Gscore: " + str(GScore))
    print("dayStartTime: " + str(dayStartTime))
    previousPoint = None
    for index, seqData in enumerate(sequence):
        print(str(index) + "\t" + seqData['point']['pointName'] + "\tEnterTime: " + str(
            seqData['enterTime']) + "\t" + "ExitTime: " + str(seqData['exitTime']) +
              "\tOpenHour: " + seqData['point']['openingHour'].split(',')[weekDay] + "\tCloseHour: " +
              seqData['point']['closingHour'].split(',')[weekDay])

        visitingTime = seqData['point']['recommendedNumHours']
        print("visitingTime: " + visitingTime)

        if index >= 1:
            distance = getDistance(seqData['point'], previousPoint)
            print("distance: " + str(distance))
            travelTime = getTravelTime(seqData['point'], previousPoint)
            print("travelling Time: " + str(travelTime) + " hour")

        previousPoint = seqData['point']
        print('\n')


if __name__ == '__main__':
    allData = readAllData('../aggregatedData/latest/data.json')
    countryName = "United Arab Emirates"
    cityName = 'Dubai'

    cityTopPoints = getTopPointsOfCity(allData, countryName, cityName)

    cityTopPointsWithLatlng = []
    for point in cityTopPoints:
        if point['coordinates'] is not None:
            cityTopPointsWithLatlng.append(point)


    numPoints=8
    listOfPoints = cityTopPointsWithLatlng[:numPoints]

    print("points: ")
    for index, point in enumerate(listOfPoints):
        print(str(index) + "\t" + point['pointName']+"\tcoordinates"+point['coordinates'] + "\t" + point['recommendedNumHours'] + "\t" + point['openingHour'] + "\t"+point['closingHour'])

    dayStartTime = 9
    dayEndTime = 20
    weekDay = 1
    mustVisitPoints = []#[listOfPoints[0], listOfPoints[2]]  # , listOfPoints[3], listOfPoints[4]]

    mustVisitPointsTime = [[13, 14], [17, 18]]  # , [16.5, 17.5], [21, 22]]

    mustNotVisitPoints = []#[listOfPoints[1]]

    print("\nMust Visit Points: ")
    for index, point in enumerate(mustVisitPoints):
        print(point['pointName'])
        print(mustVisitPointsTime[index])
        listOfPoints.remove(point)

    print("\nmust not visit points:")
    for index, point in enumerate(mustNotVisitPoints):
        print(point['pointName'])

    print('\n\n')

    for point in mustNotVisitPoints:
        listOfPoints.remove(point)

    startTime = time.time()
    bestSequence, maxGScore = getDayItinerary(listOfPoints, mustVisitPoints, mustVisitPointsTime,
                                              dayStartTime, dayEndTime, weekDay, pFactor = 'less')
    endTime = time.time()

    print('timeTaken: ', endTime-startTime)
    printSequence(bestSequence, dayStartTime, maxGScore, weekDay)