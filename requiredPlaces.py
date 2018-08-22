from utilities import processName

requiredCountries = [
    "Thailand",
    "South Korea",
    "England",
    "United Kingdom",
    "Italy",
    "France",
    "Singapore",
    "China",
    "USA",
    "United States of America",
    "United States",
    "Netherlands",
    "The Netherlands",
    "Turkey",
    "Japan",
    "United Arab Emirates",
    "UAE",
    "Austria",
    "Malaysia",
    "Taiwan",
    "China",
    "Spain",
    "Saudi Arabia",
    "India"
]

requiredCities = [
    "Bangkok",
    "Seoul",
    "London",
    "Milan",
    "Paris",
    "Rome",
    "Singapore",
    "Shanghai",
    "New York",
    "New York City",
    "Amsterdam",
    "Istanbul",
    "Tokyo",
    "Dubai",
    "Vienna",
    "Kuala Lumpur",
    "Taipei",
    "Hong Kong",
    "Hong Kong SAR",
    "Riyadh",
    "Barcelona",
    "Los Angeles",
    "Mumbai",
    "New Delhi",
    "Pune",
    "Kolkata",
    "Agra",
    "Jaipur",
    "Bengaluru",
    "Bangalore",
    "Calcutta"
]


processedRequiredCities = set(list(map(processName, requiredCities)))
processedRequiredCountries = set(list(map(processName, requiredCountries)))


