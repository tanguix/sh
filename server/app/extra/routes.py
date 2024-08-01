
from flask import Blueprint, jsonify
from app.extra.models import ExchangeRate

extra_bp = Blueprint('extra', __name__)

@extra_bp.route('/api/exchange_rate', methods=['GET'])
def get_exchange_rate():
    try:
        exchange_rate = ExchangeRate.get_latest_rate()
        
        return jsonify(exchange_rate), 200
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500



