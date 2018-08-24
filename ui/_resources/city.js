window.addEventListener("keyup", function(e) {
    console.log(e.keyCode);
    console.log(String.fromCharCode(e.keyCode));
}.bind(this));

function getData(url) {
    console.log(url);
    console.log('getting data...');
    axios.get(url).then(function(response) {
            console.log(response.data);
            window.app.itemlists = response.data;
    });
}

window.registerVue = function() {
    window.app = new Vue({
        el: '#container',
        data: {
            itemlists: []
        },
        mounted: function() {
            getData('http://127.0.0.1:5000');
        },
        methods: {
            changeFocus: function(nid) {
                getData('http://127.0.0.1:5000/' + nid);
            }
        }
    });
}

