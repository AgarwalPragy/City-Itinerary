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
        [country, city, urlForcity] = cityAndUrl.split("\t")
        print("processing:", urlForcity)
        startingUrls.append([country, city, urlForcity])
    urlsDetailFile.close()
    return startingUrls


def removeComa(reviewCount: str):
    temp = ""
    for ch in reviewCount:
        if ch >= '0' and ch <= '9':
            temp += ch
    return temp


durationRegex = re.compile('suggested duration: (.*?) hours?')

class CrawlerTripAdvisor(scrapy.Spider):
    name = 'tripAdvisor'

    start_urls = ['https://www.google.com/']

    requestCount = 0
    def incrementRequestCount(self):
        self.requestCount += 1
        if self.requestCount % 10 == 0:
            time.sleep(4)
        if self.requestCount % 100 == 0:
            time.sleep(40)
        if self.requestCount % 1000 == 0:
            time.sleep(400)

    def parse(self, response: scrapy.http.Response):
        for url in getStartingUrls():
             yield scrapy.Request(url[2], callback=self.parseCity, meta={
                    'rank': 0,
                    'cityName': url[1],
                    'countryName': url[0]
                })


    def parseCity(self, response: scrapy.http.Response):
        #example https://www.tripadvisor.in/Attractions-g186338-Activities-London_England.html#FILTERED_LIST

        attractionBoxs = response.css('div.attraction_list.attraction_list_short > div.attraction_element > div > div > div > div > div.listing_title')
        
        tourSetRegex = ".+([0-9]+).*"
        tourSetRegChecker = re.compile(tourSetRegex)

        for attraction in attractionBoxs:
            pointName = attraction.css('a::text').extract_first()
            if not tourSetRegChecker.match(pointName):
                attractionUrl = response.urljoin(attraction.css('a::attr(href)').extract_first())
                response.meta['rank'] += 1
                yield response.follow(url = attractionUrl, callback=self.parseAttractionsPage, meta = response.meta)


        nextPageLink = response.css('div.al_border.deckTools.btm > div > div.unified.pagination > a.nav.next.rndBtn.ui_button.primary.taLnk::attr(href)')
        if nextPageLink:
            nextPageLink = response.urljoin(nextPageLink.extract_first())
            self.log("nextpage: " + nextPageLink)
            if response.meta['rank'] < 100:
                yield response.follow(nextPageLink, callback=self.parseCity, meta = response.meta)

    def parseAttractionsPage(self, response: scrapy.http.Response):
        #https://www.tripadvisor.in/Attraction_Review-g186338-d188862-Reviews-National_Gallery-London_England.html
        #breadcrumbs = #response.css('ul.breadcrumbs > li > a > span::text').extract()
        countryName = response.meta['countryName']#breadcrumbs[-3]
        cityName = response.meta['cityName']#breadcrumbs[-2]
        # -2 is the word 'attractions'
        pointName = response.css('ul.breadcrumbs > li::text').extract()[-1]
        # we don't really care about the region once we have the city?

        self.log("visiting " + countryName + " " + cityName + " " + pointName)
        data = response.css('div.text::text').extract()
        description, notes = None, None
        if len(data) > 0:
            description = data[-1]
            description = ''.join(data[-1])


        addressBlock = response.css('div.detail_section.address > span::text')
        address = ''.join(addressBlock.extract())

        if(len(address) == 0):
            address = None
        
        ratingBox = response.css('div.rating')

        avgRating, ratingCount = None, None
        if ratingBox:
            bestRating = 5 #int(ratingAndCountBox.css('div.avgRatingDetail > meta[itemprop="bestRating"]::attr(content)').extract_first())
            worstRating = 1 #int(ratingAndCountBox.css('div.avgRatingDetail > meta[itemprop="worstRating"]::attr(content)').extract_first())
            givenRating = float(ratingBox.css('span.overallRating::text').extract_first().strip())
            ratingCount = int(removeComa(ratingBox.css('a.seeAllReviews::text').extract_first().split(' ')[0]))
            avgRating = scaleRating(givenRating=givenRating, worstRating=worstRating, bestRating=bestRating)
            self.log("ratings: "+ str(avgRating))        

        durationBox = durationRegex.findall(response.text.lower())
        duration = None
        if durationBox:
            duration = durationBox[0]
            # duration = duration.split(';')[-1]
            # duration = duration.split('>')[-1]
            # duration = duration.split('>')[-1]
            # duration = duration.split('-')[-1]

            if(len(duration) == 0):
                duration = None

        phoneBox = response.css('div.detail_section.phone::text')
        phone = None 
        if phoneBox:
            phone = phoneBox.extract_first()
        pointListing = PointListing(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                    countryName=countryName, cityName=cityName, pointName=pointName,
                                    description=description, notes=notes, address=address, rank = response.meta['rank'],contact = phone,
                                    avgRating=avgRating, ratingCount=ratingCount, recommendedNumHours = duration)

        yield pointListing.jsonify()

        Image = response.css('div#topicPhotoGalleryCt.row > div > span > img::attr(src)')
        if Image:
            pointImage = Image.extract_first()
            self.log("imageURL " + pointImage)
            yield ImageResource(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                countryName=countryName, cityName=cityName, pointName=pointName,
                                imageURL=pointImage).jsonify()

        # reviewsBox = response.css('div.wrap')
        # ratings = []
        # for reviewBox in reviewsBox:
        #     ratingBox = reviewBox.css('div.rating.reviewItemInline')
        #     rating = ratingBox.css('span::attr(class)').extract_first()
        #     if rating is not None and len(rating) > 0:
        #         rating = int(rating.split('_')[-1])/10
        #         ratings.append(rating)

        # for i in range(len(reviewsBox)):
        #     ratingDateBox = reviewsBox[i].css('div.rating.reviewItemInline')

        #     reviewDate = ratingDateBox.css('span::attr(title)').extract_first()
        #     description = reviewsBox[i].css('div.entry > p::text').extract_first()
        #     yield Review(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
        #      countryName=countryName, cityName=cityName, pointName=pointName,
        #      content=description, rating=rating, date=reviewDate).jsonify()


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


