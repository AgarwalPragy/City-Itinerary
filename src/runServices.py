from flask import Flask
from flask import send_file, send_from_directory, render_template
from flask_cors import CORS, cross_origin

from serviceCrawlerListingAcceptor import crawlerListingAcceptor
from serviceImageFetcher import imageFetcher
from serviceClientAPI import clientAPI

app = Flask(__name__)
app.config['SECRET_KEY'] = 'This is the secret key for now'
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={r"/foo": {"origins": "http://localhost:port"}})

app.register_blueprint(crawlerListingAcceptor)
app.register_blueprint(imageFetcher)
app.register_blueprint(clientAPI)


@app.route('/')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def index():
    return send_file('templates/index.html')


@app.route('/planner')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def planner():
    return render_template('planner.html', context={'initialConstraints': 'haha'})


@app.route('/city/<cityName>/')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def cityAttractions(cityName: str):
    return send_file('templates/city.html')


@app.route('/resources/<path:path>')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def resources(path):
    return send_from_directory('templates/resources/', path)


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


if __name__ == '__main__':
    app.run(debug=True)
