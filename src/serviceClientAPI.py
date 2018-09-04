from typing import List
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import json
import time
import datetime
from functools import lru_cache

from utilities import urlDecode
from itineraryPlanner import getDayItinerary
from tunable import clientDefaultCity, clientDefaultTripLength, clientDefaultEndTime, clientDefaultStartTime, clientMaxPossiblePointsPerDay
from clustering import getBestPoints

clientAPI = Blueprint('clientAPI', __name__)


def loadData():
    with open('../aggregatedData/latest/data.json', 'r') as f:
        countries = json.loads(f.read())

    cities = {city['fullName']: city
              for country in countries.values()
              for city in country['cities'].values()}

    citiesNoPoints = {}
    for cityIdentifier, city in cities.items():
        citiesNoPoints[cityIdentifier] = {}
        for attrib, value in city.items():
            if attrib == 'points': continue
            if attrib == 'sources': continue
            if attrib == 'pointsOrder': continue
            citiesNoPoints[cityIdentifier][attrib] = value

    return countries, cities, citiesNoPoints


countries, cities, citiesNoPoints = loadData()


def getTopPointsOfCity(city, amount=10):
    if isinstance(city, (str,)):
        city = cities[city]
    topnames = city['pointsOrder'][:amount]
    return {
        'points': {fullName: city['points'][fullName] for fullName in topnames},
        'pointsOrder': topnames
    }


recentPlans = [
    # {'city': 'United Kingdom/London', 'duration': '48'},
    # {'city': 'India/Agra', 'duration': '168'},
    # {'city': 'India/New Delhi', 'duration': '72'},
    # {'city': 'Singapore/Singapore', 'duration': '6'}
]


@clientAPI.route('/api/cities')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def getCities():
    return jsonify(citiesNoPoints)


@clientAPI.route('/api/points')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def getAttractions():
    cityName = request.args.get('city', None)
    amount = int(request.args.get('amount', 100))
    if cityName:
        cityName = urlDecode(cityName)
        return jsonify(getTopPointsOfCity(cityName, amount))
    return 'invalid city'


def getTodaysLikes(mustVisit, page):
    todaysLikes = mustVisit[page-1][1]  # mustVisit is 0-indexed. day is 1-indexed
    return [item[2] for item in todaysLikes], [item[:2] for item in todaysLikes]


def getNumDays(startDate, endDate):
    start = datetime.datetime(*list(map(int, startDate.strip().split('/'))))
    end = datetime.datetime(*list(map(int, endDate.strip().split('/'))))
    return (end - start).days + 1


@lru_cache(None)
def __getItinerary(cityName: str, likes, mustVisit, dislikes, startDate, endDate, startDayTime, endDayTime, page):
    numDays = getNumDays(startDate, endDate)

    if not (0 < page <= numDays):
        return {'itinerary': [], 'score': -1, 'nextPage': False, 'currentPage': 1}

    pointMap = getTopPointsOfCity(cityName, 100)['points']

    points = pointMap.values()
    # Remove points for which we don't have coordinates
    points = [point for point in points if point['coordinates'] != None][:50]

    # Remove dislikes
    points = [point for point in points if point['pointName'] not in set(dislikes)]

    # Remove points for which we were already shown in the previous pages
    for oldpage in range(page-1, 0, -1):
        prevItinerary = _getItinerary(
            cityName=cityName,
            likes=likes,
            mustVisit=mustVisit,
            dislikes=dislikes,
            startDate=startDate,
            endDate=endDate,
            startDayTime=startDayTime,
            endDayTime=endDayTime,
            page=oldpage)['itinerary']
        prevItineraryPoints = set([item['point']['pointName'] for item in prevItinerary])
        points = [point for point in points if point['pointName'] not in prevItineraryPoints]

    todaysLikes, todaysLikesTimings = getTodaysLikes(mustVisit, page)

    print('Page:', page)
    print('Todays likes:', todaysLikes)
    print('Todays Like Timings:', todaysLikesTimings)

    # For clustering, remove points that I must visit
    clusteringPoints = [point for point in points if point['pointName'] not in set(likes)]

    if not clusteringPoints:
        return {'itinerary': [{
            'point': {
                'pointName': '__newday__'
            },
            'dayNum': page,
            'date': '(╯°□°）╯︵ ┻━┻ No data'
        }], 'score': -1, 'nextPage': False, 'currentPage': 1}

    todaysPoints = getBestPoints(listOfPoints=clusteringPoints,
                                 allSelectedPoints=[],
                                 numDays=numDays,
                                 numPoints=clientMaxPossiblePointsPerDay - len(todaysLikes))

    start = datetime.datetime(*list(map(int, startDate.strip().split('/'))))
    today = start + datetime.timedelta(days=page-1)
    print('Today Date:', today)

    itinerary, score = getDayItinerary(listOfPoints=todaysPoints,
                                       mustVisitPoints=[pointMap[like] for like in todaysLikes],
                                       mustVisitPlaceEnterExitTime=todaysLikesTimings,
                                       dayStartTime=(startDayTime if page == 1 else clientDefaultStartTime),
                                       dayEndTime=(endDayTime if page == numDays else clientDefaultEndTime),
                                       weekDay=(today.weekday() + 1) % 7)

    datePoint = {
        'point': {
            'pointName': '__newday__'
        },
        'dayNum': page,
        'date': today.strftime('%A/ %d %B /%y')
    }

    # Add dayNum to each visit of the itinerary
    for visit in itinerary:
        visit['dayNum'] = page

    return {
        'itinerary': [datePoint] + itinerary,
        'score': score,
        'nextPage': (page + 1 if page < numDays else False),
        'currentPage': page
    }


def _getItinerary(cityName, likes, mustVisit, dislikes, startDate, endDate, startDayTime, endDayTime, page):
    print('_getItinerary(', cityName, mustVisit, dislikes, startDate, endDate, startDayTime, endDayTime, page, ')')
    result = __getItinerary(cityName=cityName,
                            likes=tuple(likes),
                            mustVisit=tuple(mustVisit),
                            dislikes=tuple(dislikes),
                            startDate=startDate,
                            endDate=endDate,
                            startDayTime=startDayTime,
                            endDayTime=endDayTime,
                            page=page)
    print('Response from _getItinerary():', len(result['itinerary']), result['score'], result['nextPage'], result['currentPage'])
    return result


@clientAPI.route('/api/itinerary')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def getItinerary():
    tstart = time.time()

    cityName = clientDefaultCity
    cityName = request.args.get('city', cityName)
    if cityName:
        cityName = urlDecode(cityName)

    strFormat = '%y/%m/%d'
    startDate = datetime.datetime.now().strftime(strFormat)
    endDate = (datetime.datetime.now() + datetime.timedelta(days=clientDefaultTripLength-1)).strftime(strFormat)
    startDayTime, endDayTime = clientDefaultStartTime, clientDefaultEndTime

    startDate = request.args.get('startDate', startDate)
    endDate = request.args.get('endDate', endDate)
    startDayTime = float(request.args.get('startDayTime', startDayTime))
    endDayTime = float(request.args.get('endDayTime', endDayTime))

    numDays = getNumDays(startDate, endDate)

    likes = request.args.get('likes', [])
    likesTimings = request.args.get('likesTimings', [])
    mustVisit = {dayNum: [] for dayNum in range(1, numDays + 1)}

    if likes and likesTimings:
        likes = list(map(urlDecode, likes.split('|')))
        likesTimings = list(map(urlDecode, likesTimings.split('|')))

        for pointName, timing in zip(likes, likesTimings):
            dayNum, enterTime, exitTime = map(float, timing.split('-'))
            mustVisit[dayNum].append((enterTime, exitTime, pointName))
        for dayNum in mustVisit:
            mustVisit[dayNum] = list(sorted(mustVisit[dayNum]))

    tupleMustVisit = []
    for dayNum in range(1, numDays + 1):
        tupleMustVisit.append((dayNum, tuple(map(tuple, mustVisit[dayNum]))))

    print('Processed MustVisit:', mustVisit)

    dislikes = request.args.get('dislikes', [])
    if dislikes:
        dislikes = list(map(urlDecode, dislikes.split('|')))

    print('Processed User Timings:', startDayTime, endDayTime)
    # input()
    page = int(request.args.get('page', '1'))

    itinerary = _getItinerary(cityName=cityName,
                              likes=likes,
                              mustVisit=tupleMustVisit,
                              dislikes=dislikes,
                              startDate=startDate,
                              endDate=endDate,
                              startDayTime=startDayTime,
                              endDayTime=endDayTime,
                              page=page)

    mustVisitItinerary = []
    start = datetime.datetime(*list(map(int, startDate.strip().split('/'))))
    pointMap = getTopPointsOfCity(cityName, 100)['points']
    for dayNum in range(1, numDays + 1):
        today = start + datetime.timedelta(days=dayNum-1)
        datePoint = {
            'point': {
                'pointName': '__newday__'
            },
            'dayNum': dayNum,
            'date': today.strftime('%A/ %d %B /%y')
        }
        mustVisitItinerary.append(datePoint)
        for enterTime, exitTime, pointName in mustVisit[dayNum]:
            visit = {
                'point': pointMap[pointName],
                'dayNum': dayNum,
                'enterTime': enterTime,
                'exitTime': exitTime
            }
            mustVisitItinerary.append(visit)


    tend = time.time()
    print('Time for request:', tend - tstart)
    result = {
        'itinerary': itinerary,
        'mustVisit': mustVisitItinerary,
        'mustNotVisit': dislikes
    }
    print(result)
    result = json.loads(json.dumps(result))
    print(result)
    return jsonify(result)


@clientAPI.route('/api/recent-plans')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def getRecentPlans():
    return jsonify(recentPlans)
