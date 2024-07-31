


from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename
from app.excel.models import ExcelProcessor
from app.logger import logger
import os

excel_bp = Blueprint('excel', __name__)


EXCEL_FOLDER = 'sheet'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}


# Ensure the directory exists
if not os.path.exists(EXCEL_FOLDER):
    os.makedirs(EXCEL_FOLDER)




def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@excel_bp.route('/api/excel_operations', methods=['GET'])
def get_operations():
    logger.info("Received request for allowed operations")
    try:
        operations = ExcelProcessor.get_allowed_operations()
        logger.info(f"Returning allowed operations: {operations}")
        return jsonify({'operations': operations}), 200
    except Exception as e:
        logger.error(f"Error fetching allowed operations: {str(e)}")
        return jsonify({'error': 'Failed to fetch allowed operations'}), 500

@excel_bp.route('/api/upload_excel', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(EXCEL_FOLDER, filename)
        file.save(filepath)
        
        try:
            summary = ExcelProcessor.process_excel(filepath)
            return jsonify({'summary': summary}), 200
        except Exception as e:
            logger.error(f"Error processing Excel file: {str(e)}")
            return jsonify({'error': 'Failed to process Excel file'}), 500
    else:
        return jsonify({'error': 'File type not allowed'}), 400


