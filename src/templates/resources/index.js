var app = null;
var fuse = null;


Date.prototype.addHours = function(h) {
   this.setTime(this.getTime() + (h*60*60*1000));
   return this;
};


var validateCityPlan = function() {
    console.log('redirect');
};


var fuzzyMatcher = function(query, callback) {
    // TODO: Fix the NYC on top instead of Agra when querying "a" bug
    console.log('query ' + query);
    var sanitized = query.toLowerCase().replace(/[^a-z]/g, '')
    var matches = [];
    var results = fuse.search(sanitized);
    $.each(results, function(index, obj) {
        matches.push(obj.item);
    });
    callback(matches);
};


var getDurationText = function(hours) {
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
};


var getRandomVisitText = function() {
    var texts = ['Visit', 'Tour', 'Explore', 'Experience'];
    return utils.chooseRandomElement(texts);
};


var renderCitySearchItem = function(city) {
    return '<div class="search-result">' +
                '<img class="search-result-cityimage" src="' + utils.getEncodedCityImageURL(city, 160, 90) + '">' +
                '<div class="search-result-cityname">' + city.cityName + '</div>' +
                '<div class="search-result-countryname">' + city.countryName + '</div>' +
            '</div>';
};


var renderCitySearchEmpty = function(context) {
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
        minDate = new Date(e.date);
        minDate.addHours(24);
        $('#datetimepicker2').data("DateTimePicker").minDate(minDate);
    });
    $("#datetimepicker2").on("dp.change", function (e) {
        maxDate = new Date(e.date);
        maxDate.addHours(-24);
        $('#datetimepicker1').data("DateTimePicker").maxDate(maxDate);
    });
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
            source: fuzzyMatcher,
            templates: {
                empty: renderCitySearchEmpty,
                suggestion: renderCitySearchItem
            }
        }
    ).on('typeahead:selected', function (e, city) {
        app.searchSelectedCity = city;
    });
};


var registerFuse = function() {
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
    fuse = new Fuse(items, options);
    registerCitySearch();
};


var registerVue = function() {
    app = new Vue({
        el: '#container',
        data: {
            cities: {},
            recentPlans: [],
            searchSelectedCity: false
        },
        mounted: function() {},
        watch: {
            cities: function () {
                registerFuse();
            }
        }
    });
};


utils.getData('/api/cities', {}, function (response) {
    app.cities = response.data;
});


utils.getData('/api/recent-plans', {}, function (response) {
    app.recentPlans = response.data;
});


registerVue();
registerDateTime();