import requests
import json
import time 
import datetime
import sys
sys.path.append('.')

from entities import *
from utilities import *


def processQuery(countryName: str, cityName: str, rootQuery, query, sleepSeconds: int = 10):
    print('processing:', query)
    time.sleep(sleepSeconds)

    result = requests.get(query)
    # json method of response object convert
    # json format data into python format data
    json_result = result.json()
    result = json_result['results']

    for i in range(len(result)):
        # Print value corresponding to the
        # 'name' key at the ith index of y
        pointName = result[i]['name']
        rating = float(result[i]['rating'])
        rating = scaleRating(rating, 1, 5)
        placeType = ','.join(result[i]['types'])
        latitude = str(result[i]['geometry']['location']['lat'])
        longitude = str(result[i]['geometry']['location']['lng'])
        address = result[i]['formatted_address']
        coordinates = latitude + ',' + longitude

        print(pointName)
        print(rating)
        print(placeType)
        print(latitude, ',', longitude)
        pointListing = PointListing('Google_Place_API', sourceURL= query, crawlTimestamp=getCurrentTime(),
                                    countryName=countryName, cityName=cityName, pointName=pointName, avgRating=rating,
                                    category=placeType, coordinates=coordinates, address=address,
                                    )

        POIs.append(pointListing)

    # if 'next_page_token' in json_result.keys():
    #     processQuery(countryName, cityName, root_query, root_query + "&pagetoken="+json_result['next_page_token'])


def savePointListings(filename: str):
    data = json.dumps([poi.jsonify() for poi in POIs])
    with open(filename, 'w') as f:
        f.write(data)


if __name__ == '__main__':
    OutfilePath = "googlePlaceAPI.json"
    api_key = 'AIzaSyAjJ4_yaHgBv8FzgeWwkTojIrx2cYWUaYA'

    interestedTypes = [
        'bar',
        'cafe',
        'casino',
        'hindu+temple',
        'movie+theater',
        'museum',
        'night+club',
        'park',
        'restaurant',
        'spa',
        'stadium',
        'zoo'
    ]

    cities = [
        {'city': 'bangkok', 'country': 'thailand'},
        {'city': 'dubai', 'country': 'Emirate of Dubai'},
        {'city': 'london', 'country': 'United Kingdom'}
    ]

    POIs = []

    root_url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query="
    for city in cities:
        for interestedType in interestedTypes:
            # query = root_url + interestedType + "s+in+" + city['city'] + "&key=" + api_key
            query = '{}{}s+in+{}&key={}'.format(
                root_url,
                interestedType,
                city['city'],
                api_key
            )
            processQuery(city['country'], city['city'], query, query)
            break
        break

    savePointListings(OutfilePath)



