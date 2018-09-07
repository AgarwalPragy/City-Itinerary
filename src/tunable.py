from entities import CityID, CountryID, PointID


clientDefaultTripLength = 4  # number of days
clientDefaultStartTime = 9   # hours
clientDefaultEndTime = 20    # hours
clientDefaultCity = 'Mumbai (Bombay), India'
clientMaxPossiblePointsPerDay = 8

maxCityRadius = 100  # in KM

stopWords = list(map(lambda x: x.lower(), [' and ', 'the ', ' & ', '\'s ']))
synonyms = [
    ('dargah', 'mosque'),
    ('darga', 'mosque'),
    ('masjidh', 'mosque'),
    ('bagh', 'garden'),
    ('qila', 'fort'),
    ('quila', 'fort')
]

matchPointID_countryThreshold = 75
matchPointID_cityThreshold = 85
matchPointID_pointThreshold = 95

avgRecommendedNumHours = 2
avgOpenTime = '9:00 am'
avgCloseTime = '10:00 pm'

mScoreAvgRating = 5         # what to assign when no ratings available
mScoreAvgRatingCount = 800   # how many fake values to put
avgSpeedOfTravel = 25
pointAvgRank = 50
avgTripExpertScore = 70

pointAttributeWeights = {
    'coordinates': 0.35,
    'address': 0.25,
    'openingHour': 0.15,
    'closingHour': 0.15,
    'category': 0.1
}

indexToOrderPolicy = {
    0: 'frequency',
    1: 'weightedAvgRating',
    2: 'wilsonScore',
    3: 'frequencyWithWDomainRanking',
    4: 'mayurScore',
    5: 'weightedOverDiffPolicies'
}

pointGratificationBasedOn = indexToOrderPolicy[5]


_freqScaleFactor = 6
_tripexpertScoreScaleFactor = 100
_categoryTitleScaleFactor = 7
_mScoreScaleFactor = 10
_rankScaleFactor = 500
_old_freqWithDomainRankingScaleFactor = 1000

orderWeightOfPolicies = {
    'mayurScore':            2 / _mScoreScaleFactor,
    'category':              1 / _categoryTitleScaleFactor,
    'tripexpertScore':       1 / _tripexpertScoreScaleFactor,
    'frequency':             1 / _freqScaleFactor,
    'rank':                  0 / _rankScaleFactor,
    'wilsonScore':           0,
    'pointAttributes':       0,
}

thresholdGoodWordCount = 6
goodWordWeight = 2
badWordWeight = -1      # Note: the negation
okayWordWeight = 2
titleWeight = 1.5
categoryWeight = 1
badCategoryTitleWords = list(set(word.strip().lower() for word in [
    'accessories', 'airport', 'Sulabh',
    'bar', 'Beer',
    'cafe', 'Casino', 'Clothing', 'club', 'Cocktail', 'company', 'Cosmetics',
    'drink', 'Drugstore',
    'factory', 'food', 'furniture',
    'Gourmet', 'Grocery', 'gym',
    'Hair', 'Hospital', 'hotel',
    'Jewelry', 'Jogging Path',
    'marijuana', 'mall',
    'Office', 'outlet',
    'Pharmacy', 'Private', 'Pub',
    'rental', 'restaurant', 'restautrant',
    'Salon', 'shop', 'Spa', 'Speakeasy', 'Startup', 'store', 'Supplies', 'shopping',
    'Theater', 'tour', 'Tours', 'Terminus', 'Toilet',
    'Whisky', 'Wine', 'Workshop'
]))

okayCategoryTitleWords = list(set(word.strip().lower() for word in [
    'Amusement', 'aquarium', 'art', 'attraction', 'Auditorium',
    'Boat', 'Bridge',
    'camping', 'church', 'Climbing',
    'Disney', 'Dolphins',
    'Educational',
    'festival', 'Fountain',
    'gallery', 'garden',
    'hall', 'Harbor', 'Helicopter', 'Hiking', 'history', 'Horse',
    'Library',
    'market',
    'Natural', 'Nature',
    'observation', 'Opera',
    'Paragliding', 'park', 'Planetarium', 'Popular',
    'Safari', 'Scuba', 'sight', 'stadium', 'station',
    'Theme', 'tourist', 'trekking',
    'Water Body', 'Wildlife',
    # cities names are important
    # 'Bangkok', 'Seoul', 'London', 'Milan', 'Paris', 'Rome', 'Singapore', 'Shanghai', 'York',
    # 'Amsterdam', 'Istanbul', 'Tokyo', 'Dubai', 'Vienna', 'Kuala Lumpur', 'Taipei', 'Hong Kong',
    # 'Riyadh', 'Barcelona', 'Los Angeles', 'Mumbai', 'Delhi', 'Pune', 'Kolkata', 'Agra', 'Jaipur', 'Bengaluru',
    # 'Bangalore', 'Calcutta'
]))

goodCategoryTitleWords = list(set(word.strip().lower() for word in [
    'Archaeological', 'Architectural',
    'botanical', 'Buckingham Palace', 'beach', 'burj khalifa',
    'Canyon', 'Castle', 'cathedral', 'cave', 'Chapel', 'City', 'Courthouse',
    'dam', 'desert',
    'Equestrian',
    'Forest',
    'fort',
    'Geologic', 'Gondolas', 'gate'
    'historic',
    'intercontinental', 'Island',
    'kingdom',
    'lake', 'lighthouse',
    'marina', 'marine', 'Minar', 'monument', 'Mosque', 'Mountain', 'Museum', 'marine drive',
    'national',
    'Observatory',
    'palace', 'Palm Jumeirah', 'Pier',
    'religious', 'river', 'Rock', 'Ruin',
    'Scenic', 'summer palace', 'scenic drive', 'science', 'spring', 'state', 'Statue'
    'temple', 'top of rock', 'Tomb', 'tower',
    'University',
    'Valley',
    'waterfall',
    'Zoo',
    # country names are really freaking important
    'Thailand', 'Korea', 'England', 'United Kingdom', 'Italy', 'France', 'Singapore', 'China', 'USA',
    'America', 'United States', 'Netherlands', 'Netherlands', 'Turkey', 'Japan',
    'United Arab Emirates', 'UAE', 'Austria', 'Malaysia', 'Taiwan', 'China', 'Spain', 'Saudi Arabia', 'Arabia', 'India'
]))


injectedPointAliases = [
    (PointID('India', 'Mumbai', 'Indian Institute of Technology Bombay'), PointID('India', 'Mumbai', 'IIT Bombay')),
    (PointID('India', 'Mumbai', 'IIT B'), PointID('India', 'Mumbai', 'IIT Bombay')),
    (PointID('India', 'Mumbai', 'InterContinental Marine Drive'), PointID('India', 'Mumbai', 'Marine Drive (Queen’s Necklace)')),
    (PointID('India', 'Jaipur', 'Palace of the Winds'), PointID('India', 'Jaipur', 'Hawa Mahal')),
    (PointID('India', 'Mumbai', 'Shree Siddhivinayak'), PointID('India', 'Mumbai', 'Siddhivinayak Temple')),
]

injectedCityAliases = [
    (CityID('USA', 'Los Angeles'), CityID('USA', 'LA')),
    (CityID('USA', 'New York'), CityID('USA', 'NY')),
    (CityID('USA', 'New York'), CityID('US', 'NY')),
    (CityID('US', 'New York'), CityID('US', 'NY')),
    (CityID('US', 'New York City'), CityID('US', 'New York')),
    (CityID('United States', 'New York City'), CityID('US', 'NY')),
    (CityID('United States of America', 'New York'), CityID('US', 'NY')),
    (CityID('United States', 'New York City'), CityID('USA', 'New York')),

    (CityID('USA', 'NY'), CityID('USA', 'NYC')),
    (CityID('US', 'NY'), CityID('USA', 'NYC')),
    (CityID('USA', 'NYC'), CityID('USA', 'New York City')),
    (CityID('India', 'Mumbai'), CityID('India', 'Bombay')),
    (CityID('India', 'Mumbai'), CityID('India', 'Mumbai (Bombay)')),
    (CityID('India', 'Calcutta'), CityID('India', 'Kolkata')),
    (CityID('India', 'Bengaluru'), CityID('India', 'Bangalore'))
]

injectedBestNames = {
    'Intercontinental Marine Drive': 'Marine Drive',
    'California': 'United States of America',
    'Great Britain': 'United Kingdom',
}

injectedCountryAliases = [
    (CountryID('USA'), CountryID('United States of America')),
    (CountryID('USA'), CountryID('California')),   # Los Angeles seems to be listed both under USA and California (even though California is in USA)
    (CountryID('USA'), CountryID('United States')),
    (CountryID('USA'), CountryID('US')),
    (CountryID('USA'), CountryID('America')),
    (CountryID('UK'), CountryID('United Kingdom')),
    (CountryID('UK'), CountryID('England')),
    (CountryID('UK'), CountryID('Britain')),
    (CountryID('UK'), CountryID('Great Britain')),
    (CountryID('UAE'), CountryID('United Arab Emirates')),
    (CountryID('Afganistan'), CountryID('Āfùhàn')),
    (CountryID('Afghanistan'), CountryID('Afganistan')),
    (CountryID('British Honduras'), CountryID('Belize')),
    (CountryID('Burma'), CountryID('Myanmar')),
    (CountryID('Suomi'), CountryID('Finland'))

    # Note: The following are useful aliases, but will mess up with the bestName
    # TODO: find a way to force a bestName
    # (CountryID('Kampuchea'), CountryID('Democratic Kampuchea')),
    # (CountryID('Cambodia'), CountryID('Democratic Kampuchea')),
    # (CountryID('Cathay'), CountryID('China')),
    # (CountryID('Catay'), CountryID('China')),
    # (CountryID('Katai'), CountryID('China')),
    # (CountryID('Zhongguo'), CountryID('China')),
    # (CountryID('People\'s Republic of China'), CountryID('China')),
    # (CountryID('Nippon'), CountryID('Japan')),
    # (CountryID('Nihon'), CountryID('Japan')),
    # (CountryID('Deutschland'), CountryID('Germany')),
    # (CountryID('Federal Republic of Germany'), CountryID('Germany')),
    # (CountryID('Iran'), CountryID('Persia')),
    # (CountryID('India'), CountryID('Hindustan')),
    # (CountryID('Iran'), CountryID('Islamic Republic of Iran'))
]

fullConfig = {item: globals()[item] for item in dir() if not item.startswith("__") and item not in ['CityID', 'CountryID', 'PointID', 'defaultdict', 'json']}

distanceOverEstimatorFactor =  1.7
weightOfMaxGscoreClusterSelection = 1
weightOfAvgGscoreClusterSelection = 1
weightOfNumPointsClusterSelection = 0.15

weightOfDistancePointSelection = 3
weightOfGscorePointSelection = 2

outlierSelectionThreshold = 3
distanceThresholdToRejectPoint = 100

pFactorLess = 4
pFactorMore = 10