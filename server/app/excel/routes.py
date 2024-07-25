


from flask import Blueprint, jsonify
from app.excel.models import ExcelProcessor
from app.logger import logger

excel_bp = Blueprint('excel', __name__)

@excel_bp.route('/api/operations', methods=['GET'])
def get_operations():
    logger.info("Received request for allowed operations")
    try:
        operations = ExcelProcessor.get_allowed_operations()
        logger.info(f"Returning allowed operations: {operations}")
        return jsonify({'operations': operations}), 200
    except Exception as e:
        logger.error(f"Error fetching allowed operations: {str(e)}")
        return jsonify({'error': 'Failed to fetch allowed operations'}), 500



