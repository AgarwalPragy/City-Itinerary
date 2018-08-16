import os
import requests
from bs4 import BeautifulSoup

def main():
	filePath = "/Users/deepak.ku/Desktop/City Itinerary Maker/Data/POI_Access_Data/inspirock_cities_access_url"

	outFilePath = "/Users/deepak.ku/Desktop/City Itinerary Maker/Data/POI_Data/AttractionsFromInspirock"

	#delete outFile is already there 
	if os.path.exists(outFilePath):
  		os.remove(outFilePath)


	urlsDetailFile = open(filePath, 'r')

	citiesAndUrls = urlsDetailFile.readlines()

	for cityAndUrl in citiesAndUrls:
		[city, urlForcity] = cityAndUrl.split("\t")
		print "processing: " + urlForcity
		attractions = getAttractions(urlForcity)
		writeAttractionsInFile(outFilePath, city, attractions)

	urlsDetailFile.close()




def getAttractions(urlForcity):
	# Collect and parse first page
	page = requests.get(urlForcity)
	soup = BeautifulSoup(page.content, 'html.parser')

	g_data = soup.find_all("div", {"class": "name attLink clickable-text"})
	
	attractions = []
	for data in g_data:
		try:
			#print data.text
			attractions.append(data.text.encode('utf-8'))
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