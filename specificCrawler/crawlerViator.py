import scrapy
from entities import *
import datetime


# TODO: Silence (but log) crawling exceptions to prevent crashes
# TODO: Make sure when aggregation is done, values are stripped of whitespace first

def getCurrentTime() -> str:
    strFormat = '%y-%m-%d %H:%M:%S'
    return datetime.datetime.now().strftime(strFormat)


def scaleRating(givenRating: float, worstRating: int, bestRating: int) -> float:
    meanShifted = (givenRating - worstRating + 1)
    range = bestRating - worstRating
    return meanShifted / range


class CrawlerViator(scrapy.Spider):
    name = 'viator'

    start_urls = ['https://www.viator.com/Amsterdam/d525-ttd']

    def parse(self, response: scrapy.http.Response):
        # example page:  https://www.viator.com/Amsterdam/d525-ttd
        countryMenuBox = response.css('#countryMenuBox > div.menu-dropdown-box.small > div > div:nth-child(1)')
        hrefs = countryMenuBox.css('a::attr(durl)').extract()
        for href in hrefs:
            yield response.follow(href, callback=self.parseCountryPage)

    def parseCountryPage(self, response: scrapy.http.Response):
        # example page:  https://www.viator.com/India/d723-ttd
        breadcrumbs = response.css('div.crumbler *> span::text').extract()
        countryName = breadcrumbs[1]

        countryListing = CountryListing(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                        countryName=countryName)
        yield countryListing.jsonify()

        cityMenuBox = response.css('#regionMenuBox > div.menu-dropdown-box.small > div > div:nth-child(1)')
        hrefs = cityMenuBox.css('a')
        for href in hrefs:
            curl = href.css('::attr(durl)').extract_first()
            yield response.follow(curl, callback=self.parseCityPage)

        attractionsPageURL = response.url[:-4]
        yield response.follow(attractionsPageURL, callback=self.parseCountryAttractionsListPage)

    def parseCityPage(self, response: scrapy.http.Response):
        # example page:  https://www.viator.com/Lucknow/d23770-ttd
        breadcrumbs = response.css('div.crumbler *> span::text').extract()
        countryName = breadcrumbs[1]
        if len(breadcrumbs) == 4:
            regionName, cityName = breadcrumbs[2:3]
            regionName = regionName
        else:
            # example page: https://www.viator.com/Mumbai/d953-ttd
            regionName, cityName = None, breadcrumbs[2]
        cityName = cityName

        cityListing = CityListing(crawler=self.name, sourceURL=response.url, crawlTimestamp=getCurrentTime(),
                                  countryName=countryName, cityName=cityName, regionName=regionName)
        yield cityListing.jsonify()

    def parseCountryAttractionsListPage(self, response: scrapy.http.Response):
        # example page:  https://www.viator.com/Netherlands/d60
        hrefs = response.css('div.ptm *> h2 > a::attr(href)').extract()
        for href in hrefs:
            yield response.follow(href, callback=self.parseAttractionsPage)

        nextPageLink = response.css('div.ptm > div:nth-child(1) > div:nth-child(2) > p > a:last-child::attr(href)').extract_first()
        if nextPageLink:
            yield response.follow(nextPageLink, callback=self.parseCountryAttractionsListPage)

    def parseAttractionsPage(self, response: scrapy.http.Response):
        # example page: https://www.viator.com/Amsterdam-attractions/Albert-Cuyp-Market/d525-a8126
        breadcrumbs = response.css('div.crumbler *> span::text').extract()
        countryName = breadcrumbs[1]
        cityName = breadcrumbs[-3]
        # -2 is the word 'attractions'
        pointName = breadcrumbs[-1]
        # we don't really care about the region once we have the city?

        data = response.css('div.cms-content')
        description, notes = None, None
        if len(data) > 0:
            description = data[0]
            description = '\n'.join(description.css('div::text').extract())
        if len(data) > 1:
            notes = data[1].css('::text').extract_first()

        sideBox = response.css('body > div.page.mtl > div.body > div.main-wide.unitRight > div.page-bg.line.light-border-b > div.unitRight.aside > div > div.mtmm.mhmm > div.line > div')
        address = sideBox.css('meta[itemprop="streetAddress"]::attr(content)').extract_first()

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

        pointImage = response.css('div.img-product > img::attr(src)').extract_first()
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
        temp = response.url.split('/')[-1].split('?')[0]
        seoID, destinationID = temp.split('-')
        seoID = seoID[1:]
        destinationID = destinationID[1:]

        firstPageURL = 'https://www.viator.com/ajax-seoReviewsList.jspa?seoId={}&destinationID={}&pageLister.page={}'.format(
            seoID, destinationID, 1
        )

        yield scrapy.Request(firstPageURL, self.parseNextReviewPage, meta=response.meta)

    def parseNextReviewPage(self, response: scrapy.http.Response):
        reviewList = response.css('div[itemprop="review"]')
        for review in reviewList:
            ratingBox = review.css('div[itemprop="reviewRating"]')
            bestRating = int(ratingBox.css('meta[itemprop="bestRating"]::attr(content)').extract_first())
            worstRating = int(ratingBox.css('meta[itemprop="worstRating"]::attr(content)').extract_first())
            givenRating = int(ratingBox.css('div.unit::attr(title)').extract_first()[:1])
            rating = scaleRating(givenRating=givenRating, worstRating=worstRating, bestRating=bestRating)

            ratingDate = ratingBox.css('span::text').extract_first()

            contentBox = review.css('div[itemprop="reviewBody"]')
            content = ''.join(contentBox.css('p::text').extract())

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

