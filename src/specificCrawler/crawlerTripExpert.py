import scrapy
import json
import sys
import time
sys.path.append('.')

from entities import *
from utilities import *
from requiredPlaces import requiredCountries, requiredCities, processedRequiredCities

# TODO: Silence (but log) crawling exceptions to prevent crashes
# TODO: Make sure when aggregation is done, values are stripped of whitespace first

apiKey = '6cb54d22babb25cc64ae730f17455338'

skipNonRequired = True
numForType = {
    1: 50,
    2: 50,
    3: 100,
}
limit = max(numForType.values())*3

print('RequiredCities', requiredCities)
print('RequiredCountries', requiredCountries)


with open('../data/tripexpertData/raw/countries.json', 'r') as f:
    availableCountries = json.loads(f.read())['response']['countries']

with open('../data/tripexpertData/raw/destinations.json', 'r') as f:
    availableCities = json.loads(f.read())['response']['destinations']


availableCityNames = [processName(city['name']) for city in availableCities]
availableCountryNames = [processName(country['name']) for country in availableCountries]

idToCountry = {country['id']: country['name'] for country in availableCountries}
idToCity = {city['id']: city for city in availableCities}

for city in requiredCities:
    if processName(city) not in availableCityNames:
        print('City not available', city)

for country in requiredCountries:
    if processName(country) not in availableCountryNames:
        print('Country not available', country)


class CrawlerTripExpert(scrapy.Spider):
    name = 'tripexpert'
    start_urls = ['https://www.google.com']

    requestCount = 0

    def incrementRequestCount(self):
        self.requestCount += 1
        if self.requestCount % 100 == 0:
            time.sleep(1)
        if self.requestCount % 1000 == 0:
            time.sleep(10)
        if self.requestCount % 10000 == 0:
            time.sleep(100)

    def parse(self, response: scrapy.http.Response):
        # must always be fired

        venuesQueryURL = 'https://api.tripexpert.com/v1/venues?destination_id={}&api_key={}&limit={}'
        for city in availableCities:
            if processName(city['name']) not in processedRequiredCities:
                if skipNonRequired:
                    print('Skipping', city['name'])
                    continue
            queryURL = venuesQueryURL.format(city['id'], apiKey, limit)
            yield response.follow(queryURL, callback=self.parseCityVenues, meta={
                'city_id': city['id']
            })

    def parseCityVenues(self, response: scrapy.http.Response):
        # example page: https://api.tripexpert.com/v1/venues?destination_id=3&api_key=6cb54d22babb25cc64ae730f17455338&limit=100

        self.incrementRequestCount()

        venues = json.loads(response.text)['response']['venues']

        venueIdURL = 'https://api.tripexpert.com/v1/venues/{}?api_key={}'
        for index, venue in enumerate(venues):
            venueType = int(venue['venue_type_id'])
            if 'rank_in_destination' not in venue:
                venueRank = 1 + (index // 3)
            else:
                venueRank = int(venue['rank_in_destination'])
            if venueRank > numForType[venueType]:
                # This venue is too poor for our interest
                continue

            queryURL = venueIdURL.format(venue['id'], apiKey)
            yield response.follow(queryURL, callback=self.parseVenueDetails, meta={
                'city_id': response.meta['city_id'],
                'venue_id': venue['id']
            })

    def parseVenueDetails(self, response: scrapy.http.Response):
        # example page: https://api.tripexpert.com/v1/venues/1557894?api_key=6cb54d22babb25cc64ae730f17455338

        self.incrementRequestCount()

        venue = json.loads(response.text)['response']['venues'][0]
        pointName = venue['name']
        city = idToCity[int(venue['destination_id'])]
        cityName = city['name']
        countryName = city['country_name']

        address = venue['address'].strip()
        if venue['latitude'] and venue['longitude']:
            coordinates = ','.join([venue['latitude'], venue['longitude']])
        else:
            coordinates = None

        days = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        opening = {day: 'unavailable' for day in days}
        closing = {day: 'unavailable' for day in days}
        if 'opening_hours' in venue:
            for item in venue['opening_hours']:
                open = ''
                close = ''
                if item['range_as_text']:
                    rangeAsText: str = item['range_as_text']
                    open, close = rangeAsText.lower().replace(' ', '').split('-')
                else:
                    continue

                if item['day_as_text']:
                    dayAsText = item['day_as_text'].lower().replace(' ', '')
                    if '-' in dayAsText:
                        startDay, endDay = dayAsText.split('-')
                        startindex = days.index(startDay)
                        endindex = days.index(endDay)
                        i = startindex
                        while True:
                            print(startindex, endindex, i)
                            opening[days[i]] = open
                            closing[days[i]] = close
                            i = (i + 1) % 7
                            if i == (endindex + 1)%7:
                                break
                    else:
                        opening[dayAsText] = open
                        closing[dayAsText] = close
        opening = [opening[day] for day in days]
        closing = [closing[day] for day in days]
        if all(value == 'unavailable' for value in opening) or all(value == 'unavailable' for value in closing):
            opening, closing = None, None
        else:
            opening = ','.join(opening)
            closing = ','.join(closing)

        description = '\n'.join('"{}" - {}'.format(review['extract'], review['publication_name']) for review in venue['reviews'])

        venueType = int(venue['venue_type_id'])
        canEat, canStay, canTour = False, False, False
        if venueType == 3:
            # attraction
            canEat, canStay, canTour = False, False, True
        elif venueType == 2:
            # restaurant
            canEat, canStay, canTour = True, False, False
        elif venueType == 1:
            # hotel
            canEat, canStay, canTour = True, True, False

        category = ['hotel', 'restaurant', 'attraction'][venueType-1]
        tripexpertScore = venue['tripexpert_score']
        website = venue['website']

        rankInCity = venue['rank_in_destination']

        pointListing = PointListing(crawler='tripexpert', sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                    countryName=countryName, cityName=cityName, pointName=pointName,
                                    address=address, coordinates=coordinates,
                                    openingHour=opening, closingHour=closing,
                                    description=description,
                                    canEat=canEat, canTour=canTour, canStay=canStay,
                                    category=category,
                                    tripexpertScore=tripexpertScore,
                                    website=website, rank=rankInCity).jsonify()

        yield pointListing

        for item in venue['photos']:
            yield ImageResource(crawler='tripexpert', sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                countryName=countryName, cityName=cityName, pointName=pointName,
                                imageURL=item['url']).jsonify()
