function getData(url, attrib) {
    console.log(url);
    console.log('getting data...');
    axios.get(url).then(function(response) {
            console.log('Request for ' + url + ' resulted in:');
            console.log(response.data);
            window.app[attrib] = response.data;
    });
}

window.registerVue = function() {
    window.app = new Vue({
        el: '#container',
        data: {
            cities: [],
            recentPlans: [],
            selectedCity: 'England/London'
        },
        mounted: function() {
            getData('/cities', 'cities');
            getData('/recent-plans', 'recentPlans');
        },
        methods: {
            getCityImage: function(plan) {
                var city = this.cities[plan.city]
                var url = city.cityImage;
                return '/fetch-image?url=' + encodeURIComponent(url) + '&width=320&height=180';
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
                var rindex = Math.floor(Math.random() * texts.length);
                return texts[rindex];
            }
        }
    });
}

window.registerVue();


$(function () {
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


        // $('.typeahead').typeahead({
        //     source: [
        //     'afwfewf',
        //     'aefwerwewer',
        //     'brhegerghreg',
        //     'fhbrtybr'
        //     ]
        // });
    });

