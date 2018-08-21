import scrapy
import datetime
import sys
sys.path.append('.')

from entities import *
from utilities import *

# TODO: Silence (but log) crawling exceptions to prevent crashes
# TODO: Make sure when aggregation is done, values are stripped of whitespace first
def getStartingUrls(filePath = "Crawler/POI_Access_Data/skyscanner_cities_access_url"):
    urlsDetailFile = open(filePath, 'r')

    citiesAndUrls = urlsDetailFile.readlines()

    startingUrls = []
    for cityAndUrl in citiesAndUrls:
        [city, urlForcity] = cityAndUrl.split("\t")
        startingUrls.append(urlForcity.strip())
    urlsDetailFile.close()
    return startingUrls



class CrawlerViator(scrapy.Spider):
    name = 'skyscanner'

    start_urls = getStartingUrls()
    #["https://www.trip.skyscanner.com/london/things-to-do", "https://www.trip.skyscanner.com/dubai/things-to-do",
    #"https://www.trip.skyscanner.com/bangkok/things-to-do"]
    #getStartingUrls()

    def parse(self, response: scrapy.http.Response):
        hrefs = response.css('div.items_list *> h2 > a::attr(href)').extract()
        attractionNumber =  1
        for href in hrefs:
            self.log("visiting: " + href)
            meta = {'rank' : attractionNumber }
            yield response.follow(href, callback=self.parseAttractionsPage, meta = meta)
            attractionNumber += 1

        nextPageLink = response.css('div.items_list > div:nth-child(2) > ul > li.next.next_page > a::attr(href)').extract_first()
        if nextPageLink:
            self.log("nextpage: " + nextPageLink)
            if attractionNumber < 300:
                yield response.follow(nextPageLink, callback=self.parse)

    def parseAttractionsPage(self, response: scrapy.http.Response):
        breadcrumbs = response.css('div.placeInfoColumn > ul > li > a > span::text').extract()
        countryName = breadcrumbs[0]
        cityName = breadcrumbs[1]
        pointName = response.css('div.placeInfoColumn > ul > li >span::text').extract()[-1]

        self.log("visiting " + countryName + " " + cityName + " " + pointName)
        data = response.css('div.placeDescriptionBox > div')
        description, notes = None, None
        if len(data) > 0:
            description = data[0]
            description = '\n'.join(description.css('div::text').extract())
        if len(data) > 1:
            notes = data[1].css('::text').extract_first()

        addressBlock = response.css('div#allPlacesTopicDetails.row > div > div.webtext')
        address = addressBlock.css('div[itemprop="streetAddress"]::text').extract_first()

        ratingAndCountBox = response.css('div.detail.avgRating.row')

        avgRating, ratingCount = None, None
        if ratingAndCountBox:
            bestRating = int(ratingAndCountBox.css('div.avgRatingDetail > meta[itemprop="bestRating"]::attr(content)').extract_first())
            worstRating = int(ratingAndCountBox.css('div.avgRatingDetail > meta[itemprop="worstRating"]::attr(content)').extract_first())
            givenRating = float(ratingAndCountBox.css('div.avgRatingDetail > meta[itemprop="ratingValue"]::attr(content)').extract_first())
            ratingCount = int(ratingAndCountBox.css('div.countAndTotal > span[itemprop="ratingCount"]::text').extract_first())
            avgRating = scaleRating(givenRating=givenRating, worstRating=worstRating, bestRating=bestRating)
            
            reviewsBox = response.css('div.review_list.row > div > div > div > div.placeRating')
            for reviewBox in reviewsBox:
                rating = float(reviewBox.css('div.recommendRatings.row > div > div::attr(aria-label)').extract_first().split()[0])
                ratingDate = reviewBox.css('div.recommendRatings.row > span::text').extract_first()
                content = reviewBox.css('div.readable.description > span > p::text').extract_first()

                rating = scaleRating(rating, 1, 5)
                yield Review(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                             countryName=countryName, cityName=cityName, pointName=pointName,
                             content=content, rating=rating, date=ratingDate).jsonify()


        pointListing = PointListing(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                    countryName=countryName, cityName=cityName, pointName=pointName,
                                    description=description, notes=notes, address=address, rank = response.meta['rank'],
                                    avgRating=avgRating, ratingCount=ratingCount)

        yield pointListing.jsonify()


        ImageResource = response.css('div#topicPhotoGalleryCt.row > div > span > img::attr(src)')

        if ImageResource:
            pointImage = ImageResource.extract_first()
            self.log("imageURL " + pointImage)
            #yield ImageResource(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                #countryName=countryName, cityName=cityName, pointName=pointName,
                                #imageURL=pointImage).jsonify()