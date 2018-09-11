var app = null;
var editTimeApp = null;
var cityFuse = null;
var pointFuse = null;
var itineraryCallUUID = null;
var searchSelectedCity = null;
var dateFormat = 'Y/m/d H.i';
var momentDateFormat = 'YYYY/MM/DD HH.mm';
var lastName = null;

var map = null;
var mapRedrawNeeded = false;
var lastRedrawTime = new Date();
var directionsService = null;
var firstDraw = true;
var mapIcons = [
    'http://maps.google.com/mapfiles/marker_orange.png',
    'http://maps.google.com/mapfiles/marker_purple.png',
    'http://maps.google.com/mapfiles/marker_grey.png',
    'http://maps.google.com/mapfiles/marker_green.png',
    'http://maps.google.com/mapfiles/marker_yellow.png',
    'http://maps.google.com/mapfiles/marker_white.png',
    'http://maps.google.com/mapfiles/marker_black.png',
    'http://maps.google.com/mapfiles/marker.png'
];
// https://mapstyle.withgoogle.com/
var mapStyles = [{"elementType": "labels", "stylers": [{"visibility": "off"} ] }, {"featureType": "administrative.neighborhood", "stylers": [{"visibility": "off"} ] }, {"featureType": "poi.business", "stylers": [{"visibility": "off"} ] }, {"featureType": "road", "elementType": "labels.icon", "stylers": [{"visibility": "off"} ] }, {"featureType": "transit", "stylers": [{"visibility": "off"} ] } ];
var bounds = null;
var allInfoWindows = null;
var allMarkers = null;


Date.prototype.addHours = function(h) {
   this.setTime(this.getTime() + (h*60*60*1000));
   return this;
};


var openPopup = function(name) {
    if(lastName !== null)
        allInfoWindows[lastName].close();
    allInfoWindows[name].open(map, allMarkers[name]);
    lastName = name;
}


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

var clearModal = function() {
    $('#edit-time-dayNum').val('');
    $('#edit-time-enterTime').val('');
    $('#edit-time-exitTime').val('');
    $('#response-status').text('');
}

var validateTime = function(visit) {
    var chosenDay = utils.roundUpTime($('#edit-time-dayNum').val());
    var chosenEnter = utils.roundUpTime($('#edit-time-enterTime').val());
    var chosenExit = utils.roundUpTime($('#edit-time-exitTime').val());

    var likes = JSON.parse(JSON.stringify(app.constraints.likes));
    var likesTimings = JSON.parse(JSON.stringify(app.constraints.likesTimings));
    var index = likes.indexOf(visit.point.pointName);
    if(index >= 0) {
        likes.splice(index, 1);
        likesTimings.splice(index, 1);
    }
    likes.push(visit.point.pointName);
    likesTimings.push([chosenDay, chosenEnter, chosenExit].join('-'));

    utils.getData('/api/validate', {
        city: app.constraints.cityName,
        startDate: app.constraints.startDate,
        endDate: app.constraints.endDate,
        startDayTime: app.constraints.startDayTime,
        endDayTime: app.constraints.endDayTime,
        dislikes: app.constraints.dislikes.join('|'),
        likes: likes.join('|'),
        likesTimings: likesTimings.join('|'),
    }, function (response) {
        code = response.data;
        $('#response-status').text(code);
        if(code === 'success') {
            clearModal();
            $('#edit-modal').modal('hide');
            app.constraints.likes = likes;
            app.constraints.likesTimings = likesTimings;
        }
    });
}


var openEditTimeModal = function(visit) {
    editTimeApp.visit = visit;
    editTimeApp.$forceUpdate();
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
    var sanitized = query.toLowerCase().replace(/[^a-z]/g, '');
    var matches = [];
    if(sanitized === '')
        matches = cityFuse.list;
    else {
        var results = cityFuse.search(sanitized);
        $.each(results, function(index, obj) {
            matches.push(obj.item);
        });
    }
    callback(matches);
};


var fuzzyPointMatcher = function(query, callback) {
    var sanitized = query.toLowerCase().replace(/[^a-z]/g, '');
    var matches = [];
    if(sanitized === '')
        matches = pointFuse.list;
    else {
        var results = pointFuse.search(sanitized);
        $.each(results, function(index, obj) {
            matches.push(obj.item);
        });
    }
    callback(matches);
};


var renderPinPopup = function(point, dayNum) {
    var desc = point.description || '';
    desc = desc.replace(/\n/g, '<hr/>').substring(0, 200) + '...';
    var openings = '';
    var closings = '';
    var open = point.openingHour.split(',')
    var close = point.closingHour.split(',')
    for (var i = 0; i < 7; i++) {
        openings += '<td>' + (open[i] === '$' ? '$': utils.roundUpTime(open[i])) + '</td>';
        closings += '<td>' + (close[i] === '$' ? '$': utils.roundUpTime(close[i])) + '</td>';
    }

    return '<div class="pin-popup">' +
               '<div class="pin-popup-title">' + point.pointName + '</div>' +
               '<div class="pin-popup-timing">' +
                   '<table class="table table-bordered"> <thead> <tr> <th scope="col">Timings</th> <th scope="col">Sun</th> <th scope="col">Mon</th> <th scope="col">Tue</th> <th scope="col">Wed</th> <th scope="col">Thu</th> <th scope="col">Fri</th> <th scope="col">Sat</th> </tr> </thead> <tbody> <tr> <th scope="row">Open</th>' +
                   openings +
                   '</tr> <tr> <th scope="row">Close</th>' +
                   closings +
                   '</tr> </tbody> </table>' +
               '</div>' +
               '<div class="pin-popup-description">' + desc + '</div>' +
           '</div>';
};


var registerCitySearch = function () {
    $('#city-searchbar').typeahead(
        {
            minLength: 0,
            hint: false
        },
        {
            name: 'fuzzySearchOnCities',
            display: 'fullName',
            limit: 50,
            source: fuzzyCityMatcher,
            templates: {
                empty: renderCityEmptyResult,
                suggestion: renderCitySearchResult
            }
        }
    ).on('typeahead:selected', function (e, city) {
        searchSelectedCity = city.fullName;
        utils.getData('/api/city-image', {
            city: city.cityName
        }, function(response) {
            var url = response.data;
            var imgurl = utils.fetchImageURL(url, 1400, 875)
            $('.background-image').css('background-image',
                "url('" + imgurl + "')");
        });
    }).on('blur', function (e) {
        $('#city-searchbar').val(searchSelectedCity);
    });
};


var registerPointSearch = function () {
    $('#point-searchbar').typeahead(
        {
            minLength: 0,
            hint: false
        },
        {
            name: 'fuzzySearchOnPoints',
            display: 'fullName',
            limit: 50,
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
        $('#point-searchbar').val('');
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
    var maxDate = moment(minDate).add(7, 'days');

    var currentEndDate = moment($('#date_timepicker_end').val(), momentDateFormat);
    if(currentEndDate.isSameOrBefore(minDate) || currentEndDate.isAfter(maxDate)) {
        currentEndDate = moment(minDate).add(3, 'days');
        currentEndDate = currentEndDate.format(momentDateFormat);
        currentEndDate = currentEndDate.substring(0, currentEndDate.length-5) + '20.00';
        currentEndDate = moment(currentEndDate, momentDateFormat);
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


var resetMap = function() {
    map = new google.maps.Map(document.getElementById('mapid'), {
        zoom: 6,
        center: {lat: 18.9, lng: 72.82},
        mapTypeControl: true,
        scaleControl: true,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
            mapTypeIds: ['roadmap']
        },
        styles: mapStyles,
    });
    directionsService = new google.maps.DirectionsService;
    bounds = new google.maps.LatLngBounds();
    allInfoWindows = {};
    allMarkers = {};
    lastName = null;
};

var _addPointsToMap = function(dayNum, items) {
    var directionsDisplay = new google.maps.DirectionsRenderer({
        map: map,
        preserveViewport: false,
        suppressMarkers: true,
    });
    if(items.length === 1) {
        var point = items[0].point;
        var coordinates = point.coordinates.split(',');
        var lat = parseFloat(coordinates[0]);
        var lng = parseFloat(coordinates[1]);
        coordinates = new google.maps.LatLng(lat, lng);
        bounds.extend(coordinates);
        makeClosuredMarker(dayNum, point, coordinates);
        return;
    }
    var waypoints = [];
    for (var i = 0; i < items.length; i++) {
        var point = items[i].point;
        var coordinates = point.coordinates.split(',');
        var lat = parseFloat(coordinates[0]);
        var lng = parseFloat(coordinates[1]);
        coordinates = new google.maps.LatLng(lat, lng);
        bounds.extend(coordinates);
        waypoints.push({
            location: coordinates,
            stopover: true,
        });
    }
    var origin = waypoints[0].location;
    var destination = waypoints[waypoints.length-1].location;
    waypoints = waypoints.splice(1, waypoints.length-1);

    var routeRequest = {
        origin: origin,
        destination: destination,
        waypoints: waypoints,
        optimizeWaypoints: false,
        travelMode: 'DRIVING',
    };
    var handleAPIResponse = function(response, status) {
        if(status === 'ZERO_RESULTS' && response.request.travelMode == 'DRIVING') {
            var newRequest = response.request;
            newRequest.travelMode = 'WALKING';
            directionsService.route(newRequest, handleAPIResponse);
        } else if(status === 'ZERO_RESULTS' && response.request.travelMode == 'WALKING') {
            var newRequest = response.request;
            newRequest.travelMode = 'BICYCLING';
            directionsService.route(newRequest, handleAPIResponse);
        } else if (status !== 'OK'){
            console.log('Directions request failed due to ' + status);
            return;
        }
        var legs = response.routes[0].legs;

        for(var i = 0; i < legs.length; i++){
            var point = items[i].point;
            makeClosuredMarker(dayNum, point, legs[i].start_location);
        }
        // Plot the destination
        makeClosuredMarker(dayNum, items[items.length-1].point, legs[legs.length-1].end_location);
        directionsDisplay.setDirections(response);
    }
    directionsService.route(routeRequest, handleAPIResponse);
}

var addPointsToMap = function() {
    var now = new Date();
    var seconds = (now.getTime() - lastRedrawTime.getTime()) / 1000;
    if(seconds < 2 && (!firstDraw)) {
        if(mapRedrawNeeded){
            setTimeout(addPointsToMap, 500);
        }
        return;
    }
    firstDraw = false;
    lastRedrawTime = now;
    $('#map-status').hide();
    mapRedrawNeeded = false;
    resetMap();
    var items = [];
    var dayNum = 1;
    for (var i = 0; i < app.itinerary.length; i++) {
        if(app.itinerary[i].point.pointName === '__newday__' && items.length > 0){
            _addPointsToMap(dayNum, JSON.parse(JSON.stringify(items)));
            items = [];
            dayNum++;
        } else if(app.itinerary[i].point.pointName !== '__newday__') {
            items.push(app.itinerary[i]);
        }
    }
    if(items.length > 0)
        _addPointsToMap(dayNum, JSON.parse(JSON.stringify(items)));

    // map.panToBounds(bounds);
    map.fitBounds(bounds);
}

var makeClosuredMarker = function(dayNum, point, position) {
    var name = point.pointName;
    allInfoWindows[name] =new google.maps.InfoWindow({
        content: renderPinPopup(point),
    });

    allMarkers[name] = new google.maps.Marker({
        icon: mapIcons[dayNum-1],
        map: map,
        position: position,
        title: point.pointName,
    });

    allMarkers[name].addListener('click', function() {
        openPopup(name);
    });
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
        city: app.constraints.cityName,
        startDate: app.constraints.startDate,
        endDate: app.constraints.endDate,
        startDayTime: app.constraints.startDayTime,
        endDayTime: app.constraints.endDayTime,
        dislikes: app.constraints.dislikes.join('|'),
        likes: app.constraints.likes.join('|'),
        likesTimings: app.constraints.likesTimings.join('|'),
        algo: app.constraints.algo,
        pFactor: app.constraints.pFactor,
        page: page,
        uuid: itineraryCallUUID
    }, function (response) {
        var data = response.data;
        var uuid = data.uuid;
        if(uuid !== itineraryCallUUID) {
            console.log('Ignoring response of previous API call with UUID: ' + itineraryCallUUID);
            return; // If response is from some old request, ignore
        }
        $('#map-status').show();

        currentPage = parseInt(data.itinerary.currentPage);
        if(currentPage === 1) {
            app.itinerary = data.itinerary.itinerary;
            app.mustVisit = data.mustVisit;
        }
        else
            app.itinerary = app.itinerary.concat(data.itinerary.itinerary);

        if(data.itinerary.nextPage !== false)
            getItineraryPage(data.itinerary.nextPage);
        else {
            mapRedrawNeeded = true;
            addPointsToMap();
        }
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
            pFactor: 'less',
            algo: 'static',
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
                    $('#city-searchbar').val(app.constraints.cityName);
                    console.log('constraints changed!')
                    getItineraryPage(1);
                    utils.getData('/api/points', {
                        city: app.constraints.cityName
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
    searchSelectedCity = initialConstraints.cityName;
    utils.getData('/api/city-image', {
        city: searchSelectedCity
    }, function(response) {
        var url = response.data;
        var imgurl = utils.fetchImageURL(url, 1400, 875)
        $('.background-image').css('background-image',
            "url('" + imgurl + "')");
    });

    registerVue();
    registerEditTimeVue();
    app.constraints = initialConstraints;
    utils.getData('/api/cities', {}, function (response) {
        app.cities = response.data;
    });
    $('#city-searchbar-submit').on('click', function() {
        newconstraints = {
            cityName: $('#city-searchbar').val(),
            startDate: $('#date_timepicker_start').val().split(' ')[0],
            endDate: $('#date_timepicker_end').val().split(' ')[0],
            startDayTime: $('#date_timepicker_start').val().split(' ')[1].split(':')[0],
            endDayTime: $('#date_timepicker_end').val().split(' ')[1].split(':')[0],
            dislikes: [],
            likes: [],
            likesTimings: [],
            pFactor: app.constraints.pFactor,
            algo: app.constraints.algo,
        }
        app.constraints = newconstraints;
        utils.getData('/api/city-image', {
            city: newconstraints.cityName,
        }, function(response) {
            var url = response.data;
            var imgurl = utils.fetchImageURL(url, 1400, 875)
            $('.background-image').css('background-image',
                "url('" + imgurl + "')");
        });
    });

    $('#edit-modal').on('hidden.bs.modal', function () {
        clearModal();
    })

    $('#algorithm').toggles({
        text: {
            off: 'Showing different areas',
            on: 'Allowing days to overlap'
        },
        width: 220,
        height: 25,
    }).on('toggle', function(e, active) {
        if (active) {
            app.constraints.algo = 'incremental';
        } else {
            app.constraints.algo = 'static';
        }
    });

    $('#p-factor').toggles({
        text: {
            on: 'Prefering best points',
            off: 'Prefering more points'
        },
        width: 220,
        height: 25,
    }).on('toggle', function(e, active) {
        if (active) {
            app.constraints.pFactor = 'more';
        } else {
            app.constraints.pFactor = 'less';
        }
    });


    registerDateTime();
    registerCitySearch();
    registerPointSearch();
})();