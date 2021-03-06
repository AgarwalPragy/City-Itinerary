from flask import Blueprint, request, jsonify, render_template
from flask_cors import cross_origin
import json
import time
import datetime
from functools import lru_cache, wraps
from collections import defaultdict
from random import randint


from utilities import urlDecode, latlngDistance, roundUpTime, readAllListingsFromFiles
from itineraryPlanner import getDayItinerary
from tunable import clientDefaultCity, clientDefaultTripLength, clientDefaultEndTime, clientDefaultStartTime
from tunable import maxCityRadius, avgSpeedOfTravel, clientMaxPossiblePointsPerDay
from clustering import getBestPoints
import clusteringStatic

clientAPI = Blueprint('clientAPI', __name__)

countries, cities, citiesNoPoints = None, None, None
listings = None

recentPlans = [
    # {'city': 'United Kingdom/London', 'duration': '48'},
    # {'city': 'India/Agra', 'duration': '168'},
    # {'city': 'India/New Delhi', 'duration': '72'},
    # {'city': 'Singapore/Singapore', 'duration': '6'}
]


def loadListings():
    listings = readAllListingsFromFiles()
    listings = {listing['_uuid']: listing for listing in listings}
    return listings


def loadData():
    print('Loading Aggregated data')
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
    print('done.')

    return countries, cities, citiesNoPoints


@clientAPI.before_app_first_request
def loadEverything():
    global countries, cities, citiesNoPoints
    global listings
    countries, cities, citiesNoPoints = loadData()
    listings = loadListings()


def autoNiceView(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        try:
            if request.args.get('pretty', None) is not None and response.is_json:
                return render_template('apiViewer.html', data=json.dumps(response.get_json()))
        except Exception as e:
            print(e)
        return response

    return wrapper


@lru_cache(None)
def getTopPointsOfCity(cityName, amount):
    city = cities[cityName]

    # Remove outliers
    cityCoords = city['coordinates']
    points = city['points']

    # Remove points for which we don't have coordinates
    points = {pointName: point for pointName, point in points.items() if point.get('coordinates', None) is not None}

    # Remove outliers
    try:
        cityCoords = list(map(float, cityCoords.split(',')))
        points = {
            pointName: point
            for pointName, point in points.items()
            if latlngDistance(*point['coordinates'].split(','), *cityCoords) < maxCityRadius
        }
    except Exception as e:
        # print('Error:', e)
        return {
            'pointsOrder': [],
            'points': []
        }

    topnames = city['pointsOrder'][:150]
    pointsOrder = []
    topPoints = {}
    for pointName in topnames:
        if pointName in points:
            topPoints[pointName] = points[pointName]
            pointsOrder.append(pointName)
            if len(topPoints) == amount:
                break

    return {
        'pointsOrder': pointsOrder,
        'points': topPoints
    }


@lru_cache(None)
def _getCities():
    goodCities = {cityName: city for cityName, city in citiesNoPoints.items() if len(getTopPointsOfCity(cityName, 10)['points']) == 10}
    return goodCities


@clientAPI.route('/api/cities')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
@autoNiceView
def getCities():
    return jsonify(_getCities())


@clientAPI.route('/api/points')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
@autoNiceView
def getCityPoints():
    cityName = request.args.get('city', None)
    amount = int(request.args.get('amount', 100))
    if cityName:
        cityName = urlDecode(cityName)
        return jsonify(getTopPointsOfCity(cityName, amount))
    return 'invalid city'


@clientAPI.route('/api/points-order')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
@autoNiceView
def getCityPointsOrder():
    cityName = request.args.get('city', None)
    amount = int(request.args.get('amount', 100))
    if cityName:
        cityName = urlDecode(cityName)
        return jsonify(getTopPointsOfCity(cityName, amount)['pointsOrder'])
    return 'invalid city'


@clientAPI.route('/api/point')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
@autoNiceView
def getSinglePoint():
    cityName = request.args.get('city', None)
    pointName = request.args.get('point', None)
    if cityName and pointName:
        cityName = urlDecode(cityName)
        pointName = urlDecode(pointName)
        return jsonify(getTopPointsOfCity(cityName, 150)['points'][pointName])
    return 'invalid city/point'


@clientAPI.route('/api/listings')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
@autoNiceView
def getListings():
    uuids = request.args.get('uuids', '')
    uuids = uuids.replace(' ', '')
    if uuids:
        if '|' in uuids:
            uuids = uuids.split('|')
        elif '""' in uuids:
            uuids = [uuid.replace('"', '') for uuid in uuids.split('""')]
        else:
            uuids = [uuids]
        return jsonify({uuid: listings[uuid] for uuid in uuids})
    return 'invalid uuid'


@clientAPI.route('/api/validate')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def validateLikes():
    cityName = clientDefaultCity
    cityName = request.args.get('city', cityName)
    if cityName:
        cityName = urlDecode(cityName)

    strFormat = '%y/%m/%d'
    startDate = datetime.datetime.now().strftime(strFormat)
    endDate = (datetime.datetime.now() + datetime.timedelta(days=clientDefaultTripLength - 1)).strftime(strFormat)
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
            if dayNum not in mustVisit:
                return 'Invalid day number {}'.format(int(dayNum))
            mustVisit[dayNum].append((enterTime, exitTime, pointName))
        for dayNum in mustVisit:
            mustVisit[dayNum] = list(sorted(mustVisit[dayNum]))

    dislikes = request.args.get('dislikes', [])
    if dislikes:
        dislikes = set(map(urlDecode, dislikes.split('|')))

    start = datetime.datetime(*list(map(int, startDate.strip().split('/'))))
    today = start
    weekDay = (today.weekday() + 1) % 7
    weekDays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    pointMap = getTopPointsOfCity(cityName, 100)['points']
    for dayNum, visits in mustVisit.items():
        previousPoint = None
        previousExitTime = None
        for enterTime, exitTime, pointName in visits:
            if pointName in dislikes:
                return 'You\'ve asked us not to show {}'.format(pointName)
            point = pointMap[pointName]
            if 'openingHour' not in point or 'closingHour' not in point:
                continue
            opening = point['openingHour'].split(',')[weekDay]
            closing = point['closingHour'].split(',')[weekDay]
            if opening == '$' or closing == '$':
                return '{} is closed on the day {} of your plan'.format(point['pointName'], dayNum)
            opening = float(opening)
            closing = float(closing)
            if not (opening <= enterTime < exitTime <= closing):
                return 'Unacceptable enter and exit time. {} is open from {} to {} on {}'.format(
                    point['pointName'], opening, closing, weekDays[weekDay]
                )
            if previousPoint:
                travelTime = latlngDistance(*previousPoint['coordinates'].split(','),
                                            *point['coordinates'].split(',')) / avgSpeedOfTravel
                travelTime = roundUpTime(travelTime)
                if previousExitTime + travelTime > enterTime:
                    return 'It takes {} hours to travel from {} to {}. You can\'t exit {} at {} and enter {} at {}'.format(
                        travelTime, previousPoint['pointName'], point['pointName'],
                        previousPoint['pointName'], previousExitTime, point['pointName'], enterTime
                    )

            previousPoint = point
            previousExitTime = exitTime
        weekDay = (weekDay + 1) % 7

    return 'success'


def getTodaysLikes(mustVisit, page):
    todaysLikes = mustVisit[page - 1][1]  # mustVisit is 0-indexed. day is 1-indexed
    return [item[2] for item in todaysLikes], [item[:2] for item in todaysLikes]


def getNumDays(startDate, endDate):
    start = datetime.datetime(*list(map(int, startDate.strip().split('/'))))
    end = datetime.datetime(*list(map(int, endDate.strip().split('/'))))
    return (end - start).days + 1


@lru_cache(None)
def __getItinerary_incremental(cityName: str, likes, mustVisit, dislikes, startDate, endDate, startDayTime, endDayTime,
                               page, pFactor):
    numDays = getNumDays(startDate, endDate)

    if not (0 < page <= numDays):
        return {'itinerary': [], 'score': -1, 'nextPage': False, 'currentPage': 1}

    pointMap = getTopPointsOfCity(cityName, 150)['points']

    points = pointMap.values()

    # Remove dislikes
    points = [point for point in points if point['pointName'] not in set(dislikes)]

    # Remove points for which we were already shown in the previous pages
    for oldpage in range(page - 1, 0, -1):
        prevItinerary = _getItinerary_incremental(cityName=cityName,
                                                  likes=likes,
                                                  mustVisit=mustVisit,
                                                  dislikes=dislikes,
                                                  startDate=startDate,
                                                  endDate=endDate,
                                                  startDayTime=startDayTime,
                                                  endDayTime=endDayTime,
                                                  page=oldpage,
                                                  pFactor=pFactor)['itinerary']
        prevItineraryPoints = set([item['point']['pointName'] for item in prevItinerary])
        points = [point for point in points if point['pointName'] not in prevItineraryPoints]

    todaysLikes, todaysLikesTimings = getTodaysLikes(mustVisit, page)

    clusteringPoints = points[:clientMaxPossiblePointsPerDay * numDays]
    if not clusteringPoints:
        return {'itinerary': [{
            'point': {
                'pointName': '__newday__'
            },
            'dayNum': page,
            'date': 'No data. (╯°□°）╯︵ ┻━┻'
        }], 'score': -1, 'nextPage': False, 'currentPage': 1}

    todaysPoints = getBestPoints(listOfPoints=clusteringPoints,
                                 allSelectedPoints=[],
                                 numDays=numDays,
                                 numPoints=clientMaxPossiblePointsPerDay,
                                 pFactor=pFactor)

    # Remove today's like from today's points
    todaysPoints = [point for point in todaysPoints if point['pointName'] not in set(likes)]

    # choose the best points form todaysPoints points
    todaysPoints = todaysPoints[:clientMaxPossiblePointsPerDay - len(todaysLikes)]

    start = datetime.datetime(*list(map(int, startDate.strip().split('/'))))
    today = start + datetime.timedelta(days=page - 1)

    weekDay = (today.weekday() + 1) % 7

    itinerary, score = getDayItinerary(listOfPoints=todaysPoints,
                                       mustVisitPoints=[pointMap[like] for like in todaysLikes],
                                       mustVisitPlaceEnterExitTime=todaysLikesTimings,
                                       dayStartTime=(startDayTime if page == 1 else clientDefaultStartTime),
                                       dayEndTime=(endDayTime if page == numDays else clientDefaultEndTime),
                                       weekDay=weekDay,
                                       pFactor=pFactor)

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


@lru_cache(None)
def clusterCity(cityName, pointNames, numDays):
    pointMap = getTopPointsOfCity(cityName, 150)['points']
    points = [pointMap[name] for name in pointNames]

    allCoordinates = tuple(tuple(map(float, point['coordinates'].split(','))) for point in points)
    labels, labelMap = clusteringStatic.cluster(allCoordinates, numDays, debug=False)

    dayPoints = defaultdict(list)
    for point, label in zip(points, labels):
        dayPoints[labelMap[label]].append(point)

    return dayPoints


@lru_cache(None)
def __getItinerary_static(cityName: str, likes, mustVisit, dislikes, startDate, endDate, startDayTime, endDayTime,
                          page, pFactor):
    numDays = getNumDays(startDate, endDate)

    if not (0 < page <= numDays):
        return {'itinerary': [], 'score': -1, 'nextPage': False, 'currentPage': 1}

    pointMap = getTopPointsOfCity(cityName, 150)['points']
    points = pointMap.values()

    if not points:
        return {'itinerary': [{
            'point': {
                'pointName': '__newday__'
            },
            'dayNum': page,
            'date': 'No data. (╯°□°）╯︵ ┻━┻'
        }], 'score': -1, 'nextPage': False, 'currentPage': 1}

    # Remove dislikes
    pointNames = [point['pointName'] for point in points if point['pointName'] not in set(dislikes)]

    # limit the points sent for clustering
    pointNames = pointNames[:clientMaxPossiblePointsPerDay * numDays]

    cityClustering = clusterCity(cityName, tuple(pointNames), numDays)
    todaysPoints = cityClustering[page-1]

    todaysLikes, todaysLikesTimings = getTodaysLikes(mustVisit, page)

    # Remove today's like from today's points
    todaysPoints = [point for point in todaysPoints if point['pointName'] not in set(likes)]

    # choose the best points form todaysPoints points
    todaysPoints = todaysPoints[:clientMaxPossiblePointsPerDay - len(todaysLikes)]

    start = datetime.datetime(*list(map(int, startDate.strip().split('/'))))
    today = start + datetime.timedelta(days=page - 1)

    weekDay = (today.weekday() + 1) % 7

    itinerary, score = getDayItinerary(listOfPoints=todaysPoints,
                                       mustVisitPoints=[pointMap[like] for like in todaysLikes],
                                       mustVisitPlaceEnterExitTime=todaysLikesTimings,
                                       dayStartTime=(startDayTime if page == 1 else clientDefaultStartTime),
                                       dayEndTime=(endDayTime if page == numDays else clientDefaultEndTime),
                                       weekDay=weekDay,
                                       pFactor=pFactor)

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


def _getItinerary_incremental(cityName, likes, mustVisit, dislikes, startDate, endDate, startDayTime, endDayTime, page, pFactor):
    result = __getItinerary_incremental(cityName=cityName,
                                        likes=tuple(likes),
                                        mustVisit=tuple(mustVisit),
                                        dislikes=tuple(dislikes),
                                        startDate=startDate,
                                        endDate=endDate,
                                        startDayTime=startDayTime,
                                        endDayTime=endDayTime,
                                        page=page,
                                        pFactor=pFactor)
    return result


def _getItinerary_static(cityName, likes, mustVisit, dislikes, startDate, endDate, startDayTime, endDayTime, page, pFactor):
    result = __getItinerary_static(cityName=cityName,
                                   likes=tuple(likes),
                                   mustVisit=tuple(mustVisit),
                                   dislikes=tuple(dislikes),
                                   startDate=startDate,
                                   endDate=endDate,
                                   startDayTime=startDayTime,
                                   endDayTime=endDayTime,
                                   page=page,
                                   pFactor=pFactor)
    return result


@clientAPI.route('/api/itinerary')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
@autoNiceView
def getItinerary():
    tstart = time.time()

    cityName = clientDefaultCity
    cityName = request.args.get('city', cityName)
    if cityName:
        cityName = urlDecode(cityName)

    strFormat = '%y/%m/%d'
    startDate = datetime.datetime.now().strftime(strFormat)
    endDate = (datetime.datetime.now() + datetime.timedelta(days=clientDefaultTripLength - 1)).strftime(strFormat)
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

    dislikes = request.args.get('dislikes', [])
    if dislikes:
        dislikes = list(map(urlDecode, dislikes.split('|')))

    page = int(request.args.get('page', '1'))

    algo = request.args.get('algo', 'static')
    pFactor = request.args.get('pFactor', 'less')

    itineraryFunction = _getItinerary_static
    if algo == 'incremental':
        itineraryFunction = _getItinerary_incremental

    itinerary = itineraryFunction(cityName=cityName,
                                  likes=likes,
                                  mustVisit=tupleMustVisit,
                                  dislikes=dislikes,
                                  startDate=startDate,
                                  endDate=endDate,
                                  startDayTime=startDayTime,
                                  endDayTime=endDayTime,
                                  page=page,
                                  pFactor=pFactor)

    mustVisitItinerary = []
    start = datetime.datetime(*list(map(int, startDate.strip().split('/'))))
    pointMap = getTopPointsOfCity(cityName, 100)['points']
    for dayNum in range(1, numDays + 1):
        today = start + datetime.timedelta(days=dayNum - 1)
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

    itineraryCallUUID = request.args.get('uuid', None)
    result = {
        'itinerary': itinerary,
        'mustVisit': mustVisitItinerary,
        'mustNotVisit': dislikes,
        'uuid': itineraryCallUUID
    }
    result = json.loads(json.dumps(result))

    tend = time.time()
    print('Time for request:', tend - tstart)

    return jsonify(result)


@clientAPI.route('/api/recent-plans')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
@autoNiceView
def getRecentPlans():
    return jsonify(recentPlans)


@clientAPI.route('/api/city-image')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def getCityImage():
    cityName = request.args.get('city', 'mumbai')
    cityName = cityName.strip().lower().replace(' ', '')
    if ',' in cityName:
        cityName = cityName.split(',')[0]
    if 'bengaluru' in cityName:
        cityName = 'bangalore'
    if 'calcutta' in cityName:
        cityName = 'kolkata'
    if 'bombay' in cityName:
        cityName = 'mumbai'

    return 'http://localhost:5000/resources/city-images/{}-{}.jpg'.format(cityName, randint(1, 3))
