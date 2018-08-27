import json
import sys
import random
from math import radians, sin, cos, atan2, sqrt
import re
from collections import defaultdict
from sklearn.cluster import KMeans
import numpy as np

sys.path.append('.')
from utilities import getWilsonScore



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


#to convert time in only hours for example 2h 30 min => 2.5
def getRecommendedNumHoursInHour(point):
    if point['recommendedNumHours'] is None:
        return 2 #consider 2 hour for visiting point
    else:
        result = 0
        timeString = point['recommendedNumHours'].strip().lower()

        hourRegex = re.compile('^([0-9]+)(h|h | hours| hour)+')

        hour = hourRegex.findall(timeString)
        if len(hour) > 0:
            result += int(hour[0][0])

        minutesRegex = re.compile('([0-9]+) min')
        minutes = minutesRegex.findall(timeString)

        if len(minutes) > 0:
            result += int(minutes[0])/60.0
        return result

#convert time in 24 hour format
def formatTime(timeString):
    if timeString == 'closed':
        return '$'

    amFormatData = timeString.split('am')

    if len(amFormatData) == 2:
        hourAndMinutes = amFormatData[0].split(':')
        hour = int(hourAndMinutes[0])
        minutes = 0
        if len(hourAndMinutes) == 2:
            minutes = int(hourAndMinutes[1])

        if hour == 12:
            result = minutes/60.0
        else:
            result = hour + minutes/60.0

        return result
    pmFormatData = timeString.split('pm')

    if len(pmFormatData) == 2:
        hourAndMinutes = pmFormatData[0].split(':')
        hour = int(hourAndMinutes[0])
        minutes = 0
        if len(hourAndMinutes) == 2:
            minutes = int(hourAndMinutes[1])

        if hour == 12:
            result = hour + minutes/60.0
        else:
            result = 12 + hour + minutes/60.0

        return result

def preprocessPoints(listOfPoints):
    for index, point in enumerate(listOfPoints):
        hours = getRecommendedNumHoursInHour(point)
        point['recommendedNumHours'] = str(hours)
        point['rank'] = index + 1

        #convert opening closing in 0-24 format

        formatedOpeningHour = ''
        formatedClosingHour = ''
        if point['openingHour'] is not None:
            openingHourDayWiseData = point['openingHour'].split(',')
            closingHourDayWiseData = point['closingHour'].split(',')

            for openTime in openingHourDayWiseData:
                formatedOpeningHour += str(formatTime(openTime.lower())) + ","

            for closeTime in closingHourDayWiseData:
                formatedClosingHour += str(formatTime(closeTime.lower())) + ","

        else: #if opening closing not given consider 8:00 AM to 6:00 PM
            openTime = '8:00 am'
            closeTime = '6:00 pm'
            for i in range(7):
                formatedOpeningHour += str(formatTime(openTime.lower())) + ","
                formatedClosingHour += str(formatTime(closeTime.lower())) + ","

        point['openingHour'] = formatedOpeningHour[:-1]
        point['closingHour'] = formatedClosingHour[:-1]
        listOfPoints[index] = point
    return listOfPoints


# consider sunday as day 0
def canVisitedPoint(point, enterTime, exitTime, dayNum):

    openHourOfDay = float(point['openingHour'].split(',')[dayNum])

    closeHourOfDay = float(point['closingHour'].split(',')[dayNum])

    if enterTime >= openHourOfDay and exitTime <= closeHourOfDay:
        return True
    else:
        return False


def getDistance(point1, point2):
    #approximate radius of earth in km
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

    return distance

def getTravelTime(point1, point2):
    distance = getDistance(point1, point2)
    return distance/80 #assumed avg speed 80km/hr


def gratificationScoreOfSeq(sequenceOfPoints, totalTime):
    gScore = 0
    for index, seqData in enumerate(sequenceOfPoints):
        gScore += getWilsonScore(seqData['point']['avgRating']/10, seqData['point']['ratingCount'])*10 #normalize between 0-10
        gScore -= seqData['point']['rank']/5   # normalize between 0-10
        if index < len(sequenceOfPoints)-1:
            travelTime = getTravelTime(seqData['point'], sequenceOfPoints[index+1]['point'])
            gScore -= (travelTime/totalTime)*10 #noramlize between 0-10

    # want more number of attraction
    gScore += len(sequenceOfPoints)
    return gScore

def getBestSequence(sequences, totalTime):
    maxGScore = -float('inf')
    maxGScoreSequence = []
    for sequence in sequences:
        gScore = gratificationScoreOfSeq(sequence, totalTime)
        #print("gscore: "+ str(gScore))
        if gScore > maxGScore:
            maxGScore = gScore
            maxGScoreSequence = sequence

    return maxGScoreSequence, maxGScore




def getDayWiseClusteredListOfPoints(pointsOfCity, numDays: int):
    dayWiseClusteredData = defaultdict(list)
    latLngToPoint = defaultdict()
    coordinates = []
    for point in pointsOfCity:
        if point['coordinates'] is not None:
            [lat, lng] = point['coordinates'].split(',')
        else:
            lat = random.uniform(51, 51.5) # london lat range
            lng = random.uniform(-0.2, 0.2) # london lng range
        coordinates.append([lat, lng])

        key = str(lat) + ", " + str(lng)
        point['coordinates'] = key
        latLngToPoint[key] = point

    coordinatesInArrayFormat = np.array(coordinates)
    kMeans = KMeans(n_clusters=numDays, max_iter=500).fit(coordinatesInArrayFormat)

    predictedClusters = kMeans.predict(coordinatesInArrayFormat)

    for index, value in enumerate(coordinates):
        [lat, lng] = value
        key = str(lat) + ", " + str(lng)
        dayWiseClusteredData[predictedClusters[index]].append(latLngToPoint[key])

    return dayWiseClusteredData

# assume start point is already added in currentSequence
def possibleSequencesBWStartPointAndEndTime(listOfPoints, visitedPoints, startPoint, currentSequence, startPointExitTIme, endTime, possibleSequences):
    possibleSequences.append(currentSequence)
    for index, point in enumerate(listOfPoints):
        if not visitedPoints[index]:
            travelTime = getTravelTime(startPoint, point)
            visitingTime = float(point['recommendedNumHours'])
            pointEnterTime = startPointExitTIme + travelTime
            pointExitTime = startPointExitTIme + travelTime + visitingTime

            if pointExitTime < endTime:


                newVisitedList = visitedPoints[:]
                newVisitedList[index] = True
                newSequence = currentSequence[:]
                pointInSeqFormat = {'point': point, 'enterTime': pointEnterTime, 'exitTime': pointExitTime }
                newSequence.append(pointInSeqFormat)

                newStartPointEndTime = startPointExitTIme + travelTime + visitingTime
                possibleSequencesBWStartPointAndEndTime(listOfPoints, newVisitedList, point, newSequence, newStartPointEndTime, endTime, possibleSequences)


# assume start point is already is added in currentSequence
def possibleSequencesBWStartAndEndPoint(listOfPoints, visitedPoints, startPoint, startPointExitTIme, endPoint, endPointEnterTime, endPointExitTime, currentSequence, possibleSequences):
    #case 1
    newSequence = currentSequence[:]
    endPointInSeqFormat = {'point': endPoint, 'enterTime': endPointEnterTime, 'exitTime': endPointExitTime}
    newSequence.append(endPointInSeqFormat)
    possibleSequences.append(newSequence)

    #case 2
    for index, point in enumerate(listOfPoints):
        if not visitedPoints[index]:
            travelTimeStartPointToPoint = getTravelTime(startPoint, point)
            visitingTimeOfPoint = float(point['recommendedNumHours'])
            travelTimePointToEndPoint = getTravelTime(point, endPoint)

            pointEnterTime = startPointExitTIme + travelTimeStartPointToPoint
            pointExitTime = pointEnterTime + visitingTimeOfPoint

            if pointExitTime + travelTimePointToEndPoint < endPointEnterTime:
                newVisitedList = visitedPoints[:]
                newVisitedList[index] = True

                newSequence = currentSequence[:]
                pointInSeqFormat = {'point': point, 'enterTime': pointEnterTime, 'exitTime': pointExitTime}
                newSequence.append(pointInSeqFormat)

                endTimeOfPoint = startPointExitTIme + travelTimeStartPointToPoint + visitingTimeOfPoint
                possibleSequencesBWStartAndEndPoint(listOfPoints, newVisitedList, point, endTimeOfPoint, endPoint, endPointEnterTime,endPointExitTime, newSequence, possibleSequences)


# it will add only endpoint always and other point only when possible
def possibleSequencesBWStartTimeAndEndPoint(listofPoints, visitedPoints, currentSequence, endPoint, startTime, endPointEnterTime, endPointExitTime):

    possibleSequences = []
    for index, startPoint in enumerate(listOfPoints):
        if not visitedPoints[index]:
            visitingTimeOfPoint = float(startPoint['recommendedNumHours'])
            travelTimeToEndPoint = getTravelTime(startPoint, endPoint)

            if startTime + visitingTimeOfPoint + travelTimeToEndPoint < endPointEnterTime:

                newVisitedList = visitedPoints[:]
                newVisitedList[index] = True

                startPointExitTime = startTime + visitingTimeOfPoint

                newSequence = currentSequence[:]

                pointInSeqFormat = {'point': startPoint, 'enterTime': startTime, 'exitTime': startPointExitTime}
                newSequence.append(pointInSeqFormat)
                # this will add all possible sequence which end with endPoint and have some points in starting
                possibleSequencesBWStartAndEndPoint(listOfPoints, newVisitedList, startPoint, startPointExitTime, endPoint, endPointEnterTime, endPointExitTime, newSequence, possibleSequences)

    #we also need to add only endPoint no any other points

    pointInSeqFormat = {'point': endPoint, 'enterTime': endPointEnterTime, 'exitTime': endPointExitTime}
    possibleSequences.append([pointInSeqFormat])

    return possibleSequences




def getDayItinerary(listofPoints, mustVisitPoints, mustVisitPlaceEnterExitTime, mustNotVisitPoints, dayStartTime, dayEndTime):

    possibleSequences = []
    visitedPoints = [False] * len(listOfPoints)

    for notVisitPoint in mustNotVisitPoints:
        visitedPoints[listOfPoints.index(notVisitPoint)] = True

    if len(mustVisitPoints) == 0:
        # we can choose any start point
        for index, startPoint in enumerate(listOfPoints):
            startPointExitTime = dayStartTime + float(startPoint['recommendedNumHours'])

            visitedPointForStartPoint = visitedPoints[:]
            visitedPointForStartPoint[index] = True

            currentSequence = [{'point': startPoint, 'enterTime': dayStartTime, 'exitTime': startPointExitTime}]

            possibleSequencesBWStartPointAndEndTime(listOfPoints, visitedPointForStartPoint, startPoint, currentSequence, startPointExitTime, dayEndTime, possibleSequences)

    else:
        for mustVisitPoint in mustVisitPoints:
            visitedPoints[listOfPoints.index(mustVisitPoint)] = True

        #we can also add point before must visit first point if we can't then this function will add first point in sequence
        firstPointEnterTime = mustVisitPlaceEnterExitTime[0][0]
        firstPointExitTime = mustVisitPlaceEnterExitTime[0][1]
        possibleSequences = possibleSequencesBWStartTimeAndEndPoint(listOfPoints, visitedPoints,[], mustVisitPoints[0], dayStartTime, firstPointEnterTime, firstPointExitTime)


        for index, startPoint in enumerate(mustVisitPoints):
            startPointExitTime = mustVisitPlaceEnterExitTime[index][1] #end Time will be now start time for sequence


            possibleSequencesAfterIter = [] # each iteration of loop will create new possible sequence based on previous iteration possibleSequences
            if index < len(mustVisitPoints)-1: # for this we have start point and end point always
                for sequence in possibleSequences:
                    visitedPointsForSeq = visitedPoints[:]

                    for seqPointData in sequence:
                        visitedPointsForSeq[listOfPoints.index(seqPointData['point'])] = True

                    endPoint = mustVisitPoints[index+1]
                    endPointEnterTime = mustVisitPlaceEnterExitTime[index+1][0]
                    endPointExitTime = mustVisitPlaceEnterExitTime[index+1][1]

                    possibleSequencesBWStartAndEndPoint(listOfPoints, visitedPointsForSeq, startPoint, startPointExitTime, endPoint, endPointEnterTime, endPointExitTime, sequence, possibleSequencesAfterIter)

            else:
                for sequence in possibleSequences:
                    visitedPointsForSeq = visitedPoints[:]

                    for seqPointData in sequence:
                        visitedPointsForSeq[listOfPoints.index(seqPointData['point'])] = True

                    possibleSequencesBWStartPointAndEndTime(listOfPoints, visitedPointsForSeq, startPoint, sequence, startPointExitTime, dayEndTime, possibleSequencesAfterIter)


            possibleSequences = possibleSequencesAfterIter[:]

    bestSequence = getBestSequence(possibleSequences, dayEndTime - dayStartTime)

    return bestSequence



def printSequence(sequence, startTime, GScore):
    print("Sequence: Gscore: " + str(GScore))
    print("startTime: " + str(startTime))
    previousPoint = []
    for index, seqData in enumerate(sequence):
        print(str(index) + "\t" + seqData['point']['pointName'] + "\tEnterTime: "+str(seqData['enterTime'])+"\t" +"ExitTime: "+str(seqData['exitTime']))

        visitingTime = float(seqData['point']['recommendedNumHours'])
        print("visitingTime: " + str(visitingTime))

        endTime = startTime + visitingTime
        if index >= 1:
            distance = getDistance(seqData['point'], previousPoint)
            print("distance: " + str(distance))
            travelTime = getTravelTime(seqData['point'], previousPoint)
            print("travelling Time: " + str(travelTime))
            endTime += travelTime
        print("endTime: " + str(endTime))

        previousPoint = seqData['point']
        startTime = endTime
        print('\n\n')



allData = readAllData('aggregatedDatafrequencyWithWDomainRanking.json')

countryName = "United Kingdom"
cityName = 'London'

cityTopPoints = getTopPointsOfCity(allData, countryName, cityName)

dayWiseClusteredData = getDayWiseClusteredListOfPoints(cityTopPoints, 5)



# for day in dayWiseClusteredData:
#     listOfPoints = dayWiseClusteredData[day]
#     print(day)
#     for point in listOfPoints:
#         print(point['pointName'])
#         print(point['recommendedNumHours'])
#         print(getRecommendedNumHoursInMinutes(point))
#     print('\n\n')
numPoints = 10
listOfPoints = cityTopPoints[:numPoints]


listOfPoints = preprocessPoints(listOfPoints)

startTime = 10
endTime = 22
mustVisitPoints = [listOfPoints[0], listOfPoints[2], listOfPoints[3], listOfPoints[4]]

mustVisitPointsTime = [[10, 11], [13, 14], [16, 17], [21, 22]]

mustNotVisitPoints = [listOfPoints[5], listOfPoints[9]]

#mustNotVisitPoints = [listOfPoints[2]]
print("\nMust Visit Points: ")
for index, point in enumerate(mustVisitPoints):
    print(point['pointName'])
    print(mustVisitPointsTime[index])


print("\nmust not visit points:")
for index, point in enumerate(mustNotVisitPoints):
    print(point['pointName'])

print('\n\n')
bestSequence, maxGScore = getDayItinerary(listOfPoints, mustVisitPoints, mustVisitPointsTime, mustNotVisitPoints, startTime, endTime)
printSequence(bestSequence, startTime, maxGScore)

