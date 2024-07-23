from flask import Blueprint, request, jsonify, send_file
import os
import json
from app.logger import logger
from app.upload.models import Item, ItemBatch, Workflow, File, HandleWorkflow, json_serialize

# create Blueprint object, which is this file
upload_bp = Blueprint('upload', __name__)
# the folder for saving the uploaded sample image
# FILE_FOLDER = 'file'

# Assuming this is in routes.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))  # Go up two levels to reach 'server'
# TODO: need to make this path variable into some yml of config files, and it should only include the names of folder you want to store
IMAGE_FOLDER = os.path.join(SERVER_DIR, 'images')  # Changed from './file' to 'files'
FILE_FOLDER = os.path.join(SERVER_DIR, 'files')  # Changed from './file' to 'files'

# Ensure the directory exists
if not os.path.exists(FILE_FOLDER):
    os.makedirs(FILE_FOLDER)




@upload_bp.route('/api/upload_data', methods=['POST'])
def upload_data():
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)
    
    try:
        sample = Item.from_request(request, SERVER_DIR)
        sample.process_files()
        result = sample.save_item()
        return jsonify({
            "message": "Sample uploaded successfully",
            "id": str(result.inserted_id),
            "timestamp": sample.timestamp
        }), 200
    except ValueError as e:
        return jsonify({
            "error": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error uploading sample: {str(e)}")
        return jsonify({
            "error": "An unexpected error occurred while uploading the sample."
        }), 500



@upload_bp.route('/api/upload_sample', methods=['POST'])
def upload_sample():
    try:
        data = request.json
        
        if not isinstance(data, list):
            return jsonify({"error": "Invalid data format, expected a list of documents"}), 400
        
        sample_batch = ItemBatch(data)
        
        # Check if we're removing a sample
        if data and '_remove' in data[0] and data[0]['_remove']:
            sample_token = data[0].get('sample_token')
            if not sample_token:
                return jsonify({"error": "Sample token is required for removal"}), 400
            
            removed_ids = sample_batch.remove_sample(sample_token)
            response = {
                "message": "Sample removed successfully",
                "removed_ids": removed_ids,
                "sample_token": sample_token
            }
        else:
            # Regular save operation
            result = sample_batch.save_items()
            response = {
                "message": "Samples processed successfully", 
                "inserted_ids": result.inserted_ids,
                "updated_ids": result.modified_ids,
                "sample_token": sample_batch.main_sample_token
            }
        
        return jsonify(response), 201
    except Exception as e:
        logger.exception(f"Error in upload_sample: {str(e)}")
        return jsonify({"error": str(e)}), 500




# --------------------------------------------- collective operation ----------------------------------------------


# Update the API endpoint to handle potential multiple workflow error
@upload_bp.route('/api/workflow_commit', methods=['POST'])
def commit_changes():
    changes = request.json.get('changes')
    if not changes:
        return jsonify({"error": "No changes provided"}), 400

    results = HandleWorkflow.process_changes(changes)

    if any("error" in result for result in results):
        error_message = "Some changes could not be processed"
        status_code = 400
        status = "unsaved"

        if any(result.get("type") == "multiple_workflows" for result in results):
            error_message = "Cannot process changes for multiple workflows in a single request"
            status_code = 422  # Unprocessable Entity

        return jsonify({
            "message": error_message,
            "results": results,
            "status": status
        }), status_code
    else:
        return jsonify({
            "message": "All changes committed successfully",
            "results": results,
            "status": "saved"
        }), 200






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
            logger.debug(f"Workflow data: {workflow}")
            return jsonify(workflow), 200
        else:
            logger.warning(f"Workflow not found: {workflow_id}")
            return jsonify({"error": "Workflow not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching workflow {workflow_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500






@upload_bp.route('/api/fetch_locked_workflow', methods=['GET'])
def get_locked_workflows():
    try:
        locked_workflows = list(Workflow.get_locked_workflows())
        locked_workflow_ids = [w['workflow_id'] for w in locked_workflows]
        return jsonify(locked_workflow_ids), 200
    except Exception as e:
        logger.error(f"Error fetching locked workflows: {str(e)}")
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
    print(absolute_path)
    logger.info(f"Attempting to send file: {absolute_path}")
    
    try:
        return send_file(absolute_path, as_attachment=True, download_name=file_info['name'])
    except Exception as e:
        logger.error(f"Error sending file: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500








# ------------------------------------------ indivdual operation -------------------------------------------------
# maybe you need in the future
