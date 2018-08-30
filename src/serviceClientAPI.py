from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import json
from utilities import urlDecode
from itineraryPlanner import getDayItinerary
import time

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


@clientAPI.route('/api/itinerary')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def getItinerary():
    tstart = time.time()
    cityName = request.args.get('city', None)
    constraints = request.args.get('constraints', {})
    print(cityName, constraints)
    if cityName:
        cityName = urlDecode(cityName)
        city = cities[cityName]
        points = getTopPointsOfCity(city, 20)['points'].values()
        points = [point for point in points if point['coordinates'] != None][:7]
        print([point['pointName'] for point in points])
        itinerary = getDayItinerary(points, [], [], [], 9, 21, 1)[0]
        tend = time.time()
        print('Time for request:', tend - tstart)
        return jsonify(itinerary)
    tend = time.time()
    print('Time for request:', tend - tstart)
    return 'invalid city'


@clientAPI.route('/api/recent-plans')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def getRecentPlans():
    return jsonify(recentPlans)
