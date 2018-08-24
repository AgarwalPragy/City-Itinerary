from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

clientAPI = Blueprint('clientAPI', __name__)


cities = {
    'England/London':    {'countryName': 'England', 'cityName': 'London', 'cityImage': r'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/London_Thames_Sunset_panorama_-_Feb_2008.jpg/2880px-London_Thames_Sunset_panorama_-_Feb_2008.jpg'},
    'USA/New York City': {'countryName': 'USA', 'cityName': 'New York City', 'cityImage': r'https://lonelyplanetimages.imgix.net/mastheads/GettyImages-538096543_medium.jpg?sharp=10&vib=20&w=1200'},
    'USA/Los Angeles':   {'countryName': 'USA', 'cityName': 'Los Angeles', 'cityImage': r'https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/Los_Angeles%2C_Winter_2016.jpg/1200px-Los_Angeles%2C_Winter_2016.jpg'},
    'India/New Delhi':   {'countryName': 'India', 'cityName': 'New Delhi', 'cityImage': 'http://blog.aaligasht.com/wp-content/uploads/2017/05/new-delhi-Header-Image.jpg'},
    'India/Agra':        {'countryName': 'India', 'cityName': 'Agra', 'cityImage': 'https://cdn.wheelstreet.com/images/cityBanner/agra_large.jpg'},
    'China/Shanghai':    {'countryName': 'China', 'cityName': 'Shanghai', 'cityImage': 'https://www.burgessyachts.com/media/adminforms/locations/s/k/skyline_of_modern_city_with_sunrise_in_shanghai_vb1042938.jpg'},
    'Singapore/Singapore': {'countryName': 'Singapore', 'cityName': 'Singapore', 'cityImage': 'https://fm.cnbc.com/applications/cnbc.com/resources/img/editorial/2018/03/14/105066394-GettyImages-498350103_1.1910x1000.jpg'}
}

recentPlans = [
    {'city': 'England/London', 'duration': '48'},
    {'city': 'India/Agra', 'duration': '168'},
    {'city': 'India/New Delhi', 'duration': '72'},
    {'city': 'Singapore/Singapore', 'duration': '6'}
]


@clientAPI.route('/cities')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def getCities():
    return jsonify(cities)



@clientAPI.route('/recent-plans')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def getRecentPlans():
    return jsonify(recentPlans)
