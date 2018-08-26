from entities import CityID, CountryID, PointID

matchPointID_countryThreshold = 75
matchPointID_cityThreshold = 85
matchPointID_pointThreshold = 95

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

