from flask import Blueprint, render_template, jsonify, request
from ..models import Postalcodes
from .. import db
# Blueprint Configuration
api_bp = Blueprint(
    'api_bp', __name__,
    url_prefix="/api",
)

@api_bp.route('/address', methods=['GET'])
def home():
    postcode = request.args.get("postcode")
    huisnummer = request.args.get("huisnummer")
    my = { "query": request.args,
          "address": {} }
    address = Postalcodes().query.filter(Postalcodes.postcode == postcode, Postalcodes.huisnummer == huisnummer).first()
    
    if address:
        my.update(
            {"address": address.to_dict() }
            )
        
    # db.session.commit()
    return jsonify(my)