from flask import Blueprint, request
from flask_cors import cross_origin

crawlerListingAcceptor = Blueprint('crawlerListingAcceptor', __name__)


@crawlerListingAcceptor.route('/submit-listing', methods=['POST'])
@cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])
def submitListing():
    try:
        entityListing = request.args.get('listing')
        print(entityListing)
        # TODO: Save this listing to our mongo-db
        return 'success'
    except Exception as e:
        return str(e)
