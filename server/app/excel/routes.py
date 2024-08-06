


from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename
from app.excel.models import ExcelProcessor
from app.logger import logger
from urllib.parse import unquote
import json

excel_bp = Blueprint('excel', __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}




def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@excel_bp.route('/api/append_excel_files', methods=['POST'])
def append_excel_data():
    if 'filename' not in request.form or 'data' not in request.form or 'is_new_file' not in request.form:
        return jsonify({'error': 'Missing filename, data, or is_new_file flag'}), 400

    filename = request.form['filename']
    data = request.form['data']
    is_new_file = request.form['is_new_file'].lower() == 'true'

    try:
        result, status_code = ExcelProcessor.append_data(filename, data, is_new_file)
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error appending data to Excel file: {str(e)}")
        return jsonify({'error': f'Failed to append data to Excel file: {str(e)}'}), 500




@excel_bp.route('/api/upload_excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        result, status_code = ExcelProcessor.save_uploaded_file(file)
        return jsonify(result), status_code
    else:
        return jsonify({'error': 'File type not allowed'}), 400



@excel_bp.route('/api/list_excel_files', methods=['GET'])
def list_excel_files():
    result, status_code = ExcelProcessor.list_excel_files()
    return jsonify(result), status_code






@excel_bp.route('/api/ds_operations', methods=['GET'])
def get_operations():
    operations = ExcelProcessor.get_allowed_operations()
    return jsonify({'operations': operations}), 200



@excel_bp.route('/api/process_excel', methods=['GET'])
def process_excel():
    filename = unquote(request.args.get('filepath', ''))
    operations = request.args.get('operations', '').split(',')
    selected_columns = request.args.get('columns', '').split(',') if request.args.get('columns') else None
    
    if not filename or not operations:
        return jsonify({'error': 'Missing filename or operations'}), 400
    
    try:
        results, status_code = ExcelProcessor.process_excel(filename, operations, selected_columns)
        return jsonify(results), status_code
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        return jsonify({'error': 'Failed to process Excel file'}), 500



@excel_bp.route('/api/get_columns', methods=['GET'])
def get_columns():
    filename = unquote(request.args.get('filepath', ''))
    
    if not filename:
        return jsonify({'error': 'No file name provided'}), 400
    
    result, status_code = ExcelProcessor.get_columns(filename)
    return jsonify(result), status_code


