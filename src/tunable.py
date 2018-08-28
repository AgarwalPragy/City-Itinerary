from entities import CityID, CountryID, PointID

matchPointID_countryThreshold = 75
matchPointID_cityThreshold = 85
matchPointID_pointThreshold = 95

avgRecommendedNumHours = 2
avgOpenTime = '9:00 am'
avgCloseTime = '10:00 pm'

mScoreAvgRatingCount = 10
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

orderWeightOfPolicies = {
    'frequency': 0.2,
    'rank': 0.1,
    'wilsonScore': 0.1,
    'mayurScore': 0.1,
    'pointAttributes': 0.1,
    'tripexpertScore': 0.1,
    'category': 0.3
}

orderBasedOn = indexToOrderPolicy[5]

goodWordWeight = 2
badWordWeight = 1
badCategoryTitleWords = list(set(word.strip().lower() for word in [
    'accessories',
    'bar', 'Beer',
    'cafe', 'Casino', 'Clothing', 'club', 'Cocktail', 'company', 'Cosmetics',
    'drink', 'Drugstore',
    'factory', 'food', 'furniture',
    'Gourmet', 'Grocery', 'gym',
    'Hair', 'Hospital', 'hotel',
    'Jewelry', 'Jogging Path',
    'marijuana',
    'Office', 'outlet',
    'Pharmacy', 'Private', 'Pub',
    'rental', 'restaurant', 'restautrant',
    'Salon', 'shop', 'Spa', 'Speakeasy', 'Startup', 'store', 'Supplies',
    'Theater', 'tour', 'Tours',
    'Whisky', 'Wine', 'Workshop'
]))
goodCategoryTitleWords = list(set(word.strip().lower() for word in [
    'Amusement', 'aquarium''Architectural', 'Art', 'attraction', 'Auditorium',
    'beach', 'Boat', 'botanical', 'Bridge',
    'camping', 'Canyon', 'Castle', 'cave', 'Cave', 'Chapel', 'church', 'City', 'Climbing', 'Courthouse',
    'dam', 'desert', 'Disney', 'Dolphins',
    'Educational', 'Equestrian',
    'festival', 'Forest', 'fort', 'Fountain',
    'gallery', 'garden', 'Geologic', 'Gondolas',
    'hall', 'Harbor', 'Helicopter', 'Hiking', 'historic', 'history', 'Horse',
    'Island', 'island',
    'lake', 'Library', 'lighthouse',
    'Mall', 'marina', 'market', 'masjidh', 'meuseum', 'Monument', 'monument', 'Mosque', 'Mountain', 'mountain', 'Museum',
    'national', 'Natural', 'Nature',
    'observation', 'Observatory', 'Opera',
    'palace', 'Paragliding', 'park', 'Pier', 'Planetarium', 'Planetarium', 'Popular',
    'religious', 'river', 'Rock', 'Ruin',
    'Safari', 'Scenic', 'science', 'Scuba', 'spring', 'stadium', 'state', 'station',
    'temple', 'Theme', 'tourist', 'tower', 'trekking',
    'University',
    'Valley',
    'Water Body', 'waterfall', 'Wildlife', 'Wildlife',
    'Zoo'
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
