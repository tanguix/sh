

from flask import Blueprint, jsonify, request
from app.price.models import Price
import traceback

price_bp = Blueprint('price', __name__)

@price_bp.route('/api/get_price_weight', methods=['GET'])
def get_price_weight():
    try:
        identifier = request.args.get('identifier')
        view_mode = request.args.get('view_mode', 'normalized')
        
        if not identifier:
            return jsonify({"error": "Identifier is required"}), 400
        
        if view_mode not in ['normalized', 'separate']:
            return jsonify({"error": "Invalid view_mode. Must be 'normalized' or 'separate'"}), 400
        
        price_weight_data = Price.get_price_weight_by_identifier(identifier, view_mode)
        
        return jsonify(price_weight_data), 200
    except Exception as e:
        print(f"Error in get_price_weight: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500



