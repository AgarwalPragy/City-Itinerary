import os
import re
import requests
from bs4 import BeautifulSoup

def main():
	filePath = "/Users/deepak.ku/Desktop/City Itinerary Maker/Data/POI_Access_Data/skyscanner_cities_access_url"

	outFilePath = "/Users/deepak.ku/Desktop/City Itinerary Maker/Data/POI_Data/AttractionsFromSkyscanner1"

	numOfPages = 25

	#delete outFile is already there 
	if os.path.exists(outFilePath):
  		os.remove(outFilePath)


	urlsDetailFile = open(filePath, 'r')

	citiesAndUrls = urlsDetailFile.readlines()

	for cityAndUrl in citiesAndUrls:
		[city, url] = cityAndUrl.split("\t")
		for pageNo in range(1, numOfPages+1):
			nthPageUrl = getUrlofNthPage(url.strip(), pageNo)
			print "processing " + nthPageUrl
			attractions = getAttractions(nthPageUrl)
			writeAttractionsInFile(outFilePath, city, attractions)

	urlsDetailFile.close()



#pass data in lowercaseonly 
def isContainsIgnoredList(attraction):
	ignoredList = ["trip", "tour"]

	for ignoredData in ignoredList:
		if ignoredData in attraction:
			return True 
	return False


def cleanString(str):
	temp = ""
	for ch in str:
		if ch != '\n':
			temp += ch
	return temp

def getUrlofNthPage(url, n):
	if(n == 1):
		return url;
	else:
		return url + "?page="+str(n)


def getAttractions(urlForcity):
	# Collect and parse first page
	page = requests.get(urlForcity)
	soup = BeautifulSoup(page.content, 'html.parser')

	g_data = soup.find_all("h2", {"class": "placeName"})	
	attractions = []
	for data in g_data:
		try:
			attraction =  data.contents[0].text
			attractions.append(cleanString(attraction))
		except:
			pass
	return attractions


def writeAttractionsInFile(filePath, city, attractions):
	outFile = open(filePath, "a")

	for attraction in attractions:
		try:
			outFile.write(city + "\t" + attraction + "\n")
		except:
			pass
	outFile.close()


if __name__ == '__main__':  
   main()