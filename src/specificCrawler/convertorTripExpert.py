import json
import sys
sys.path.append('.')

from jsonUtils import EnhancedJSONEncoder
from entities import *
from utilities import getCurrentTime


def process():
    with open('../data/tripexpertData/raw/destinations.json', 'r') as f:
        availableCities = json.loads(f.read())['response']['destinations']

    listings = []
    for city in availableCities:
        countryName = city['country_name']
        cityName = city['name']
        coordinates = ','.format(city['latitude'], city['longitude'])
        if 'None' in coordinates:
            coordinates = None

        crawler = 'tripexpertConvertor'
        sourceURL = 'https://api.tripexpert.com/v1/destinations?api_key=6cb54d22babb25cc64ae730f17455338&limit=10000'
        crawlTimestamp = getCurrentTime()

        cityListing = CityListing(crawler=crawler, sourceURL=sourceURL, crawlTimestamp=crawlTimestamp, countryName=countryName, cityName=cityName, coordinates=coordinates)

        imageURL: str = city['index_photo']
        if '?' in imageURL:
            imageURL = imageURL[:imageURL.index('?')]

        imageListing = ImageResource(crawler=crawler, sourceURL=sourceURL, crawlTimestamp=crawlTimestamp, countryName=countryName, cityName=cityName, imageURL=imageURL)

        listings.append(cityListing)
        listings.append(imageListing)

    with open('../data/tripexpertData/cities.json', 'w') as f:
        f.write(json.dumps(listings, cls=EnhancedJSONEncoder))


if __name__ == '__main__':
    process()
