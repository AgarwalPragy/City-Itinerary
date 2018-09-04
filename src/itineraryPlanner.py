import json
import sys
from math import radians, sin, cos, atan2, sqrt
sys.path.append('.')
from utilities import roundUpTime
from tunable import avgSpeedOfTravel
import time

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

    return distance * 1.7 # to make approximate same as path distance


def getTravelTime(point1, point2):
    distance = getDistance(point1, point2)
    return roundUpTime(distance/avgSpeedOfTravel)  # assumed avg speed 40km/hr


def getBestSequence(sequences):
    maxGScore = -float('inf')
    maxGScoreSequence = []
    print('Number of sequences to check for gratification:', len(sequences))
    for sequence in sequences:
        gScore = gratificationScoreOfSequence([seqData['point'] for seqData in sequence])
        if gScore > maxGScore:
            maxGScore = gScore
            maxGScoreSequence = sequence

    return maxGScoreSequence, maxGScore

# assume start point is already added in currentSequence and marked true in visitedPoints
def possibleSequencesBWStartPointAndEndTime(listOfPoints, visitedPoints, startPoint, currentSequence,
                                            startPointExitTime, endTime, weekDay, possibleSequences):
    possibleSequences.append(currentSequence)
    for index, point in enumerate(listOfPoints):
        if not visitedPoints[index]:
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
                visitedListForPoint = visitedPoints[:]
                visitedListForPoint[index] = True

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
        if not visitedPoints[index]:
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
                visitedListForPoint = visitedPoints[:]
                visitedListForPoint[index] = True

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
        if not visitedPoints[index]:
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
                visitedListForPoint = visitedPoints[:]
                visitedListForPoint[index] = True

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
                    dayEndTime, weekDay):
    possibleSequences = []
    visitedPoints = [False] * len(listOfPoints)
    if len(mustVisitPoints) == 0:
        # we can choose any start point
        for index, startPoint in enumerate(listOfPoints):
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
                visitedPointsForStartPoint = visitedPoints[:]
                visitedPointsForStartPoint[index] = True

                currentSequence = [{'point': startPoint, 'enterTime': startPointEnterTime, 'exitTime': startPointExitTime}]

                possibleSequencesBWStartPointAndEndTime(listOfPoints=listOfPoints, visitedPoints=visitedPointsForStartPoint,
                                                        startPoint=startPoint, currentSequence=currentSequence, startPointExitTime=startPointExitTime,
                                                        endTime=dayEndTime, weekDay=weekDay, possibleSequences=possibleSequences)
    else:
        for mustVisitPoint in mustVisitPoints:
            if mustVisitPoint in listOfPoints:
                visitedPoints[listOfPoints.index(mustVisitPoint)] = True
        #points can be added before first must visit point, if it is not possible to add points before first must visit point this function will add only
        #first must visit point in possibleSequences
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
                    visitedPointsForSeq = visitedPoints[:]

                    for seqData in sequence:
                        visitedPointsForSeq[listOfPoints.index(seqData['point'])] = True

                    endPoint = mustVisitPoints[index + 1]
                    endPointEnterTime = mustVisitPlaceEnterExitTime[index + 1][0]
                    endPointExitTime = mustVisitPlaceEnterExitTime[index + 1][1]

                    possibleSequencesBWStartAndEndPoint(listOfPoints=listOfPoints, visitedPoints=visitedPointsForSeq, startPoint=startPoint,
                                                        startPointExitTIme=startPointExitTime, endPoint=endPoint, endPointEnterTime=endPointEnterTime,
                                                        endPointExitTime=endPointExitTime, currentSequence=sequence, weekDay=weekDay,
                                                        possibleSequences=possibleSequencesAfterIter)

            else:
                for sequence in possibleSequences:
                    visitedPointsForSeq = visitedPoints[:]

                    for seqData in sequence:
                        visitedPointsForSeq[listOfPoints.index(seqData['point'])] = True

                    possibleSequencesBWStartPointAndEndTime(listOfPoints=listOfPoints, visitedPoints=visitedPointsForSeq,
                                                            startPoint=startPoint, currentSequence=sequence, startPointExitTime=startPointExitTime,
                                                            endTime=dayEndTime, weekDay=weekDay, possibleSequences=possibleSequencesAfterIter)

            possibleSequences = possibleSequencesAfterIter[:]

    bestSequence = getBestSequence(possibleSequences)
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
    countryName = "India"
    cityName = 'Jaipur'

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
    dayEndTime = 22
    weekDay = 0
    mustVisitPoints = [listOfPoints[0], listOfPoints[2]]  # , listOfPoints[3], listOfPoints[4]]

    mustVisitPointsTime = [[13, 14], [17, 18]]  # , [16.5, 17.5], [21, 22]]

    mustNotVisitPoints = []#[listOfPoints[1]]

    print("\nMust Visit Points: ")
    for index, point in enumerate(mustVisitPoints):
        print(point['pointName'])
        print(mustVisitPointsTime[index])

    print("\nmust not visit points:")
    for index, point in enumerate(mustNotVisitPoints):
        print(point['pointName'])

    print('\n\n')

    for point in mustNotVisitPoints:
        listOfPoints.remove(point)

    startTime = time.time()
    bestSequence, maxGScore = getDayItinerary(listOfPoints, mustVisitPoints, mustVisitPointsTime,
                                              dayStartTime, dayEndTime, weekDay)
    endTime = time.time()

    print('timeTaken: ', endTime-startTime)
    printSequence(bestSequence, dayStartTime, maxGScore, weekDay)