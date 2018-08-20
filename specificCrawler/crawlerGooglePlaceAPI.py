import requests, json
from entities import *
import time 
import datetime

def getCurrentTime() -> str:
	strFormat = '%y-%m-%d %H:%M:%S'
	return datetime.datetime.now().strftime(strFormat)


def listToStr(typeList):
	temp = ""
	for data in typeList:
		temp += data + ","
	if len(temp) > 0:
		temp = temp[:-1]
	return temp

def scaleRating(givenRating: float, worstRating: int, bestRating: int) -> float:
	meanShifted = (givenRating - worstRating + 1)
	range = bestRating - worstRating
	return meanShifted / range

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
		place_type = listToStr(result[i]['types'])
		lat = str(result[i]['geometry']['location']['lat'])
		lng = str(result[i]['geometry']['location']['lng'])
		address = result[i]['formatted_address']

		print(pointName)
		print(rating)
		print(place_type)
		print(lat + ", " + lng)
		pointListing = PointListing("Google_Place_API", sourceURL= query, crawlTimestamp=getCurrentTime(),
									countryName=countryName, cityName=cityName, pointName=pointName, avgRating = rating,
									category = place_type, coordinates = lat + ", " + lng, address = address,
									)

		POIs[pointName + ", " + cityName + ", "+ countryName] = pointListing
	if 'next_page_token' in json_result.keys():
		processQuery(countryName, cityName, root_query, root_query + "&pagetoken="+json_result['next_page_token'])		

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





OutfilePath = "googlePlaceAPI.json"
api_key = 'AIzaSyAjJ4_yaHgBv8FzgeWwkTojIrx2cYWUaYA'

intrested_types = ["bar", "cafe", "casino", "hindu+temple", "movie+theater", "museum", "night+club", "park", "restaurant", "spa", "stadium", "zoo"]

cities = [{'city': 'bangkok', 'country' : 'thailand'}, {'city' : 'seoul', 'country' : 'South Korea'}]

POIs = {}
root_url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query="
for city in cities:
	for intrested_type in intrested_types:
		query = root_url + intrested_type + "s+in+" + city['city'] + "&key="+api_key
		processQuery(city['country'], city['city'], query, query)

printPOI(OutfilePath)



