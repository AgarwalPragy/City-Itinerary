import os
import requests
from bs4 import BeautifulSoup

def main():
    filePath = "POI_Access_Data/viator_cities_access_url"

    outFilePath = "POI_Data/AttractionsFromViator"

    #delete outFile is already there 
    if os.path.exists(outFilePath):
        os.remove(outFilePath)


    urlsDetailFile = open(filePath, 'r')

    citiesAndUrls = urlsDetailFile.readlines()

    for cityAndUrl in citiesAndUrls:
        [city, urlForcity] = cityAndUrl.split("\t")
        print("processing:", urlForcity)
        attractions = getAttractions(urlForcity)
        writeAttractionsInFile(outFilePath, city, attractions)

    urlsDetailFile.close()




def getAttractions(urlForcity):
    # Collect and parse first page
    page = requests.get(urlForcity)
    soup = BeautifulSoup(page.content, 'html.parser')

    g_data = soup.find_all("h2", {"class": "man mtm product-title"})

    #root page url
    #parentPageUrl = "https://www.viator.com"
    
    attractions = []
    for data in g_data:
        try:
            #child page url
            #childPageUrl = data.contents[1].get("href")
            #urlForAttraction = parentPageUrl + childPageUrl
            #print urlForAttraction
            #attractionsPage = requests.get(urlForAttraction)
            #attractionsSoup = BeautifulSoup(attractionsPage.content, 'html.parser')

            #attractions_data = attractionsSoup.find_all("div", {"id": "prodItinerary"})
            #print attractions_data.contents
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