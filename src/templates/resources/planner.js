var app = null;
var cityFuse = null;
var pointFuse = null;
var map = null;
var pinPopups = null;


Date.prototype.addHours = function(h) {
   this.setTime(this.getTime() + (h*60*60*1000));
   return this;
};


var getRatingStars = function(point) {
    console.log(point.pointName + ' has rating ' + point.avgRating);
    var rating = Math.round(point.avgRating) / 2.0;
    console.log('Giving it ' + rating + ' stars')
    var classes = [];
    for (var i = 1; i <= Math.floor(rating); i++) {
        classes.push('fas fa-star');
    }
    if(rating > Math.floor(rating)) {
        classes.push('fas fa-star-half-alt');
    }
    for (var i = Math.ceil(rating)+1; i <= 5; i++) {
        classes.push('far fa-star');
    }
    console.log(classes);
    return classes;
};


var renderCitySearchResult = function(city) {
    return '<div class="search-result">' +
                '<img class="search-result-cityimage" src="' + utils.getEncodedCityImageURL(city, 160, 90) + '">' +
                '<div class="search-result-cityname">' + city.cityName + '</div>' +
                '<div class="search-result-countryname">' + city.countryName + '</div>' +
            '</div>';
};

var renderCityEmptyResult = function(context) {
    var randomSuggestion = utils.chooseRandomElement([
        '&#10075;' + context.query + '&#10076; sucks lmao.',
        'They won\'t let me in',
        'Shoo .. Don\'t go there!',
        'There be <s>dragons</s> nothing?',
        'Come again?'
    ]);
    var randomPerson = utils.chooseRandomElement(['Albert Einstein', 'Nikola Tesla', 'Charles Darwin', 'Carl Sagan', 'Charles Babbage', 'Aristotle']);
    return '<div class="search-result tt-suggestion">' +
                '<img class="search-result-cityimage" src="' + utils.fetchImageURL(utils.cityImageUnavailable, 160, 90) + '">' +
                '<div class="search-result-cityname">' + randomSuggestion + '</div>' +
                '<div class="search-result-countryname">- ' + randomPerson + '</div>' +
            '</div>';
};

var renderPointSearchResult = function(point) {
    return '<div class="search-result">' +
                '<img class="search-result-pointimage" src="' + utils.getEncodedPointImageURL(city, 144, 80) + '">' +
                '<div class="search-result-pointname">' + point.pointName + '</div>' +
            '</div>';
};

var renderPointEmptyResult = function(context) {
    return '<div class="search-result tt-suggestion">' +
                '<img class="search-result-pointimage" src="' + utils.fetchImageURL(utils.pointImageUnavailable, 144, 80) + '">' +
            '</div>';
};


var fuzzyCityMatcher = function(query, callback) {
    // TODO: Fix the NYC on top instead of Agra when querying "a" bug
    console.log('query ' + query);
    var sanitized = query.toLowerCase().replace(/[^a-z]/g, '')
    var matches = [];
    var results = cityFuse.search(sanitized);
    $.each(results, function(index, obj) {
        matches.push(obj.item);
    });
    callback(matches);
};


var fuzzyPointMatcher = function(query, callback) {
    // TODO: Fix the NYC on top instead of Agra when querying "a" bug
    console.log('query ' + query);
    var sanitized = query.toLowerCase().replace(/[^a-z]/g, '')
    var matches = [];
    var results = pointFuse.search(sanitized);
    $.each(results, function(index, obj) {
        matches.push(obj.item);
    });
    callback(matches);
};


var renderPinPopup = function(point) {
    return '<div class="pin-popup">' +
               '<div class="pin-popup-title">' + point.pointName + '</div>' +
               '<div class="pin-popup-description' + point.description + '</div>' +
           '</div>';
};


var registerCitySearch = function () {
    $('#city-searchbar').typeahead(
        {
            minLength: 1,
            hint: false
        },
        {
            name: 'fuzzySearchOnCities',
            display: 'fullName',
            limit: 6,
            source: fuzzyCityMatcher,
            templates: {
                empty: renderCityEmptyResult,
                suggestion: renderCitySearchResult
            }
        }
    ).on('typeahead:selected', function (e, city) {
        app.searchSelectedCity = city;
    });
};


var registerPointSearch = function () {
    $('#point-searchbar').typeahead(
        {
            minLength: 1,
            hint: false
        },
        {
            name: 'fuzzySearchOnCities',
            display: 'fullName',
            limit: 6,
            source: fuzzyPointMatcher,
            templates: {
                empty: renderPointEmptyResult,
                suggestion: renderPointSearchResult
            }
        }
    ).on('typeahead:selected', function (e, point) {
        // TODO: add point to some list.
    });
};


var registerCityFuse = function() {
    var options = {
        shouldSort: true,
        includeScore: true,
        threshold: 0.2,
        location: 0,
        distance: 100,
        maxPatternLength: 32,
        minMatchCharLength: 1,
        keys: [
            {name: 'cityName', weight: 0.4},
            {name: 'cityAliases', weight: 0.2},
            {name: 'countryName', weight: 0.1},
            {name: 'countryAliases', weight: 0.1},
        ]
    };
    var items = Object.values(app.cities);
    cityFuse = new Fuse(items, options);
    registerCitySearch();
};


var registerPointFuse = function() {
    var options = {
        shouldSort: true,
        includeScore: true,
        threshold: 0.2,
        location: 0,
        distance: 100,
        maxPatternLength: 32,
        minMatchCharLength: 1,
        keys: [
            {name: 'pointName', weight: 0.4},
            {name: 'pointAliases', weight: 0.2},
            {name: 'cityName', weight: 0.2},
            {name: 'cityAliases', weight: 0.2},
            {name: 'countryName', weight: 0.1},
            {name: 'countryAliases', weight: 0.1},
        ]
    };
    var items = Object.values(app.points);
    pointFuse = new Fuse(items, options);
    registerPointSearch();
};


var registerDateTime = function () {
    $('#date_timepicker_start').datetimepicker({
        format: 'Y/m/d H.i',
        allowTimes: ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00'],
        onShow:function( ct ){
            this.setOptions({
                maxDate: $('#date_timepicker_end').val()?$('#date_timepicker_end').val():false
            })
        },
        timepicker: true
    });
    $('#date_timepicker_end').datetimepicker({
        format: 'Y/m/d H.i',
        allowTimes: ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00'],
        onShow:function( ct ){
            this.setOptions({
                minDate: $('#date_timepicker_start').val()?$('#date_timepicker_start').val():false
            })
        },
        timepicker: true
    });
};


var registerMap = function() {
    map = L.map('mapid')
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
};

var redrawMap = function() {
    map.setView([51.505, -0.09], 13);
    pinPopups = {}
    for (var i = 0; i < app.itinerary.length; i++) {
        var point = itinerary[i].point;
        var pointName = point.pointName;
        console.log('Point: ' + point.fullName + ', coordinates: ' + point.coordinates);
        pinPopups[pointName] = L.marker(getCoordinatesFromString(point.coordinates));
        p = pinPopups[pointName];
        p.addTo(map);
        p.bindPopup(renderPinPopup(point));
        p.openPopup();
    }
}

var registerVue = function() {
    Vue.directive('sortable', {
        inserted: function (el, binding) {
            var sortable = new Sortable(el, binding.value || {});
        }
    });
    window.app = new Vue({
        el: '#plan-box',
        data: {
            cities: {},
            points: {},
            searchSelectedCity: false,
            currentCity: false,
            currentConstraints: false,
            itinerary: []
        },
        mounted: function() {},
        methods: {
            reorder ({oldIndex, newIndex}) {
                const movedItem = app.itinerary.splice(oldIndex, 1)[0]
                app.itinerary.splice(newIndex, 0, movedItem)
            }
        },
        watch: {
            cities: function() {
                registerCityFuse();
                registerPointFuse();
            },
            currentCity: function() {
                utils.getData('/api/points', {
                    city: app.currentCity.fullName
                }, function (response) {
                    app.points = response.data;
                });
                utils.getData('/api/itinerary', {
                    city: initialCity,
                    constraints: initialConstraints
                }, function (response) {
                    app.itinerary = response.data;
                });
                redrawMap();
            }
        }
    });
};


(function() {
    registerVue();
    utils.getData('/api/itinerary', {
        city: initialCity,
        constraints: initialConstraints
    }, function (response) {
        app.itinerary = response.data;
    });
    app.currentCity = initialCity;
    app.currentConstraints = initialConstraints;
    utils.getData('/api/cities', {}, function (response) {
        app.cities = response.data;
    });
    utils.getData('/api/points', {
        city: app.currentCity.fullName
    }, function (response) {
        app.points = response.data;
    });


    registerDateTime();
    $('date_timepicker_start').val('')

    registerMap();
    $('#city-searchbar').val(initialCity);

})();