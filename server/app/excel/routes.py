


from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename
from app.excel.models import ExcelProcessor
from app.logger import logger
import os
from urllib.parse import unquote

excel_bp = Blueprint('excel', __name__)
EXCEL_FOLDER = 'sheet'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




@excel_bp.route('/api/list_excel_files', methods=['GET'])
def list_excel_files():
    try:
        files = [f for f in os.listdir(EXCEL_FOLDER) if f.endswith(('.xlsx', '.xls'))]
        return jsonify(files), 200
    except Exception as e:
        logger.error(f"Error listing Excel files: {str(e)}")
        return jsonify({'error': 'Failed to list Excel files'}), 500




@excel_bp.route('/api/append_excel_files', methods=['POST'])
def append_excel_data():
    if 'filename' not in request.form or 'data' not in request.form or 'is_new_file' not in request.form:
        return jsonify({'error': 'Missing filename, data, or is_new_file flag'}), 400

    filename = request.form['filename']
    data = request.form['data']
    is_new_file = request.form['is_new_file'].lower() == 'true'

    if is_new_file:
        if not filename.endswith(('.xlsx', '.xls')):
            filename += '.xlsx'
        filepath = os.path.join(EXCEL_FOLDER, filename)
        if os.path.exists(filepath):
            return jsonify({'error': 'File already exists'}), 400
    else:
        filepath = os.path.join(EXCEL_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

    try:
        ExcelProcessor.append_data(filepath, data, is_new_file)
        return jsonify({'message': 'Data appended successfully'}), 200
    except Exception as e:
        logger.error(f"Error appending data to Excel file: {str(e)}")
        return jsonify({'error': 'Failed to append data to Excel file'}), 500





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
def upload_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        try:
            os.makedirs(EXCEL_FOLDER, exist_ok=True)
            filepath = os.path.join(EXCEL_FOLDER, filename)
            file.save(filepath)
            return jsonify({'message': 'File uploaded successfully', 'filepath': filepath}), 200
        except OSError as e:
            logger.error(f"OS error occurred when saving file: {str(e)}")
            return jsonify({'error': 'Failed to save file due to system error'}), 500
    else:
        return jsonify({'error': 'File type not allowed'}), 400




@excel_bp.route('/api/process_excel', methods=['GET'])
def process_excel():
    filepath = unquote(request.args.get('filepath', ''))
    operations = request.args.get('operations', '').split(',')
    
    if not filepath:
        return jsonify({'error': 'No file path provided'}), 400
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    if not operations:
        return jsonify({'error': 'No operations selected'}), 400
    
    try:
        results = ExcelProcessor.process_excel(filepath, operations)
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        return jsonify({'error': 'Failed to process Excel file'}), 500


