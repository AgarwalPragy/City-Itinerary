from entities import CityID, CountryID, PointID


clientDefaultTripLength = 3  # number of days
clientDefaultStartTime = 9   # hours
clientDefaultEndTime = 20    # hours
clientDefaultCity = 'Mumbai (Bombay), India'
clientMaxPossiblePointsPerDay = 8


matchPointID_countryThreshold = 75
matchPointID_cityThreshold = 85
matchPointID_pointThreshold = 95

avgRecommendedNumHours = 2
avgOpenTime = '9:00 am'
avgCloseTime = '10:00 pm'

mScoreAvgRating = 5         # what to assign when no ratings available
mScoreAvgRatingCount = 10   # how many fake values to put
avgSpeedOfTravel = 25
kMeansPointSelectDisWeight = 12
kMeansPointSelectGScoreWeight = 1

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


_freqScaleFactor = 5
_tripexpertScoreScaleFactor = 100
_categoryTitleScaleFactor = 3
_mScoreScaleFactor = 10

orderWeightOfPolicies = {
    'mayurScore':       10 / _mScoreScaleFactor,
    'category':          9 / _categoryTitleScaleFactor,
    'tripexpertScore':   7 / _tripexpertScoreScaleFactor,
    'rank':              0,
    'frequency':         5 / _freqScaleFactor,
    'wilsonScore':       1,
    'pointAttributes':   1
}

thresholdGoodWordCount = 3
goodWordWeight = 1.5
badWordWeight = -2      # Note: the negation
okayWordWeight = 1
titleWeight = 1.5
categoryWeight = 1
badCategoryTitleWords = list(set(word.strip().lower() for word in [
    'accessories', 'airport',
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
    'Amusement', 'Auditorium', 'attraction',
    'Boat', 'Bridge',
    'camping',  'Climbing',
    'Educational',
    'festival',
    'hall', 'Hiking', 'Helicopter',  'Horse',
    'market',
    'observation',  'Opera',
    'Paragliding', 'Popular',
    'Safari',  'Scuba', 'stadium',
    'Theme', 'trekking', 'tourist',
    'Harbor', 'history',
    'Natural', 'Nature',
    'park',
    'Planetarium',
    'station',
    'Water Body', 'Wildlife',

    # cities names are important
    'Bangkok', 'Seoul', 'London', 'Milan', 'Paris', 'Rome', 'Singapore', 'Shanghai', 'York',
    'Amsterdam', 'Istanbul', 'Tokyo', 'Dubai', 'Vienna', 'Kuala Lumpur', 'Taipei', 'Hong Kong',
    'Riyadh', 'Barcelona', 'Los Angeles', 'Mumbai', 'Delhi', 'Pune', 'Kolkata', 'Agra', 'Jaipur', 'Bengaluru',
    'Bangalore', 'Calcutta'
]))

goodCategoryTitleWords = list(set(word.strip().lower() for word in [
    'aquarium', 'Architectural', 'Art', 'Archaeological',
    'beach', 'botanical', 'bagh',
    'Canyon', 'Castle', 'cave', 'Chapel', 'church', 'City', 'Courthouse', 'cathedral',
    'dam', 'desert', 'Disney', 'Dolphins', 'dargah',
    'Equestrian',
    'Forest', 'fort', 'Fountain',
    'gallery', 'garden', 'Geologic', 'Gondolas',
    'historic',
    'Island', 'island', 'intercontinental',
    'kingdom',
    'lake', 'Library', 'lighthouse',
    'marina', 'marine', 'masjidh', 'monument', 'Mosque', 'Mountain', 'Museum', 'Minar',
    'national',
    'Observatory',
    'palace', 'Pier',
    'Qila',
    'religious', 'river', 'Rock', 'Ruin',
    'Scenic', 'science', 'spring', 'state', 'Statue'
    'temple', 'tower', 'Tomb',
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
    (PointID('India', 'Mumbai', 'IIT B'), PointID('India', 'Mumbai', 'IIT Bombay'))
]

injectedCityAliases = [
    (CityID('USA', 'Los Angeles'), CityID('USA', 'LA')),
    (CityID('USA', 'New York'), CityID('USA', 'NY')),
    (CityID('USA', 'NY'), CityID('USA', 'NYC')),
    (CityID('India', 'Mumbai'), CityID('India', 'Bombay')),
    (CityID('India', 'Calcutta'), CityID('India', 'Kolkata')),
    (CityID('India', 'Bengaluru'), CityID('India', 'Bangalore'))
]

injectedCountryAliases = [
    (CountryID('USA'), CountryID('United States of America')),
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
