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
from clustering import getPointsFromMaxPointsCluster

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
    amount = int(request.args.get('amount', 50))
    if cityName:
        cityName = urlDecode(cityName)
        return jsonify(getTopPointsOfCity(cityName, amount))
    return 'invalid city'


def getTodaysLikes(likes, likesTimings, startDate, page):
    return [], []
    pass


def getNumDays(startDate, endDate):
    start = datetime.datetime(*list(map(int, startDate.strip().split('/'))))
    end = datetime.datetime(*list(map(int, endDate.strip().split('/'))))
    return (end - start).days + 1


@lru_cache(None)
def __getItinerary(cityName: str, likes, likesTimings, dislikes, startDate, endDate, startDayTime, endDayTime, page):
    numDays = getNumDays(startDate, endDate)

    if not (0 < page <= numDays):
        return {'itinerary': [], 'score': -float('inf'), 'nextPage': False, 'currentPage': 0}

    pointMap = getTopPointsOfCity(cityName, 60)['points']

    points = pointMap.values()
    # Remove points for which we don't have coordinates
    points = [point for point in points if point['coordinates'] != None][:50]

    # Remove dislikes
    points = [point for point in points if point['pointName'] not in set(dislikes)]

    # Remove points for which we were already shown in the previous pages
    for oldpage in range(page-1, 0, -1):
        prevItinerary = _getItinerary(cityName, likes, likesTimings, dislikes, startDate, endDate, startDayTime, endDayTime, oldpage)['itinerary']
        prevItineraryPoints = set([item['point']['pointName'] for item in prevItinerary])
        points = [point for point in points if point['pointName'] not in prevItineraryPoints]  # TODO: Fix this

    todaysLikes, todaysLikesTimings = getTodaysLikes(likes, likesTimings, startDate, page)

    # For clustering, remove points that I must visit today
    clusteringPoints = [point for point in points if point['pointName'] not in set(todaysLikes)]

    todaysPoints = getPointsFromMaxPointsCluster(listOfPoints=clusteringPoints,
                                                 numDays=numDays,
                                                 numPoints=clientMaxPossiblePointsPerDay - len(todaysLikes))


    start = datetime.datetime(*list(map(int, startDate.strip().split('/'))))
    today = start + datetime.timedelta(days=page-1)
    print('Today:', today)

    itinerary, score = getDayItinerary(listOfPoints=todaysPoints,
                                mustVisitPoints=[pointMap[like] for like in todaysLikes],
                                mustVisitPlaceEnterExitTime=todaysLikesTimings,
                                mustNotVisitPoints=[],
                                dayStartTime=(startDayTime if page == 0 else clientDefaultStartTime),
                                dayEndTime=(endDayTime if page == numDays else clientDefaultEndTime),
                                weekDay=(today.weekday() + 1) % 7)

    datePoint = {
        'point': {
            'pointName': '__newday__'
        },
        'dayNum': page,
        'date': today.strftime('%A/ %d %B /%y')
    }

    return {
        'itinerary': [datePoint] + itinerary,
        'score': score,
        'nextPage': (page + 1 if page < numDays else False),
        'currentPage': page
    }


def _getItinerary(cityName, likes, likesTimings, dislikes, startDate, endDate, startDayTime, endDayTime, page):
    print(cityName, likes, likesTimings, dislikes, startDate, endDate, startDayTime, endDayTime, page)
    result = __getItinerary(cityName, tuple(likes), tuple(likesTimings), tuple(dislikes), startDate, endDate, startDayTime, endDayTime, page)
    print(len(result['itinerary']), result['score'], result['nextPage'])
    return result




@clientAPI.route('/api/itinerary')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def getItinerary():
    tstart = time.time()

    cityName = clientDefaultCity
    cityName = request.args.get('city', cityName)
    if cityName:
        cityName = urlDecode(cityName)

    likes = request.args.get('likes', [])
    if likes:
        likes = list(map(urlDecode, likes.split('|')))

    likesTimings = request.args.get('likesTimings', [])
    if likesTimings:
        likesTimings = list(map(urlDecode, likesTimings.split('|')))

    dislikes = request.args.get('dislikes', [])
    if dislikes:
        dislikes = list(map(urlDecode, dislikes.split('|')))

    strFormat = '%y/%m/%d'
    startDate = datetime.datetime.now().strftime(strFormat)
    endDate = (datetime.datetime.now() + datetime.timedelta(days=clientDefaultTripLength)).strftime(strFormat)
    startDayTime, endDayTime = clientDefaultStartTime, clientDefaultEndTime

    startDate = request.args.get('startDate', startDate)
    endDate = request.args.get('endDate', endDate)
    startDayTime = float(request.args.get('startDayTime', startDayTime))
    endDayTime = float(request.args.get('endDayTime', endDayTime))

    page = int(request.args.get('page', '1'))

    itinerary = _getItinerary(cityName, likes, likesTimings, dislikes, startDate, endDate, startDayTime, endDayTime, page)

    tend = time.time()
    print('Time for request:', tend - tstart)
    return jsonify(itinerary)


@clientAPI.route('/api/recent-plans')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def getRecentPlans():
    return jsonify(recentPlans)
