from flask import Blueprint, request, jsonify, send_file, abort
import os
import json
from app.logger import logger
from app.upload.models import Item, ItemBatch, Workflow, File

# create Blueprint object, which is this file
upload_bp = Blueprint('upload', __name__)
# the folder for saving the uploaded sample image
# FILE_FOLDER = 'file'

# Assuming this is in routes.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))  # Go up two levels to reach 'server'
IMAGE_FOLDER = os.path.join(SERVER_DIR, 'image')  # Changed from './file' to 'files'
FILE_FOLDER = os.path.join(SERVER_DIR, 'files')  # Changed from './file' to 'files'

# Ensure the directory exists
if not os.path.exists(FILE_FOLDER):
    os.makedirs(FILE_FOLDER)



@upload_bp.route('/api/upload_data', methods=['POST'])
def upload_data():
    # create the folder if doesn't exist
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)

    # get all the data from multi-value form: files.get() for "image" and form.get() for "text"
    image_file = request.files.get('image')
    reference_no = request.form.get('reference_no')
    categories = request.form.get('categories')
    tags = request.form.get('tags')
    additional_fields = request.form.get('additional_fields')

    # all these variable sends array back, so load them
    if tags:
        tags = json.loads(tags)
    if categories:
        categories = json.loads(categories)
    if additional_fields:
        additional_fields = json.loads(additional_fields)

    # create path variable for holding the path where image gonna be saved to
    # in the database, you only save path, not the whole image file
    image_file_path = None
    # check if image file received
    if image_file:
        image_file_path = os.path.join(IMAGE_FOLDER, image_file.filename)
        image_file.save(image_file_path)

    # create Item object
    # =========== add check method in the model.py to check if refernece number is unique, otherwise prevent inserting ==========
    # to-do

    sample = Item(reference_no, categories, tags, additional_fields, image_file_path)
    # save_item() method that insert data into database
    result = sample.save_item()
    return jsonify({"message": "Sample uploaded successfully", "id": str(result.inserted_id)}), 200



@upload_bp.route('/api/upload_sample', methods=['POST'])
def upload_sample():
    try:
        data = request.json  # receive data from frontend
        
        # Check if data is a list
        if not isinstance(data, list):
            return jsonify({"error": "Invalid data format, expected a list of documents"}), 400

        # Create ItemBatch object and save items
        sample_batch = ItemBatch(data)
        result = sample_batch.save_items()
        
        return jsonify({
            "message": "Samples uploaded successfully", 
            "inserted_ids": [str(id) for id in result.inserted_ids], 
            "sample_token": sample_batch.sample_token}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500




# --------------------------------------------- collective operation ----------------------------------------------
# WorkFlow section backend handling
# from app.upload.models import Workflow, Node, Section, File
from app.upload.models import HandleWorkflow






# Flask route remains the same
@upload_bp.route('/api/workflow_commit', methods=['POST'])
def commit_changes():
    changes = request.json.get('changes')
    if not changes:
        return jsonify({"error": "No changes provided"}), 400

    results = HandleWorkflow.process_changes(changes)

    if any("error" in result for result in results):
        return jsonify({
            "message": "Some changes could not be processed",
            "results": results
        }), 400
    else:
        return jsonify({
            "message": "All changes committed successfully",
            "results": results
        }), 200




# def commit_changes():
#     try:
#         changes = request.json.get('changes')
#         if not changes:
#             return jsonify({"error": "No changes provided"}), 400
#         print("Received changes:")
#         for i, change in enumerate(changes):
#             print(f"{i}: {change}")
#         results = []
#         for change in changes:
#             try:
#                 print(f"Processing change: {change['type']}")
#                 result = HandleWorkflow.process_change(change['type'], change['data'])
#                 print(f"Result of {change['type']}: {result}")
#                 results.append(result)
#             except KeyError as e:
#                 print(f"KeyError in {change['type']}: {str(e)}")
#                 return jsonify({"error": f"Missing key in change data for {change['type']}: {str(e)}"}), 400
#             except ValueError as e:
#                 print(f"ValueError in {change['type']}: {str(e)}")
#                 return jsonify({"error": str(e)}), 400
#         return jsonify({
#             "message": "Changes committed successfully",
#             "results": results
#         }), 200
#     except Exception as e:
#         print(f"Unexpected error: {str(e)}")
#         return jsonify({"error": str(e)}), 500



@upload_bp.route('/api/fetch_all_workflow', methods=['GET'])
def get_workflow():
    workflow_id = request.args.get('workflow_id')
    logger.info(f"Requested workflow_id: {workflow_id}")
    
    if not workflow_id:
        logger.error("Workflow ID not provided")
        return jsonify({"error": "Workflow ID must be provided"}), 400

    try:
        workflow = Workflow.get_workflow_by_id(workflow_id)
        if workflow:
            logger.info(f"Successfully fetched workflow: {workflow_id}")
            logger.debug(f"Workflow data: {workflow}")  # Ad            
            return jsonify(workflow), 200
        else:
            logger.warning(f"Workflow not found: {workflow_id}")
            return jsonify({"error": "Workflow not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching workflow {workflow_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500



@upload_bp.route('/api/upload_file', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    files = request.files.getlist('files')
    workflow_id = request.form.get('workflow_id')
    node_id = request.form.get('node_id')
    section_id = request.form.get('section_id')
    file_data_array = json.loads(request.form.get('file_data'))

    logger.info(f"Received upload request for workflow_id: {workflow_id}, node_id: {node_id}, section_id: {section_id}")
    logger.info(f"Number of files: {len(files)}, File data: {file_data_array}")

    if len(files) != len(file_data_array):
        return jsonify({"error": "Mismatch between files and file data"}), 400

    results = File.process_multiple_uploads(files, file_data_array, workflow_id, node_id, section_id, FILE_FOLDER)

    successful_uploads = [r for r in results if "message" in r]
    failed_uploads = [r for r in results if "error" in r]

    logger.info(f"Upload results: {results}")
    logger.info(f"Successful uploads: {len(successful_uploads)}, Failed uploads: {len(failed_uploads)}")

    if len(successful_uploads) == len(files):
        return jsonify({"message": "All files uploaded successfully", "results": results}), 200
    elif len(successful_uploads) > 0:
        return jsonify({"message": "Some files uploaded successfully", "results": results}), 207
    else:
        logger.error(f"All file uploads failed. Results: {results}")
        return jsonify({"error": "All file uploads failed", "results": results}), 500




@upload_bp.route('/api/download_file/<workflow_id>/<node_id>/<section_id>/<file_id>', methods=['GET'])
def download_file(workflow_id, node_id, section_id, file_id):
    file_info, error = File.get_file_for_download(workflow_id, node_id, section_id, file_id)
    
    if error:
        logger.error(f"Error retrieving file: {error}")
        return jsonify({"error": error}), 404
    
    absolute_path = os.path.join(SERVER_DIR, file_info['path'])
    logger.info(f"Attempting to send file: {absolute_path}")
    
    try:
        return send_file(absolute_path, as_attachment=True, download_name=file_info['name'])
    except Exception as e:
        logger.error(f"Error sending file: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500








# ------------------------------------------ indivdual operation -------------------------------------------------
# maybe you need in the future
