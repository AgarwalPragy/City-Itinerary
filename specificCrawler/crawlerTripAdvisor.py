import scrapy
import datetime
import re
import sys
sys.path.append('.')

from entities import *
from utilities import *


# TODO: Silence (but log) crawling exceptions to prevent crashes
# TODO: Make sure when aggregation is done, values are stripped of whitespace first
def getStartingUrls(filePath = "Crawler/POI_Access_Data/tripadvisor_cities_access_url"):
    urlsDetailFile = open(filePath, 'r')

    citiesAndUrls = urlsDetailFile.readlines()

    startingUrls = []
    for cityAndUrl in citiesAndUrls:
        [city, urlForcity] = cityAndUrl.split("\t")
        print("processing:", urlForcity)
        startingUrls.append(urlForcity)
    urlsDetailFile.close()
    return startingUrls


def removeComa(reviewCount: str):
    temp = ""
    for ch in reviewCount:
        if ch >= '0' and ch <= '9':
            temp += ch
    return temp


class CrawlerViator(scrapy.Spider):
    name = 'tripAdvisor'

    start_urls = getStartingUrls()
    #['https://www.tripadvisor.in/Attractions-g186338-Activities-London_England.html#FILTERED_LIST']

    def parse(self, response: scrapy.http.Response):
        # example page:  https://www.viator.com/Netherlands/d60
        attractionBoxs = response.css('div.attraction_list.attraction_list_short > div.attraction_element > div > div > div > div > div.listing_title')
        
        tourSetRegex = ".+([0-9]+).*"
        tourSetRegChecker = re.compile(tourSetRegex)

        attractionNumber = 1
        for attraction in attractionBoxs:
            pointName = attraction.css('a::text').extract_first()
            if not tourSetRegChecker.match(pointName):
                attractionUrl = response.urljoin(attraction.css('a::attr(href)').extract_first())
                meta = {'rank' : attractionNumber }
                yield response.follow(url = attractionUrl, callback=self.parseAttractionsPage, meta = meta)
                attractionNumber += 1


        nextPageLink = response.css('div.al_border.deckTools.btm > div > div.unified.pagination > a.nav.next.rndBtn.ui_button.primary.taLnk::attr(href)')
        if nextPageLink:
            nextPageLink = response.urljoin(nextPageLink.extract_first())
            self.log("nextpage: " + nextPageLink)
            yield response.follow(nextPageLink, callback=self.parse)

    def parseAttractionsPage(self, response: scrapy.http.Response):
        # example page: https://www.viator.com/Amsterdam-attractions/Albert-Cuyp-Market/d525-a8126
        breadcrumbs = response.css('ul.breadcrumbs > li > a > span::text').extract()
        countryName = breadcrumbs[-3]
        cityName = breadcrumbs[-2]
        # -2 is the word 'attractions'
        pointName = response.css('ul.breadcrumbs > li::text').extract()[-1]
        # we don't really care about the region once we have the city?

        self.log("visiting " + countryName + " " + cityName + " " + pointName)
        data = []#response.css('div.text::text').extract()[1]
        description, notes = None, None
        if len(data) > 0:
            description = data[0]
            description = '\n'.join(description.css('div::text').extract())
        if len(data) > 1:
            notes = data[1].css('::text').extract_first()

        address = response.css('span.street-address::text').extract_first()
        
        ratingBox = response.css('span.header_rating > div.rs.rating') 

        avgRating, ratingCount = None, None
        if ratingBox:
            bestRating = 5 #int(ratingAndCountBox.css('div.avgRatingDetail > meta[itemprop="bestRating"]::attr(content)').extract_first())
            worstRating = 1 #int(ratingAndCountBox.css('div.avgRatingDetail > meta[itemprop="worstRating"]::attr(content)').extract_first())
            givenRating = int(ratingBox.css('div > span::attr(class)').extract_first().split('_')[-1])/10
            ratingCount = int(removeComa(ratingBox.css('a.more > span::text').extract_first()))
            avgRating = scaleRating(givenRating=givenRating, worstRating=worstRating, bestRating=bestRating)
            self.log("ratings: "+ str(avgRating))        


        pointListing = PointListing(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                    countryName=countryName, cityName=cityName, pointName=pointName,
                                    description=description, notes=notes, address=address, rank = response.meta['rank'],
                                    avgRating=avgRating, ratingCount=ratingCount)

        yield pointListing.jsonify()

        yield response.follow(url = response.url, callback=self.getReviews, meta = {
                            'countryName': countryName,
                            'cityName': cityName,
                            'pointName': pointName
                            })
        #ImageResource = response.css('div#topicPhotoGalleryCt.row > div > span > img::attr(src)')

        #if ImageResource:
            #pointImage = ImageResource.extract_first()
            #self.log("imageURL " + pointImage)
            #yield ImageResource(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                #countryName=countryName, cityName=cityName, pointName=pointName,
                                #imageURL=pointImage).jsonify()


    def getReviews(self, response: scrapy.http.Response):
        self.log("review method called")

        reviewCount = 0
        reviewsUrl = response.css('div.quote.isNew > a::attr(href)').extract()
        for url in reviewsUrl:
            url = response.urljoin(url)
            self.log("review url: " + url)
            yield scrapy.Request(url, callback=self.parseReviewsPage, meta = response.meta)
            reviewCount += 1

        nextPageLink = response.css('div.collapsedReviewsList > div > div > a::attr(href)').extract()

        if len(nextPageLink) == 2:
            newPageUrl = nextPageLink[1]
            newPageUrl = response.urljoin(newPageUrl)
            if reviewCount < 25:
                yield scrapy.Request(url = newPageUrl, callback = self.getReviews, meta = response.meta)


    def parseReviewsPage(self, response: scrapy.http.Response):

        box = response.css('div.rating.reviewItemInline')

        content = response.css('div.entry > p.partial_entry::text').extract_first()
        ratingDate = box.css('span::attr(title)').extract_first()
        rating = float(box.css('span::attr(class)').extract_first().split('_')[-1])/10
        rating = scaleRating(rating, 1, 5)
        yield Review(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                     countryName=response.meta['countryName'], cityName=response.meta['cityName'], pointName=response.meta['pointName'],
                     content=content, rating=rating, date=ratingDate).jsonify()

