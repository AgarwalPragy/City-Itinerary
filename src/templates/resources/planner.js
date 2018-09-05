var app = null;
var editTimeApp = null;
var cityFuse = null;
var pointFuse = null;
var map = null;
var allCoordinates = [];
var allClusters = [];
var allClusterPaths = [];
var recenteringMap = false;
var itineraryCallUUID = null;
var searchSelectedCity = initialConstraints.city;
var timeEditingPoint = null;
var dateFormat = 'Y/m/d H.i';
var momentDateFormat = 'YYYY/MM/DD HH.mm';

Date.prototype.addHours = function(h) {
   this.setTime(this.getTime() + (h*60*60*1000));
   return this;
};

var getPointFromName = function(pointName) {
    return app.points.points[pointName];
}

var getRatingStars = function(point) {
    var rating = Math.round(point.avgRating) / 2.0;
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
    return classes;
};

var validateTime = function(visit) {
    var chosenDay = $('#edit-time-dayNum').val();
    var chosenEnter = $('#edit-time-enterTime').val();
    var chosenExit = $('#edit-time-exitTime').val();

    // TODO: Magic here

    var likes = JSON.parse(JSON.stringify(app.constraints.likes));
    var likesTimings = JSON.parse(JSON.stringify(app.constraints.likesTimings));

    var index = likes.indexOf(visit.point.pointName);
    if(index >= 0) {
        likes.splice(index, 1);
        likesTimings.splice(index, 1);
    }
    likes.push(visit.point.pointName);
    likesTimings.push([chosenDay, chosenEnter, chosenExit].join('-'))
    app.constraints.likes = likes;
    app.constraints.likesTimings = likesTimings;
    $('#edit-modal').modal('hide');
}


var openEditTimeModal = function(visit) {
    editTimeApp.visit = visit;
    timeEditingPoint = visit.point;
    $('#edit-modal').modal();
}

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
                '<img class="search-result-pointimage" src="' + utils.getEncodedPointImageURL(point, 80, 45) + '">' +
                '<div class="search-result-pointname">' + point.pointName + '</div>' +
            '</div>';
};

var renderPointEmptyResult = function(context) {
    return '<div class="search-result tt-suggestion">' +
                '<img class="search-result-pointimage" src="' + utils.fetchImageURL(utils.pointImageUnavailable, 80, 45) + '">' +
            '</div>';
};


var fuzzyCityMatcher = function(query, callback) {
    var sanitized = query.toLowerCase().replace(/[^a-z]/g, '')
    var matches = [];
    var results = cityFuse.search(sanitized);
    $.each(results, function(index, obj) {
        matches.push(obj.item);
    });
    callback(matches);
};


var fuzzyPointMatcher = function(query, callback) {
    var sanitized = query.toLowerCase().replace(/[^a-z]/g, '')
    var matches = [];
    var results = pointFuse.search(sanitized);
    $.each(results, function(index, obj) {
        matches.push(obj.item);
    });
    callback(matches);
};


var renderPinPopup = function(point) {
    var desc = point.description || '';
    return '<div class="pin-popup">' +
               '<div class="pin-popup-title">' + point.pointName + '</div>' +
               '<div class="pin-popup-description">' + desc.replace(/\n/g, '<hr/>') + '</div>' +
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
            limit: 40,
            source: fuzzyCityMatcher,
            templates: {
                empty: renderCityEmptyResult,
                suggestion: renderCitySearchResult
            }
        }
    ).on('typeahead:selected', function (e, city) {
        $('.background-image').css(
            'background-image', "url('" + utils.getEncodedCityImageURL(city, null, null) + "')");

        searchSelectedCity = city.fullName;
    }).on('blur', function (e) {
        $('#city-searchbar').val(searchSelectedCity);
    });
};


var registerPointSearch = function () {
    $('#point-searchbar').typeahead(
        {
            minLength: 1,
            hint: false
        },
        {
            name: 'fuzzySearchOnPoints',
            display: 'fullName',
            limit: 40,
            source: fuzzyPointMatcher,
            templates: {
                empty: renderPointEmptyResult,
                suggestion: renderPointSearchResult
            }
        }
    ).on('typeahead:selected', function (e, point) {
        openEditTimeModal({
            point: point,
            enterTime: '',
            exitTime: '',
            dayNum: '',
        })
    }).on('blur', function (e) {
        // $('#point-searchbar').val('');
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
    var items = Object.values(app.points.points);
    pointFuse = new Fuse(items, options);
};

var limitTripLength = function() {
    var minDate = moment($('#date_timepicker_start').val(), momentDateFormat);
    var maxDate = moment(minDate).add(8, 'days');

    var currentEndDate = moment($('#date_timepicker_end').val(), momentDateFormat);
    if(currentEndDate.isSameOrBefore(minDate) || currentEndDate.isAfter(maxDate)) {
        currentEndDate = moment(minDate).add(4, 'days');
    }
    $('#date_timepicker_end').datetimepicker({
        minDate: minDate.format(momentDateFormat),
        maxDate: maxDate.format(momentDateFormat),
        value: currentEndDate.format(momentDateFormat),
    });
}

var registerDateTime = function () {
    $('#date_timepicker_start').datetimepicker({
        format: dateFormat,
        defaultTime:'10:00',
        value: initialConstraints.startDate + ' ' + initialConstraints.startDayTime + ':00',
        allowTimes: ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00'],
        onShow: limitTripLength,
        onChangeDateTime: limitTripLength,
        timepicker: true
    });
    $('#date_timepicker_end').datetimepicker({
        format: dateFormat,
        defaultTime:'20:00',
        value: initialConstraints.endDate + ' ' + initialConstraints.endDayTime + ':00',
        allowTimes: ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00'],
        onShow: limitTripLength,
        timepicker: true
    });
};


var registerMap = function() {
    map = L.map('mapid')
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    map.setView([51.505, -0.09], 12);
};


var clearMap = function() {
    for (var i = allClusters.length - 1; i >= 0; i--) {
        allClusters[i].remove();
    }
    allClusters = [];
}

var reCenterMap = function() {
    if(recenteringMap)
        return;
    recenteringMap = true;
    if(allCoordinates.length < 1) return;
    var bounds = new L.LatLngBounds(allCoordinates);
    map.fitBounds(bounds, {
        padding: [10, 10]
    });
    map.invalidateSize();
    recenteringMap = false;
}

var addPointsToMap = function(currentPage, items) {
    var pins = [];
    if(!items) return;
    for (var i = 0; i < items.length; i++) {
        var point = items[i].point;
        var pointName = point.pointName;
        if(pointName === '__newday__')
            continue;
        console.log('Point: ' + point.fullName + ', coordinates: ' + point.coordinates);
        var coordinates = utils.getCoordinatesFromString(point.coordinates);
        coordinates = L.latLng(coordinates[0], coordinates[1]);
        allCoordinates.push(coordinates);
        pin = L.marker(coordinates);        
        pin.bindPopup(renderPinPopup(point));
        pins.push(pin);
    }
    cluster = L.layerGroup(pins);
    allClusters.push(cluster);
    cluster.addTo(map);
    // path = L.Routing.control({
    //     waypoints: allCoordinates,
    //     routeWhileDragging: false
    // });
    // allClusterPaths.push(path);
    // path.addTo(map);
    reCenterMap();
}

var isLiked = function(point) {
    var index = app.constraints.likes.indexOf(point.pointName);
    return index > -1;
}

var isDisliked = function(point) {
    var index = app.constraints.dislikes.indexOf(point.pointName);
    return index > -1;
}

var removeDislikePoint = function(pointName) {
    var index = app.constraints.dislikes.indexOf(pointName);
    app.constraints.dislikes.splice(index, 1);
}

var dislikePoint = function(point) {
    if(isDisliked(point)) return;
    app.constraints.dislikes.push(point.pointName);
}


var removeLikePoint = function(visit) {
    var index = app.constraints.likes.indexOf(visit.point.pointName);
    app.constraints.likes.splice(index, 1);
    app.constraints.likesTimings.splice(index, 1);
}

var likePoint = function(visit) {
    if(isLiked(visit.point)) return;
    app.constraints.likes.push(visit.point.pointName);
    app.constraints.likesTimings.push([visit.dayNum, visit.enterTime, visit.exitTime].join('-'))
}



var getItineraryPage = function(page) {
    if(page == 1) {
        itineraryCallUUID = utils.uuid4();
    }
    utils.getData('/api/itinerary', {
        city: app.constraints.city,
        startDate: app.constraints.startDate,
        endDate: app.constraints.endDate,
        startDayTime: app.constraints.startDayTime,
        endDayTime: app.constraints.endDayTime,
        dislikes: app.constraints.dislikes.join('|'),
        likes: app.constraints.likes.join('|'),
        likesTimings: app.constraints.likesTimings.join('|'),
        page: page,
        uuid: itineraryCallUUID
    }, function (response) {
        var data = response.data;
        var uuid = data.uuid;
        if(uuid !== itineraryCallUUID) {
            console.log('Ignoring response of previous API call with UUID: ' + itineraryCallUUID);
            return; // If response is from some old request, ignore
        }
        currentPage = parseInt(data.itinerary.currentPage);
        if(currentPage === 1) {
            app.itinerary = data.itinerary.itinerary;
            app.mustVisit = data.mustVisit;
            clearMap();
            allCoordinates = [];
            allClusters = [];
        }
        else
            app.itinerary = app.itinerary.concat(data.itinerary.itinerary);

        addPointsToMap(currentPage, data.itinerary.itinerary);
        if(data.itinerary.nextPage !== false)
            getItineraryPage(data.itinerary.nextPage);
        else
            setTimeout(reCenterMap, 1000);
    });
}

var registerEditTimeVue = function() {
    editTimeApp = new Vue({
        el: '#edit-modal-content',
        data: {
            visit: {
                point: {
                    pointName: '',
                    openingHour: '$,$,$,$,$,$,$',
                    closingHour: '$,$,$,$,$,$,$',
                },
                enterTime: -1,
                exitTime: -1,
            }
        }
    });
}

var registerVue = function() {
    app = new Vue({
        el: '#plan-box',
        data: {
            cities: {},
            points: {points: [], pointsOrder: []},
            constraints: false,
            itinerary: [],
            mustVisit: {},
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
            },
            points: function() {
                registerPointFuse();
            },
            constraints: {
                handler: function() {
                    $('#city-searchbar').val(app.constraints.city);
                    console.log('constraints changed!')
                    getItineraryPage(1);
                    utils.getData('/api/points', {
                        city: app.constraints.city
                    }, function (response) {
                        app.points = response.data;
                    });
                },
                deep: true
            }
        }
    });
};


(function() {
    registerVue();
    registerEditTimeVue();
    app.constraints = initialConstraints;
    utils.getData('/api/cities', {}, function (response) {
        app.cities = response.data;
    });
    $('#city-searchbar-submit').on('click', function() {
        newconstraints = {
            city: $('#city-searchbar').val(),
            startDate: $('#date_timepicker_start').val().split(' ')[0],
            endDate: $('#date_timepicker_end').val().split(' ')[0],
            startDayTime: $('#date_timepicker_start').val().split(' ')[1].split(':')[0],
            endDayTime: $('#date_timepicker_end').val().split(' ')[1].split(':')[0],
            dislikes: [],
            likes: [],
            likesTimings: [],
        }
        app.constraints = newconstraints;
    });

    registerDateTime();
    registerMap();
    registerCitySearch();
    registerPointSearch();
})();