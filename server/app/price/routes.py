

from flask import Blueprint, jsonify
from app.price.models import Price


price_bp = Blueprint('price', __name__)



@price_bp.route('/api/get_price_weight', methods=['GET'])
def get_price_weight():
    try:
        identifier = request.args.get('identifier')
        if not identifier:
            return jsonify({"error": "Identifier is required"}), 400

        price_weight_data = Price.get_price_weight_by_identifier(identifier)
        
        return jsonify(price_weight_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



