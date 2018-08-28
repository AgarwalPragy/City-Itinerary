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
    with open(filePath, 'r') as f:
        citiesAndUrls = f.readlines()

    startingUrls = []
    for cityAndUrl in citiesAndUrls:
        countryName, city, cityURL = cityAndUrl.split('\t')
        cityURL = cityURL.strip()

        print("found:", cityURL)
        urlToCityAndCountryMapping[cityURL] = {
            'city': city,
            'country': countryName}
        startingUrls.append(cityURL)

    return startingUrls


class CrawlerInspirock(scrapy.Spider):
    name = 'inspirock'
    custom_settings = {
        'Accept-Language': 'en'
    }
    start_urls = getStartingUrls()

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
        descriptionBox = response.css('div.desc-in *::text')
        if descriptionBox:
            descriptionList = descriptionBox.extract()
            description = ""
            for desc in descriptionList:
                splited = desc.split("\n")

                for splitedDes in splited:
                    if len(splitedDes.strip()) > 0:
                        description += splitedDes.strip()
            if len(description) == 0:
                description = None 

        ratingAndCountBox = response.css('div.rating > div.ins-rating')
        # ratingBox = sideBox.css('p[itemprop="aggregateRating"]')

        avgRating, ratingCount = None, None
        if ratingAndCountBox:
            bestRating = 5
            worstRating = 1
            givenRating = float(ratingAndCountBox.css('span::text').extract_first())
            avgRating = scaleRating(givenRating=givenRating, worstRating=worstRating, bestRating=bestRating)

        rightBox = response.css('div.attraction-metadata > aside')
        duration, address = None, None
        if rightBox:
            duration = rightBox.css('div::text').extract()[1]
            addressData = rightBox.css('p::text').extract_first().strip()
            if len(addressData) > 0:
                address = addressData + response.meta['city'] + ", " + response.meta['country'] 

        rankBox = response.css('div.rating-count > b::text')
        rank = None

        if rankBox:
            rank = rankBox.extract_first()[1:].strip()
            rank = int(rank)

        self.log('rank: ' + str(rank))

        tagBox = response.css('div.tags-attractions > a::text')

        types = None 
        if tagBox:
            tags = tagBox.extract()
            types = ""
            for tag in tags:
                tag = tag.split('#')[-1]
                if len(tag) > 0:
                    types += tag + ","

            types = types[:-1]
            if len(types) == 0:
                types = None 
            self.log("types: " + types)

        openingsHour, closingsHour = None, None
        openCloseBox = response.css('div.attraction-metadata > aside.opening-hours > div.clearfix > table > tr > td.time::text')

        if openCloseBox:
            self.log("times: "+response.url)
            hours = openCloseBox.extract()
            openingsHour = ''
            closingsHour = ''
            for hour in hours:
                splitter = hour.split('-')
                if len(splitter) == 2:
                    openingsHour += splitter[0].strip() + ','
                    closingsHour += splitter[1].strip() + ','
                else:
                    openingsHour += splitter[0].strip() + ','
                    closingsHour += splitter[0].strip() + ','
            openingsHour = openingsHour[:-1]
            closingsHour = closingsHour[:-1]

        contactBox = response.css('p.phone > a > span::text')
        contact = None
        if contactBox:
            contact = contactBox.extract_first()

        priceBox = response.css('div.attraction-metadata > aside')

        priceLevel = None 
        if priceBox:
            titleChecker = priceBox[-1].css('div.cat-title::text')
            if titleChecker and titleChecker.extract_first().lower() == "price range":
                priceLevel = priceBox.css('p::text').extract_first()



        pointListing = PointListing(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                    countryName=countryName, cityName=cityName, pointName=pointName,
                                    description=description, notes=notes, address=address,priceLevel = priceLevel, contact = contact, 
                                    openingHour=openingsHour, closingHour=closingsHour, recommendedNumHours=duration,category = types,
                                    avgRating=avgRating, ratingCount=ratingCount, rank=rank)

        yield pointListing.jsonify()
        # some problem with loading pics
        pics = response.css('div.photos > div > ul > li > a > img::attr(src)')
    
        if pics:
            pointImages = pics.extract()
            for pointImage in pointImages:
                self.log("imageURL " + pointImage)
                yield ImageResource(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                    countryName=countryName, cityName=cityName, pointName=pointName,
                                    imageURL=pointImage).jsonify()

        googleReviewsBox = response.css('div.reviews > ul > li.greview')

        for googleReviewBox in googleReviewsBox:
            ratingAndDate = googleReviewBox.css('div.review-metadata.clearfix')
            rating = ratingAndDate.css('div.rating-stars.google > span::attr(style)').extract_first().split(':')[-1].strip()[:-2]
            rating = float(rating)/20
            ratingDate = ratingAndDate.css('span.review-date::text').extract_first().split('On')[-1].strip()
            scaledRating = scaleRating(rating, 1, 5)
            description = googleReviewBox.css('div.desc > *::text').extract()
            description = ''.join(description)

            yield Review(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
             countryName=countryName, cityName=cityName, pointName=pointName,
             content=description, rating=scaledRating, date=ratingDate).jsonify()

        #tripadvisor reviews (only 3 are there) are shown in local language so we are not considering these 3 reviews 
        # tripAdvisorReviewsBox = response.css('div#attractionTripReviews.reviews > ul > li')
        # for reviewBox in tripAdvisorReviewsBox:
        #     ratingAndDate = reviewBox.css('div.review-metadata.clearfix')

        #     rating = ratingAndDate.css('div > span::attr(style)').extract_first().split(':')[-1].strip()[:-2]
        #     rating = float(rating)/20
        #     scaledRating = scaleRating(rating, 1, 5)

        #     ratingDate = ratingAndDate.css('span.review-date::text').extract_first().split('On')[-1].strip()

        #     descriptionData = reviewBox.css('blockquote::text').extract_first().split('. ')
        #     description = ""
        #     if(len(descriptionData) == 1):
        #         description = descriptionData[0] + "."
        #     else:
        #         for i in range(len(descriptionData)-1):
        #             if len(descriptionData[i].strip()) > 0:
        #                 description += descriptionData[i] + ". "
        #         description = description[:-2].strip()
    

        #     if(len(description) > 0):
        #         yield Review(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
        #         countryName=countryName, cityName=cityName, pointName=pointName,
        #         content=description, rating=scaledRating, date=ratingDate).jsonify()


