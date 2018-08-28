from flask import Blueprint, request, jsonify, render_template
from flask_cors import cross_origin
import json
from utilities import urlDecode


clientAPI = Blueprint('clientAPI', __name__)


def loadData():
    with open('aggregatedData.json', 'r') as f:
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


@clientAPI.route('/api/attractions')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def getAttractions():
    cityName = request.args.get('city', None)
    amount = int(request.args.get('amount', 50))
    if cityName:
        cityName = urlDecode(cityName)
        city = cities[cityName]
        topnames = city['pointsOrder'][:amount]

        return jsonify({
            'points': {fullName: city['points'][fullName] for fullName in topnames},
            'pointsOrder': topnames
        })
    return 'invalid city'


@clientAPI.route('/api/itinerary')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def getItinerary():
    cityName = request.args.get('city', None)
    startTime = request.args.get('startTime', None)
    endTime = request.args.get('endTime', None)

    if cityName and startTime and endTime:
        cityName = urlDecode(cityName)
        city = cities[cityName]


@clientAPI.route('/api/recent-plans')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def getRecentPlans():
    return jsonify(recentPlans)
