var utils = {}

utils.cityImageUnavailable = 'http://getdrawings.com/img/gotham-city-silhouette-14.png';
utils.pointImageUnavailable = 'http://getdrawings.com/img/gotham-city-silhouette-14.png';


utils.getData = function(url, params, callback) {
    console.log('Got a call for ' + url + ' with params:');
    console.log(params);
    axios.get(url, {
        params: params
    }).then(function(response) {
        console.log('Request for ' + url + ' with params:')
        console.log(params)
        console.log('resulted in:');
        console.log(response.data);
        callback(response);
    });
};

utils.padString = function(str, filler, minLength) {
    var str = str + '';
    return str.length >= minLength ? str : new Array(minLength - str.length + 1).join(filler) + str;
};

utils.getCoordinatesFromString = function(coordinates) {
    coordinates = coordinates.split(',')
    console.log(coordinates);
    lat = parseFloat(coordinates[0]);
    long = parseFloat(coordinates[1]);
    return [lat, long];
};

utils.formatTime = function(amount) {
    var hours = Math.floor(amount);
    var minutes = Math.floor((amount - hours) * 60);
    return utils.padString(hours, '0', 2) + ':' + utils.padString(minutes, '0', 2);
};

utils.fetchImageURL = function(url, width, height) {
    return '/api/fetch-image?url=' + encodeURIComponent(url) + '&width=' + width + '&height=' + height;
};

utils.getEncodedPointImageURL = function(point, width, height) {
    var images = point.images;
    var url = '';
    if(images && images.length > 0)
        url = images[0]['imageURL'];
    else
        url = utils.pointImageUnavailable;
    return utils.fetchImageURL(url, width, height);
};

utils.getEncodedCityImageURL = function (city, width, height) {
    var images = city.images;
    var url = '';
    if(images && images.length > 0)
        url = utils.chooseRandomElement(images)['imageURL'];
    else
        url = utils.cityImageUnavailable;
    return utils.fetchImageURL(url, width, height);
};


utils.chooseRandomElement = function(items) {
    var rindex = Math.floor(Math.random() * items.length);
    return items[rindex];
};