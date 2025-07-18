from flask import Blueprint, render_template, jsonify, request
from bcource.models import Postalcodes
from bcource import db
from flask_security import auth_required
import re

# Blueprint Configuration
api_bp = Blueprint(
    'api_bp', __name__,
    url_prefix="/api",
)


def validate_adress(query):
    
    r = {}

    if query:
        r["postcode"] = query.get("postcode","")
        r["huisnummer"] = query.get("huisnummer","")
        ext = query.get("ext")
        
        
        if ext != None and ext !="":
            r["huisnummer"] = f'{r["huisnummer"]}-{ext}'
            
    else:
        return False
    
    if not r["postcode"] or not r["huisnummer"]:
        return False
    
    r["postcode"] = r["postcode"].replace(' ','')
    
    if not re.search(r"^[0-9]{4}\w{2}", r["postcode"]):
        return False
    # try:
    #     int(huisnummer)
    # except:
    #     return False

    return r

@api_bp.route('/address', methods=['POST'])
@auth_required()
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

