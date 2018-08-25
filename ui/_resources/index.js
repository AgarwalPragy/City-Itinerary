var cityImageUnavailable = 'http://getdrawings.com/img/gotham-city-silhouette-14.png'

var getData = function(url, callback) {
    console.log(url);
    console.log('getting data...');
    axios.get(url).then(function(response) {
        console.log('Request for ' + url + ' resulted in:');
        console.log(response.data);
        callback(response);
    });
}

window.fuse = null;

var chooseRandomElement = function(items) {
    var rindex = Math.floor(Math.random() * items.length);
    return items[rindex];
}

var registerCitiesDependents = function(cities) {
    var options = {
        shouldSort: true,
        includeScore: true,
        threshold: 0.2,
        location: 0,
        distance: 100,
        maxPatternLength: 32,
        minMatchCharLength: 1,
        keys: [
            {name: 'cityName', weight: 0.3},
            {name: 'cityAliases', weight: 0.1},
            {name: 'countryName', weight: 0.1},
            {name: 'countryAliases', weight: 0.1},
        ]
    };
    console.log(cities)
    var items = Object.values(cities);
    console.log(items)
    window.fuse = new Fuse(items, options);
    registerSearch();
}

var fuzzyMatcher = function(cities) {
  return function findMatches(query, callback) {
    // TODO: Fix the NYC on top instead of Agra when querying "a" bug
    console.log('query ' + query);
    var sanitized = query.replace(/\s/g, '')

    var matches = [];
    var results = fuse.search(sanitized);
    console.log(results);
    $.each(results, function(index, obj) {
        matches.push(obj.item);
    });
    callback(matches);
  };
};

var getEncodedCityImageURL = function (city) {
    var images = city.images;
    if(images && images.length > 0) return chooseRandomElement(images)['imageURL'];
    return encodeURIComponent(cityImageUnavailable);
}


var renderResult = function(item) {
    return '<div class="search-result">' + 
                '<img class="search-result-cityimage" src="/fetch-image?url=' + getEncodedCityImageURL(item) + '&width=160&height=90">' +
                '<div class="search-result-cityname">' + item.cityName + '</div>' +
                '<div class="search-result-countryname">' + item.countryName + '</div>' +
            '</div>';
};


var registerVue = function() {
    window.app = new Vue({
        el: '#container',
        data: {
            cities: {'England/London': {
                'cityName': 'London',
                'countryName': 'England'
            }},
            recentPlans: [],
            selectedCity: 'England/London'
        },
        mounted: function() {
            getData('/cities', function (response) {
                cities = response.data;
                window.app['cities'] = cities;
                registerCitiesDependents(cities);
            });
            getData('/recent-plans', function (response) {
                window.app['recentPlans'] = response.data;
            });
        },
        methods: {
            getCityImage: function(plan) {
                var city = this.cities[plan.city]
                return '/fetch-image?url=' + getEncodedCityImageURL(city) + '&width=320&height=180';
            },
            getCityName: function(plan) {
                var city = this.cities[plan.city];
                return '' + city.cityName;
            },
            getDurationText: function(hours) {
                if(hours > 24) {
                    var days = hours / 24;
                    var hours = hours % 24;
                    if(hours < 2) {
                        return days + ' days';
                    } else {
                        return days + ' days & ' + hours + ' hours';
                    }
                } else {
                    return hours + ' hours'
                }
            },
            getRandomVisitText: function() {
                var texts = ['Visit', 'Tour', 'Explore', 'Experience'];
                return chooseRandomElement(texts);
            }
        }
    });
}

var registerDateTime = function () {
    $('#datetimepicker1').datetimepicker({
            inline: true,
            sideBySide: true
        });
    $('#datetimepicker2').datetimepicker({
            inline: true,
            sideBySide: true,
            useCurrent: false //Important! See issue #1075
        });
    $("#datetimepicker1").on("dp.change", function (e) {
        $('#datetimepicker2').data("DateTimePicker").minDate(e.date);
    });
    $("#datetimepicker2").on("dp.change", function (e) {
        $('#datetimepicker1').data("DateTimePicker").maxDate(e.date);
    });
}


var registerSearch = function () {
    $('#city-searchbar').typeahead(
        {
            minLength: 1,
            hint: false
        },
        {
            name: 'city-searchbar',
            display: 'fullName',
            source: fuzzyMatcher(window.app.cities),
            templates: {
                empty: [
                    '<div class="search-result tt-suggestion">' + 
                        '<img class="search-result-cityimage" src="/fetch-image?url=' + encodeURIComponent(cityImageUnavailable) + '&width=160&height=90">' +
                        '<div class="search-result-cityname">That city sucks!</div>' +
                        '<div class="search-result-countryname">Don\'t go there ..</div>' +
                    '</div>'
                ].join('\n'),
                suggestion: renderResult
            }
        }
    );
}

registerVue();
registerDateTime();




