import requests
import json
import time 
import datetime
import sys
sys.path.append('.')

from entities import *
from utilities import *


def processQuery(countryName, cityName, root_query, query):
	print("processing: " + query)
	result = requests.get(query)
	# json method of response object convert
	# json format data into python format data
	time.sleep(10)
	json_result = result.json()

	result = json_result['results']

	for i in range(len(result)):
		# Print value corresponding to the
		# 'name' key at the ith index of y
		pointName = result[i]['name']
		rating = float(result[i]['rating'])
		rating = scaleRating(rating, 1, 5)
		place_type = ','.join(result[i]['types'])
		lat = str(result[i]['geometry']['location']['lat'])
		lng = str(result[i]['geometry']['location']['lng'])
		address = result[i]['formatted_address']

		print(pointName)
		print(rating)
		print(place_type)
		print(lat, ',', lng)
		pointListing = PointListing("Google_Place_API", sourceURL= query, crawlTimestamp=getCurrentTime(),
									countryName=countryName, cityName=cityName, pointName=pointName, avgRating = rating,
									category = place_type, coordinates = lat + ", " + lng, address = address,
									)

		POIs[pointName + ", " + cityName + ", "+ countryName] = pointListing
	#if 'next_page_token' in json_result.keys():
		#processQuery(countryName, cityName, root_query, root_query + "&pagetoken="+json_result['next_page_token'])		

def printPOI(OutfilePath):
	outFile = open(OutfilePath, 'w')
	length = len(POIs)
	count = 0
	outFile.write("[")
	for key in POIs:
		#print(POIs[key])
		data = json.dumps(POIs[key].__dict__)
		outFile.write(data)
		count += 1
		if count < length:
			outFile.write(",\n")
	outFile.write("]")
	outFile.close()



if __name__ == '__main__':
	OutfilePath = "googlePlaceAPI.json"
	api_key = 'AIzaSyAjJ4_yaHgBv8FzgeWwkTojIrx2cYWUaYA'

	intrested_types = ["bar", "cafe", "casino", "hindu+temple", "movie+theater", "museum", "night+club", "park", "restaurant", "spa", "stadium", "zoo"]

	cities = [{'city': 'bangkok', 'country' : 'thailand'}, {'city' : 'dubai', 'country' : 'Emirate of Dubai'}, {'city': 'london', 'country' : 'United Kingdom'}]

	POIs = {}
	root_url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query="
	for city in cities:
		for intrested_type in intrested_types:
			query = root_url + intrested_type + "s+in+" + city['city'] + "&key="+api_key
			processQuery(city['country'], city['city'], query, query)

	printPOI(OutfilePath)



