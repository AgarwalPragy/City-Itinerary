from flask import Flask, request
from flask import send_file, send_from_directory, render_template
from flask_cors import CORS, cross_origin
import datetime
import json
import urllib

from serviceCrawlerListingAcceptor import crawlerListingAcceptor
from serviceImageFetcher import imageFetcher
from serviceClientAPI import clientAPI, getNumDays
from tunable import clientDefaultStartTime, clientDefaultEndTime, clientDefaultTripLength, clientDefaultCity
from utilities import urlDecode

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


@app.route('/favicon.png')
def favicon():
    return send_from_directory('templates/', 'favicon.png')


@app.route('/planner')
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def planner():
    cityName = clientDefaultCity
    cityName = request.args.get('city', cityName)
    if cityName:
        cityName = urlDecode(cityName)

    strFormat = '%y/%m/%d'
    startDate = datetime.datetime.now().strftime(strFormat)
    endDate = (datetime.datetime.now() + datetime.timedelta(days=clientDefaultTripLength-1)).strftime(strFormat)
    startDayTime, endDayTime = clientDefaultStartTime, clientDefaultEndTime

    startDate = request.args.get('startDate', startDate)
    endDate = request.args.get('endDate', endDate)
    startDayTime = float(request.args.get('startDayTime', startDayTime))
    endDayTime = float(request.args.get('endDayTime', endDayTime))

    numDays = getNumDays(startDate, endDate)
    likes = request.args.get('likes', [])
    likesTimings = request.args.get('likesTimings', [])
    mustVisit = {dayNum: [] for dayNum in range(1, numDays + 1)}

    if likes and likesTimings:
        likes = list(map(urlDecode, likes.split('|')))
        likesTimings = list(map(urlDecode, likesTimings.split('|')))

        for pointName, timing in zip(likes, likesTimings):
            dayNum, enterTime, exitTime = map(float, timing.split('-'))
            mustVisit[dayNum].append((enterTime, exitTime, pointName))
        for dayNum in mustVisit:
            mustVisit[dayNum] = list(sorted(mustVisit[dayNum]))

    dislikes = request.args.get('dislikes', [])
    if dislikes:
        dislikes = list(map(urlDecode, dislikes.split('|')))

    constraints = {
        'city': cityName,
        'likes': likes,
        'likesTimings': likesTimings,
        'dislikes': dislikes,
        'startDate': startDate,
        'endDate': endDate,
        'startDayTime': startDayTime,
        'endDayTime': endDayTime,
        'page': 1
    }

    return render_template('planner.html', initialConstraints=json.dumps(constraints))


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
    app.run(host='0.0.0.0', debug=True)
