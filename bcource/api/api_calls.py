from flask import Blueprint, render_template, jsonify, request
from bcource.api.models import Postalcodes
from bcource import db
import re

# Blueprint Configuration
api_bp = Blueprint(
    'api_bp', __name__,
    url_prefix="/api",
)


def validate_adress(query):
    if query:
        postcode = query.get("postcode")
        huisnummer = query.get("huisnummer")
    else:
        return False
    
    print (query)
    if not postcode or not huisnummer:
        return False
    
    postcode = postcode.replace(' ','')
    
    if not re.search("^[0-9]{4}\w{2}", postcode):
        return False
    try:
        int(huisnummer)
    except:
        return False

    return query

@api_bp.route('/address', methods=['POST'])
# @csrf.exempt
def adress():
    
    r = {}
    query = validate_adress(request.form)
    if not query:
        r.update({"status": 400, "status_message": "Address not Found"})
        return jsonify(r)
    
    
    address = Postalcodes().query.filter(
        Postalcodes.postcode == query["postcode"].replace(' ',''), 
        Postalcodes.huisnummer == query["huisnummer"]).first()
    
    if address:
        r.update(
            address.to_dict()
            )
        r.update({"status": 200, "status_message": "Address Found"})
    else:
        r.update({"status": 400, "status_message": "Address not Found"})
        
    db.session.commit()
    

    return jsonify(r)

