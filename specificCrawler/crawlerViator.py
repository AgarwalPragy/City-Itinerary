import scrapy
import sys
sys.path.append('.')

from entities import *
from utilities import *
from requiredPlaces import requiredCountries, requiredCities, processedRequiredCities, processedRequiredCountries

# TODO: Silence (but log) crawling exceptions to prevent crashes
# TODO: Make sure when aggregation is done, values are stripped of whitespace first

skipNonRequired = True
print('RequiredCities', requiredCities)
print('RequiredCountries', requiredCountries)


class CrawlerViator(scrapy.Spider):
    name = 'viator_v2'

    start_urls = ['https://www.viator.com/Amsterdam/d525-ttd']


    requestCount = 0

    def incrementRequestCount(self):
        self.requestCount += 1
        if self.requestCount % 100 == 0:
            time.sleep(1)
        if self.requestCount % 1000 == 0:
            time.sleep(10)
        if self.requestCount % 10000 == 0:
            time.sleep(100)

    def parse(self, response: scrapy.http.Response):
        # example page:  https://www.viator.com/Amsterdam/d525-ttd
        countryMenuBox = response.css('#countryMenuBox > div.menu-dropdown-box.small > div > div:nth-child(1)')
        hrefs = countryMenuBox.css('a::attr(durl)').extract()
        for href in hrefs:
            yield response.follow(href, callback=self.parseCountryPage)

    def parseCountryPage(self, response: scrapy.http.Response):
        # example page:  https://www.viator.com/India/d723-ttd

        self.incrementRequestCount()

        breadcrumbs = response.css('div.crumbler *> span::text').extract()
        countryName = breadcrumbs[1].strip()

        countryListing = CountryListing(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                        countryName=countryName)
        yield countryListing.jsonify()

        if skipNonRequired:
            if processName(countryName) not in processedRequiredCountries:
                # do not process this country's cities
                print('Skipping country: ', countryName)
                return
        countryId = response.url.split('/')[-1].split('-')[0][1:]
        cityListingURL = 'https://www.viator.com/pascities.jspa?country={}'.format(countryId)
        yield response.follow(cityListingURL, callback=self.parseCountryCities, meta={'countryName': countryName})

        # Don't extract attractions from the country page. Instead do it from the city page for better filtering
        # attractionsPageURL = response.url[:-4]
        # yield response.follow(attractionsPageURL, callback=self.parseCountryAttractionsListPage)

    def parseCountryCities(self, response: scrapy.http.Response):
        # example page: https://www.viator.com/pascities.jspa?country=723

        self.incrementRequestCount()

        hrefs = response.css('div.unit.size-pas-cities *> a::attr(durl)').extract()
        for href in hrefs:
            yield response.follow(href, callback=self.parseCityPage, meta=response.meta)

    def parseCityPage(self, response: scrapy.http.Response):
        # example page:  https://www.viator.com/Lucknow/d23770-ttd

        self.incrementRequestCount()
        breadcrumbs = response.css('div.crumbler *> span::text').extract()
        countryName = breadcrumbs[1].strip()
        if countryName != response.meta['countryName']:
            if countryName is None:
                countryName = response.meta['countryName'].strip()
            else:
                self.log('Country name mismatch.\nExpected: {}\nFound: {}'.format(meta['countryName'], countryName))
        if len(breadcrumbs) == 4:
            regionName, cityName = breadcrumbs[2:4]
            cityName = cityName.strip()
            regionName = regionName.strip()
        else:
            # example page: https://www.viator.com/Mumbai/d953-ttd
            regionName, cityName = None, breadcrumbs[2]
            cityName = cityName.strip()

        cityListing = CityListing(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                  countryName=countryName, cityName=cityName, regionName=regionName)
        yield cityListing.jsonify()

        if skipNonRequired:
            if processName(cityName) not in processedRequiredCities:
                # do not process this country's cities
                print('Skipping city: ', countryName, cityName)
                return

        attractionsPageURL = response.url[:-4]
        yield response.follow(attractionsPageURL, callback=self.parseCityAttractionsListPage, meta={
            'countryName': countryName,
            'cityName': cityName,
        })

    def parseCountryAttractionsListPage(self, response: scrapy.http.Response):
        # example page:  https://www.viator.com/Netherlands/d60

        self.incrementRequestCount()
        hrefs = response.css('div.ptm *> h2 > a::attr(href)').extract()
        for href in hrefs:
            yield response.follow(href, callback=self.parseAttractionsPage)

        nextPageLink = response.css('div.ptm > div:nth-child(1) > div:nth-child(2) > p > a:last-child::attr(href)').extract_first()
        if nextPageLink:
            yield response.follow(nextPageLink, callback=self.parseCountryAttractionsListPage)

    def parseCityAttractionsListPage(self, response: scrapy.http.Response):
        # example page:  https://www.viator.com/Mumbai/d953

        self.incrementRequestCount()
        hrefs = response.css('div.ptm *> h2 > a::attr(href)').extract()
        for href in hrefs:
            yield response.follow(href, callback=self.parseAttractionsPage)

        nextPageLink = response.css('div.ptm > div:nth-child(1) > div:nth-child(2) > p > a:last-child::attr(href)').extract_first()
        if nextPageLink:
            yield response.follow(nextPageLink, callback=self.parseCityAttractionsListPage, meta=response.meta)

    def parseAttractionsPage(self, response: scrapy.http.Response):
        # example page: https://www.viator.com/Amsterdam-attractions/Albert-Cuyp-Market/d525-a8126

        self.incrementRequestCount()
        breadcrumbs = response.css('div.crumbler *> span::text').extract()
        countryName = breadcrumbs[1].strip()
        cityName = breadcrumbs[-3].strip()
        # -2 is the word 'attractions'
        pointName = breadcrumbs[-1].strip()
        # we don't really care about the region once we have the city?

        data = response.css('div.cms-content')
        description, notes = None, None
        if len(data) > 0:
            description = data[0]
            description = '\n'.join(description.css('div::text').extract()).strip()
        if len(data) > 1:
            notes = data[1].css('::text').extract_first().strip()

        sideBox = response.css('body > div.page.mtl > div.body > div.main-wide.unitRight > div.page-bg.line.light-border-b > div.unitRight.aside > div > div.mtmm.mhmm > div.line > div')
        address = sideBox.css('meta[itemprop="streetAddress"]::attr(content)').extract_first().strip()

        ratingBox = sideBox.css('p[itemprop="aggregateRating"]')
        avgRating, ratingCount = None, None
        if ratingBox:
            bestRating = int(ratingBox.css('meta[itemprop="bestRating"]::attr(content)').extract_first())
            worstRating = int(ratingBox.css('meta[itemprop="worstRating"]::attr(content)').extract_first())
            givenRating = float(ratingBox.css('meta[itemprop="ratingValue"]::attr(content)').extract_first())
            ratingCount = int(ratingBox.css('span[itemprop="reviewCount"]::text').extract_first())
            avgRating = scaleRating(givenRating=givenRating, worstRating=worstRating, bestRating=bestRating)

        pointListing = PointListing(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                    countryName=countryName, cityName=cityName, pointName=pointName,
                                    description=description, notes=notes, address=address,
                                    avgRating=avgRating, ratingCount=ratingCount)

        yield pointListing.jsonify()

        pointImage = response.css('div.img-product > img::attr(src)').extract_first().strip()
        yield ImageResource(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                            countryName=countryName, cityName=cityName, pointName=pointName,
                            imageURL=pointImage).jsonify()

        yield response.follow('?subPageType=reviews', callback=self.parseReviewsPage, meta={
            'countryName': countryName,
            'cityName': cityName,
            'pointName': pointName
        })

    def parseReviewsPage(self, response: scrapy.http.Response):
        # example page: https://www.viator.com/New-Delhi-attractions/Taj-Mahal/d804-a3010?subPageType=reviews

        # This page is infinite scrolling
        # dynamically loads content from an API of the following url format
        # https://www.viator.com/ajax-seoReviewsList.jspa?seoId=3010&destinationID=804&pageLister.page=6

        # simply get the d-id and seoID and destinationID from the URL and get the reviews

        self.incrementRequestCount()
        temp = response.url.split('/')[-1].split('?')[0]
        seoID, destinationID = temp.split('-')
        seoID = seoID[1:]
        destinationID = destinationID[1:]

        firstPageURL = 'https://www.viator.com/ajax-seoReviewsList.jspa?seoId={}&destinationID={}&pageLister.page={}'.format(
            seoID, destinationID, 1
        )

        yield scrapy.Request(firstPageURL, self.parseNextReviewPage, meta=response.meta)

    def parseNextReviewPage(self, response: scrapy.http.Response):

        self.incrementRequestCount()
        reviewList = response.css('div[itemprop="review"]')
        for review in reviewList:
            ratingBox = review.css('div[itemprop="reviewRating"]')
            bestRating = int(ratingBox.css('meta[itemprop="bestRating"]::attr(content)').extract_first())
            worstRating = int(ratingBox.css('meta[itemprop="worstRating"]::attr(content)').extract_first())
            givenRating = int(ratingBox.css('div.unit::attr(title)').extract_first()[:1])
            rating = scaleRating(givenRating=givenRating, worstRating=worstRating, bestRating=bestRating)

            ratingDate = ratingBox.css('span::text').extract_first()

            contentBox = review.css('div[itemprop="reviewBody"]')
            content = ''.join(contentBox.css('p::text').extract()).strip()

            yield Review(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                         countryName=response.meta['countryName'], cityName=response.meta['cityName'], pointName=response.meta['pointName'],
                         content=content, rating=rating, date=ratingDate).jsonify()

        if len(reviewList) == 25:
            # there might be more reviews on the next page. This api returns 25 items at a time
            queryString = response.url.split('=')
            index = int(queryString[-1])
            queryString[-1] = str(index+1)
            nextPageURL = '='.join(queryString)
            # TODO: uncomment the below line to continue processing the other reviews
            # for now, we just need the first page.
            # yield scrapy.Request(nextPageURL, self.parseNextReviewPage)

