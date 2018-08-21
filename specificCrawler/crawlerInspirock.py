import scrapy
import datetime
import sys
sys.path.append('.')

from entities import *
from utilities import *


# TODO: Silence (but log) crawling exceptions to prevent crashes
# TODO: Make sure when aggregation is done, values are stripped of whitespace first

urlToCityAndCountryMapping = {}
def getStartingUrls(filePath = "Crawler/POI_Access_Data/inspirock_cities_access_url"):
    urlsDetailFile = open(filePath, 'r')

    citiesAndUrls = urlsDetailFile.readlines()

    startingUrls = []
    for cityAndUrl in citiesAndUrls:
        [countryName, city, urlForcity] = cityAndUrl.split("\t")
        urlForcity = urlForcity.strip()
        print("processing:", urlForcity)
        urlToCityAndCountryMapping[urlForcity] = {'city' : city, 'country' : countryName}
        startingUrls.append(urlForcity)
    urlsDetailFile.close()
    return startingUrls


class CrawlerViator(scrapy.Spider):
    name = 'inspirock'

    start_urls = getStartingUrls()

    def parse(self, response: scrapy.http.Response):
        hrefs = response.css('div.tours > a::attr(href)').extract()
        attractionNumber = 1
        for href in hrefs:
            href = response.urljoin(href)
            self.log("visiting: " + href)
            meta = urlToCityAndCountryMapping[response.url]
            meta['rank'] = attractionNumber
            yield response.follow(href, callback=self.parseAttractionsPage, meta = meta)
            attractionNumber += 1


    def parseAttractionsPage(self, response: scrapy.http.Response):
        breadcrumbs = response.css('div.where-in-world > span > a > span::text').extract()
        if len(breadcrumbs) >= 3:
            #countryName = breadcrumbs[-3] 
            #cityName = breadcrumbs[-2]
            cityName = response.meta['city']
            countryName = response.meta['country']

            # -2 is the word 'attractions'
            pointName = breadcrumbs[-1]
        else:
            return

        self.log("visiting " + countryName + " " + cityName + " " + pointName)
        data = response.css('div.description.itemDescription.attraction.desc')
        description, notes = None, None
        if len(data) > 0:
            description = data[0]
            description = '\n'.join(description.css('div::text').extract())
        if len(data) > 1:
            notes = data[1].css('::text').extract_first()


        ratingAndCountBox = response.css('div.rating > div.ins-rating')

        #ratingBox = sideBox.css('p[itemprop="aggregateRating"]')
        avgRating, ratingCount = None, None
        if ratingAndCountBox:
            bestRating = 5
            worstRating = 1
            givenRating = float(ratingAndCountBox.css('span::text').extract_first())
            #ratingCount = int(ratingAndCountBox.css('div.countAndTotal > span[itemprop="ratingCount"]::text').extract_first())
            avgRating = scaleRating(givenRating=givenRating, worstRating=worstRating, bestRating=bestRating)
            


        rightBox = response.css('div.attraction-metadata > aside')
        duration , address = None, None
        if rightBox:
            duration = rightBox.css('div::text').extract()[1]
            address = rightBox.css('p::text').extract_first()

        openingsHour , closingsHour = None, None
        openCloseBox = response.css('div.attraction-metadata > aside.opening-hours > div.clearfix > table > tr > td.time::text')

        if openCloseBox:
            self.log("times: "+response.url)
            hours = openCloseBox.extract()
            openingsHour = ""
            closingsHour = ""
            for hour in hours:
                spliter = hour.split('-')
                if(len(spliter) == 2):
                    openingsHour += spliter[0].strip() + ","
                    closingsHour += spliter[1].strip() + ","
                else:
                    openingsHour += spliter[0].strip() + ","
                    closingsHour += spliter[0].strip() + ","
            openingsHour = openingsHour[:-2]
            closingsHour = closingsHour[:-2]

        pointListing = PointListing(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                    countryName=countryName, cityName=cityName, pointName=pointName,
                                    description=description, notes=notes, address=address, 
                                    openingHour = openingsHour, closingHour = closingsHour, recommendedNumHours = duration,
                                    avgRating=avgRating, ratingCount=ratingCount, rank = response.meta['rank'])

        yield pointListing.jsonify()


        ImageResource = pics = response.css('div.photos > div > ul > li > a > img::attr(src)')

        if ImageResource:
            pointImage = ImageResource.extract_first()
            self.log("imageURL " + pointImage)
            #yield ImageResource(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                #countryName=countryName, cityName=cityName, pointName=pointName,
                                #imageURL=pointImage).jsonify()