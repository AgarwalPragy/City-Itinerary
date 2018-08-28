import typing as t
from collections import defaultdict
from tqdm import tqdm
from operator import attrgetter, itemgetter
import json
import os
import errno


from jsonUtils import J, EnhancedJSONEncoder
from aggregatorLogic import *
from utilities import doesFuzzyMatch, UnionFind, tree, processName, getCurrentTime
from entities import JEL, JKL, JCL, JPL, CityID, CountryID, PointID
from tunable import matchPointID_countryThreshold, matchPointID_cityThreshold, matchPointID_pointThreshold, injectedPointAliases, injectedCityAliases, injectedCountryAliases, orderBasedOn, fullConfig


ID = t.Union[CountryID, CityID, PointID]


def saveData(filename, data: t.Any) -> None:
    # https://stackoverflow.com/questions/12517451/automatically-creating-directories-with-file-output
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    print('saving to', filename)
    with open(filename, 'w') as f:
        f.write(json.dumps(data, cls=EnhancedJSONEncoder))


def readListingsFromFiles(filenames: t.List[str]) -> t.List[JEL]:
    data: t.List[JEL] = []
    print('Reading files.')
    for filename in filenames:
        with open(filename, 'r') as f:
            data += json.loads(f.read())
        print('Read:', filename)
    return data


def extractPointID(identifier: t.Union[PointID]) -> PointID:
    return PointID(identifier.countryName, identifier.cityName, identifier.pointName)


def extractCityID(identifier: t.Union[PointID, CityID]) -> CityID:
    return CityID(identifier.countryName, identifier.cityName)


def extractCountryID(identifier: t.Union[PointID, CityID, CountryID]) -> CountryID:
    return CountryID(identifier.countryName)


def getPointID(point: t.Union[JPL]) -> PointID:
    return PointID(point['countryName'], point['cityName'], point['pointName'])


def getCityID(city: t.Union[JCL, JPL]) -> CityID:
    return CityID(city['countryName'], city['cityName'])


def getCountryID(country: t.Union[JKL, JCL, JPL]) -> CountryID:
    return CountryID(country['countryName'])


def getID(entity: JEL) -> ID:
    myID: ID
    if entity['_listingType'] == 'point': myID = getPointID(JPL(entity))
    if entity['_listingType'] == 'city': myID = getCityID(JCL(entity))
    if entity['_listingType'] == 'country': myID = getCountryID(JKL(entity))
    return myID


def forPoint(entity: JEL) -> bool:
    return entity['countryName'] and entity['cityName'] and entity['pointName']


def forCity(entity: JEL) -> bool:
    return entity['countryName'] and entity['cityName'] and not entity['pointName']


def forCountry(entity: JEL) -> bool:
    return entity['countryName'] and not entity['cityName'] and not entity['pointName']


def matchPointIDs(pointID1: PointID, pointID2: PointID) -> bool:
    # TODO: tune this
    if doesFuzzyMatch(pointID1.countryName, pointID2.countryName, matchPointID_countryThreshold):
        if doesFuzzyMatch(pointID1.cityName, pointID2.cityName, matchPointID_cityThreshold):
            if doesFuzzyMatch(pointID1.pointName, pointID2.pointName, matchPointID_pointThreshold):
                return True
    return False


def clusterAllIDs(pointIDs: t.List[PointID], cityIDs: t.List[CityID], countryIDs: t.List[CountryID]) -> t.Tuple[t.Dict[PointID, PointID], t.Dict[CityID, CityID], t.Dict[CountryID, CountryID]]:
    """Intelligently Identifies NameClusterMaps for countries, cities and points considered together"""
    # Usecase:
    #     India/Raipur vs India/Rampur
    #     can be Identified by the POIs that are present in the two cities
    print('Collecting all aliases')
    allPointAliases: t.Set[PointID] = set(pointIDs) | set(map(itemgetter(0), injectedPointAliases)) | set(map(itemgetter(1), injectedPointAliases))
    allCityAliases: t.Set[CityID] = set(cityIDs) | set(map(extractCityID, allPointAliases)) | set(map(itemgetter(0), injectedCityAliases)) | set(map(itemgetter(1), injectedCityAliases))
    allCountryAliases: t.Set[CountryID] = set(countryIDs) | set(map(extractCountryID, allPointAliases)) | set(map(extractCountryID, allCityAliases)) | set(map(itemgetter(0), injectedCountryAliases)) | set(map(itemgetter(1), injectedCountryAliases))
    pointIDs = sorted(list(allPointAliases))

    print('Found {} country aliases'.format(len(allCountryAliases)))
    print('Found {} city aliases'.format(len(allCityAliases)))
    print('Found {} point aliases'.format(len(allPointAliases)))

    # if 2 names match, club them
    print('Matching point identifiers')
    chosenAlready = [False] * len(pointIDs)
    pointIDUnions: UnionFind[PointID] = UnionFind()
    for index1, alias1 in enumerate(tqdm(pointIDs)):
        if chosenAlready[index1]:
            continue
        chosenAlready[index1] = True
        for index2, alias2 in enumerate(pointIDs[index1 + 1:], index1 + 1):
            if chosenAlready[index2]:
                continue

            if matchPointIDs(alias1, alias2):
                pointIDUnions.union(alias1, alias2)
                chosenAlready[index2] = True
    print('Injecting point aliases')
    for alias1, alias2 in injectedPointAliases:
        pointIDUnions.union(alias1, alias2)

    print('Matching city identifiers')
    cityIDUnions: UnionFind[CityID] = UnionFind()
    for pointAlias in pointIDs:
        root = pointIDUnions[pointAlias]
        rootCity = extractCityID(root)
        cityAlias = extractCityID(pointAlias)
        if rootCity == cityAlias:
            continue
        cityIDUnions.union(rootCity, cityAlias)
    print('Injecting city aliases')
    for cityAlias1, cityAlias2 in injectedCityAliases:
        cityIDUnions.union(cityAlias1, cityAlias2)

    print('Matching country identifiers')
    countryIDUnions: UnionFind[CountryID] = UnionFind()
    for pointAlias in pointIDs:
        root = pointIDUnions[pointAlias]
        countryAlias = extractCountryID(pointAlias)
        rootCountry = extractCountryID(root)
        if rootCountry == countryAlias:
            continue
        countryIDUnions.union(rootCountry, countryAlias)
    print('Injecting country aliases')
    for countryAlias1, countryAlias2 in injectedCountryAliases:
        countryIDUnions.union(countryAlias1, countryAlias2)
    # -----------------------------------------------------------------------------

    print('Building alias to bestName maps')
    countryAliasMap: t.Dict[CountryID, t.List[CountryID]] = defaultdict(list)
    for countryAlias in allCountryAliases:
        countryAliasMap[countryIDUnions[countryAlias]].append(countryAlias)

    bestCountryIDMap: t.Dict[CountryID, CountryID] = {}
    for clubbedCountryAliases in countryAliasMap.values():
        countryNames = list(map(attrgetter('countryName'), clubbedCountryAliases))
        bestCountryID = CountryID(getBestName(countryNames))
        for countryAlias in clubbedCountryAliases:
            bestCountryIDMap[countryAlias] = bestCountryID

    cityAliasMap: t.Dict[CityID, t.List[CityID]] = defaultdict(list)
    for cityAlias in allCityAliases:
        cityAliasMap[cityIDUnions[cityAlias]].append(cityAlias)

    bestCityIDMap: t.Dict[CityID, CityID] = {}
    for clubbedCityAliases in cityAliasMap.values():
        bestCountryName = bestCountryIDMap[extractCountryID(clubbedCityAliases[0])].countryName
        cityNames = list(map(attrgetter('cityName'), clubbedCityAliases))
        bestCityID = CityID(bestCountryName, getBestName(cityNames))
        for cityAlias in clubbedCityAliases:
            bestCityIDMap[cityAlias] = bestCityID

    pointAliasMap: t.Dict[PointID, t.List[PointID]] = defaultdict(list)
    for pointAlias in allPointAliases:
        pointAliasMap[pointIDUnions[pointAlias]].append(pointAlias)

    bestPointIDMap: t.Dict[PointID, PointID] = {}
    for clubbedPointAliases in pointAliasMap.values():
        bestCityID = bestCityIDMap[extractCityID(clubbedPointAliases[0])]
        pointNames = list(map(attrgetter('pointName'), clubbedPointAliases))
        bestPointID = PointID(bestCityID.countryName, bestCityID.cityName, getBestName(pointNames))
        for pointAlias in clubbedPointAliases:
            bestPointIDMap[pointAlias] = bestPointID

    return bestPointIDMap, bestCityIDMap, bestCountryIDMap


def safeAppend(dataset, location, value):
    if location not in dataset:
        dataset[location] = []
    if value:
        dataset[location].append(value)


def collectAllListings(listings: t.List[JEL],
                       bestPointIDMap: t.Dict[PointID, PointID],
                       bestCityIDMap: t.Dict[CityID, CityID],
                       bestCountryIDMap: t.Dict[CountryID, CountryID]) -> J:
    print('Collecting all listings')
    data: J = tree()
    for datum in listings:
        if datum['_listingType'] == 'country':
            countryName = bestCountryIDMap[getCountryID(datum)].countryName
            safeAppend(data[countryName], 'listings', datum)
        elif datum['_listingType'] == 'city':
            countryName, cityName = bestCityIDMap[getCityID(datum)]
            safeAppend(data[countryName]['cities'][cityName], 'listings', datum)
        elif datum['_listingType'] == 'point':
            countryName, cityName, pointName = bestPointIDMap[getPointID(datum)]
            safeAppend(data[countryName]['cities'][cityName]['points'][pointName], 'listings', datum)
        elif datum['_listingType'] == 'imageResource':
            if forPoint(datum):
                countryName, cityName, pointName = bestPointIDMap[getPointID(datum)]
                datum = fixEntityNames(datum, countryName=countryName, cityName=cityName, pointName=pointName)
                safeAppend(data[countryName]['cities'][cityName]['points'][pointName], 'images', datum)
            elif forCity(datum):
                countryName, cityName = bestCityIDMap[getCityID(datum)]
                datum = fixEntityNames(datum, countryName=countryName, cityName=cityName)
                safeAppend(data[countryName]['cities'][cityName], 'images', datum)
            elif forCountry(datum):
                countryName = bestCountryIDMap[getCountryID(datum)].countryName
                datum = fixEntityNames(datum, countryName=countryName)
                safeAppend(data[countryName], 'images', datum)
        elif datum['_listingType'] == 'review':
            if forPoint(datum):
                countryName, cityName, pointName = bestPointIDMap[getPointID(datum)]
                datum = fixEntityNames(datum, countryName=countryName, cityName=cityName, pointName=pointName)
                safeAppend(data[countryName]['cities'][cityName]['points'][pointName], 'reviews', datum)
            elif forCity(datum):
                countryName, cityName = bestCityIDMap[getCityID(datum)]
                datum = fixEntityNames(datum, countryName=countryName, cityName=cityName)
                safeAppend(data[countryName]['cities'][cityName], 'reviews', datum)
            elif forCountry(datum):
                countryName = bestCountryIDMap[getCountryID(datum)].countryName
                datum = fixEntityNames(datum, countryName=countryName)
                safeAppend(data[countryName], 'reviews', datum)

    print('Sanitizing all listings')
    for countryName, country in data.items():
        safeAppend(data[countryName], 'images', None)
        safeAppend(data[countryName], 'reviews', None)
        safeAppend(data[countryName], 'listings', None)
        if 'cities' not in data[countryName]:
            data[countryName]['cities'] = {}
        for cityName, city in country['cities'].items():
            safeAppend(data[countryName]['cities'][cityName], 'images', None)
            safeAppend(data[countryName]['cities'][cityName], 'reviews', None)
            safeAppend(data[countryName]['cities'][cityName], 'listings', None)
            if 'points' not in data[countryName][cityName]:
                data[countryName][cityName]['points'] = {}
            for pointName, point in city['points'].items():
                safeAppend(data[countryName]['cities'][cityName]['points'][pointName], 'images', None)
                safeAppend(data[countryName]['cities'][cityName]['points'][pointName], 'reviews', None)
                safeAppend(data[countryName]['cities'][cityName]['points'][pointName], 'listings', None)

    return data


def fixEntityNames(entity, countryName=None, cityName=None, pointName=None):
    if countryName:
        entity['countryName'] = countryName
    if cityName:
        entity['cityName'] = cityName
    if pointName:
        entity['pointName'] = pointName
    return entity


def frontAndBack(items):
    return list(set(processName(''.join(alias)) for alias in items) | set(processName(''.join(alias[::-1])) for alias in items))


def aggregateAllListings(data: J, revPoint, revCity, revCountry) -> J:
    print('Aggregating data')
    categoriesFound = set()
    aggregated = tree()
    countryCount, cityCount, pointCount, imageCount, reviewCount = 0, 0, 0, 0, 0
    for countryName, country in data.items():
        aggregatedCountry = aggregated[countryName]
        bestCountryID = CountryID(countryName)
        aggregatedCountry['countryAliases'] = frontAndBack(revCountry[bestCountryID] + [bestCountryID])

        if not country['cities']:
            aggregatedCountry['cities'] = {}
        for cityName, city in country['cities'].items():
            aggregatedCity = aggregatedCountry['cities'][cityName]
            bestCityID = CityID(countryName, cityName)
            aggregatedCity['fullName'] = ', '.join(bestCityID[::-1])
            aggregatedCity['cityAliases'] = frontAndBack(revCity[bestCityID] + [bestCityID])
            aggregatedCity['countryAliases'] = aggregatedCountry['countryAliases']

            if not city['points']:
                aggregatedCity['points'] = {}
            points = []
            for pointName, point in city['points'].items():
                aggregatedPoint = aggregatedCity['points'][pointName]
                bestPointID = PointID(countryName, cityName, pointName)
                aggregatedPoint['fullName'] = ', '.join(bestPointID[::-1])
                aggregatedPoint['pointAliases'] = frontAndBack(revPoint[bestPointID] + [bestPointID])
                aggregatedPoint['cityAliases'] = aggregatedCity['cityAliases']
                aggregatedPoint['countryAliases'] = aggregatedCountry['countryAliases']

                if not point['listings']:
                    print('No listings found, but reviews/images exist for the point:', bestPointID)
                finalPoint = aggregateOnePointFromListings(point['listings'], countryName, cityName, pointName)
                points.append(finalPoint)
                for attrib, val in finalPoint.jsonify().items():
                    aggregatedPoint[attrib] = val
                aggregatedPoint['images'] = orderImages(point['images'])
                aggregatedPoint['reviews'] = orderReviews(point['reviews'])
                category = aggregatedPoint['category']
                if category and category.strip():
                    categoriesFound |= set(cat.strip() for cat in category.split(','))

                pointCount += 1
                imageCount += len(point['images'])
                reviewCount += len(point['reviews'])

            finalCity = aggregateOneCityFromListings(city['listings'], countryName, cityName)
            for attrib, val in finalCity.jsonify().items():
                aggregatedCity[attrib] = val
            orderedPoints = orderPointsOfCity(points)
            aggregatedCity['pointsOrder'] = list(map(attrgetter('pointName'), orderedPoints))
            aggregatedCity['images'] = orderImages(city['images'])
            aggregatedCity['reviews'] = orderReviews(city['reviews'])
            cityCount += 1
            imageCount += len(city['images'])
            reviewCount += len(city['reviews'])

        finalCountry = aggregateOneCountryFromListings(country['listings'], countryName)
        for attrib, val in finalCountry.jsonify().items():
            aggregatedCountry[attrib] = val
        aggregatedCountry['images'] = orderImages(country['images'])
        aggregatedCountry['reviews'] = orderReviews(country['reviews'])
        countryCount += 1
        imageCount += len(country['images'])
        reviewCount += len(country['reviews'])

    print('Finally extracted {} countries'.format(countryCount))
    print('Finally extracted {} cities'.format(cityCount))
    print('Finally extracted {} points'.format(pointCount))
    print('Finally extracted {} images'.format(imageCount))
    print('Finally extracted {} reviews'.format(reviewCount))
    return aggregated, categoriesFound


def makeReverseMap(mapping):
    revMapping = defaultdict(list)
    for alias, best in mapping.items():
        revMapping[best].append(alias)
    return revMapping


def processAll():
    listings: t.List[JEL] = readListingsFromFiles([
        '../data/injectedData/countryFlags.json',
        '../data/tripexpertData/cities.json',
        '../data/tripexpertData/tripexpert_requiredcities.json',
        '../data/viatorData/viator_requiredcities.json',
        '../data/inspirockData/finalInspirock.json',
        '../data/skyscannerData/finalSkyscanner.json'
    ])

    print('Processing.')

    countryListings: t.List[JKL] = [JKL(listing) for listing in listings if listing['_listingType'] == 'country']
    cityListings: t.List[JCL] = [JCL(listing) for listing in listings if listing['_listingType'] == 'city']
    pointListings: t.List[JPL] = [JPL(listing) for listing in listings if listing['_listingType'] == 'point']

    pointIDs: t.List[PointID] = [getPointID(point) for point in pointListings]
    cityIDs: t.List[CityID] = [getCityID(city) for city in cityListings]
    countryIDs: t.List[CountryID] = [getCountryID(country) for country in countryListings]

    for listing in listings:
        if listing['_listingType'] in ['review', 'imageResource']:
            if forCountry(listing):
                countryIDs.append(getCountryID(listing))
            elif forCity(listing):
                cityIDs.append(getCityID(listing))
            elif forPoint(listing):
                pointIDs.append(getPointID(listing))

    # TODO: save these mappings so that fuzzy search queries can be answered
    # TODO: check why Amsterdam, Milan don't show up
    bestPointIDMap, bestCityIDMap, bestCountryIDMap = clusterAllIDs(pointIDs, cityIDs, countryIDs)
    revPoint, revCity, revCountry = map(makeReverseMap, [bestPointIDMap, bestCityIDMap, bestCountryIDMap])

    toAggregatedData = collectAllListings(listings, bestPointIDMap, bestCityIDMap, bestCountryIDMap)
    aggregatedListings, categoriesFound = aggregateAllListings(toAggregatedData, revPoint, revCity, revCountry)

    for timestamp in [getCurrentTime(), 'latest']:
        print('Saving results')
        saveData('../aggregatedData/{}/data.json'.format(timestamp), aggregatedListings)
        print('Saving config')
        saveData('../aggregatedData/{}/config.json'.format(timestamp), fullConfig)

        print('Saving debug info')
        debugInfo = {
            'bestPointIDMap': {str(key): str(val) for key, val in bestPointIDMap.items()},
            'bestCityIDMap': {str(key): str(val) for key, val in bestCityIDMap.items()},
            'bestCountryIDMap': {str(key): str(val) for key, val in bestCountryIDMap.items()},
            'toAggregatedData': toAggregatedData,
            'categoriesFound': list(categoriesFound)
        }
        for key, val in debugInfo.items():
            saveData('../aggregatedData/{}/debug/{}.json'.format(timestamp, key), val)

    print('All done. Exit')


if __name__ == '__main__':
    processAll()
