import os
import re
import requests
from bs4 import BeautifulSoup

def main():
    filePath = "POI_Access_Data/tripadvisor_cities_access_url"

    outFilePath = "POI_Data/AttractionsFromTripadvisor"

    numOfPages = 3

    #delete outFile is already there 
    if os.path.exists(outFilePath):
        os.remove(outFilePath)


    urlsDetailFile = open(filePath, 'r')

    citiesAndUrls = urlsDetailFile.readlines()

    for cityAndUrl in citiesAndUrls:
        [city, suffixUrl, prefixUrl] = cityAndUrl.split("\t")
        for pageNo in range(1, numOfPages+1):
            nthPageUrl = getUrlofNthPage(suffixUrl,prefixUrl, pageNo)
            print("processing:", nthPageUrl)
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

def getUrlofNthPage(suffixUrl, prefixUrl, n):
    if(n == 1):
        return suffixUrl + prefixUrl
    else:
        middleUrl = "oa" + str((n-1) * 30) + "-"
        return suffixUrl + middleUrl + prefixUrl


def getAttractions(urlForcity):
    # Collect and parse first page
    page = requests.get(urlForcity)
    soup = BeautifulSoup(page.content, 'html.parser')

    g_data = soup.find_all("div", {"class": "listing_title "})

    #root page url
    parentPageUrl = "https://www.tripadvisor.com"
    
    tourSetRegex = ".+([0-9]+).*"
    tourSetRegChecker = re.compile(tourSetRegex)
    attractions = []
    for data in g_data:
        try:
            attractionsOrTourSet = data.contents[1].text.encode('utf-8').strip()
            if tourSetRegChecker.match(attractionsOrTourSet):
                if isContainsIgnoredList(attractionsOrTourSet.lower()) == False:
                    childURL = data.contents[1].get("href")
                    newPageUrl = parentPageUrl + childURL
                    newPage = requests.get(newPageUrl)
                    newSoup = BeautifulSoup(newPage.content, 'html.parser')
                    newPage_data = newSoup.find_all("div", {"class":"listing_title"})
                    for newData in newPage_data:
                        try:
                            attraction = newData.contents[1].text.encode('utf-8').strip()
                            if isContainsIgnoredList(attraction.lower()) == False:
                                attractions.append(cleanString(attraction + "[ "+attractionsOrTourSet.split("(")[0] + "]"))
                        except:
                            pass
            else:
                attractions.append(cleanString(attractionsOrTourSet))
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