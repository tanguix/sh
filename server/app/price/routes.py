

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


@price_bp.route('/api/search_document', methods=['GET'])
def search_document():
    try:
        reference_no = request.args.get('reference_no')
        
        if not reference_no:
            return jsonify({"error": "Reference number is required"}), 400
        
        document_data = Price.get_document_by_reference_no(reference_no)
        
        if not document_data:
            return jsonify({"error": "Document not found"}), 404
        
        return jsonify(document_data), 200
    except Exception as e:
        print(f"Error in search_document: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
