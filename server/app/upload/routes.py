from flask import Blueprint, request, jsonify, send_file
import os
import json
from app.logger import logger
from app.upload.models import Item, ItemBatch, Workflow, File, HandleWorkflow 
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



@upload_bp.route('/api/upload_reference', methods=['POST'])
def upload_reference():
    try:
        data = request.json
        logger.info(f"Received data: {data}")
        full_name = data.get('fullName')
        abbreviation = data.get('abbreviation')
        
        if not full_name or not abbreviation:
            return jsonify({"error": "Both full name and abbreviation are required"}), 400
        
        success = Item.add_reference(full_name, abbreviation)
        
        if success:
            return jsonify({"message": "Reference added successfully"}), 200
        else:
            return jsonify({"error": "Failed to add reference"}), 500
    
    except ValueError as e:
        logger.error(f"ValueError in upload_reference: {str(e)}")
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        logger.error(f"Unexpected error in upload_reference: {str(e)}")
        return jsonify({"error": "An unexpected error occurred while uploading the reference"}), 500




@upload_bp.route('/api/fetch_reference_keys', methods=['GET'])
def fetch_reference_keys():
    try:
        references = Item.get_all_references()
        return jsonify(references), 200
    except Exception as e:
        logger.error(f"Error fetching reference keys: {str(e)}")
        return jsonify({"error": "An unexpected error occurred while fetching reference keys"}), 500




@upload_bp.route('/api/upload_data', methods=['POST'])
def upload_data():
    try:
        item = Item.from_form_data(request.form, request.files)
        result = item.save_item()
        return jsonify({
            "message": "Sample uploaded successfully",
            "result": {
                "id": str(result.inserted_id),
                "timestamp": item.timestamp
            }
        }), 200
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error uploading sample: {str(e)}")
        return jsonify({"error": "An unexpected error occurred while uploading the sample."}), 500





@upload_bp.route('/api/upload_sample', methods=['POST'])
def upload_sample():
    try:
        data = request.json
        if not isinstance(data, list):
            return jsonify({"error": "Invalid data format, expected a list of documents"}), 400
        
        mode = request.args.get('mode', 'normal')
        identifier = request.args.get('identifier')
        
        if not identifier:
            return jsonify({"error": "Identifier is required"}), 400
        
        sample_batch = ItemBatch(data, mode=mode, identifier=identifier)
        
        if data and '_remove' in data[0] and data[0]['_remove']:
            response = sample_batch.remove_item(data[0])
        else:
            response = sample_batch.save_items()
        
        return jsonify(response), 201
    except Exception as e:
        logger.exception(f"Error in upload_sample: {str(e)}")
        return jsonify({"error": str(e)}), 500



@upload_bp.route('/api/fetch_identifiers', methods=['GET'])
def fetch_identifiers():
    mode = request.args.get('mode')  # No default provided
    identifiers = ItemBatch.get_identifiers(mode)
    return jsonify({"identifiers": identifiers})



@upload_bp.route('/api/create_identifier', methods=['POST'])
def create_identifier():
    mode = request.args.get('mode', 'normal')
    name = request.json.get('name')
    
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    new_identifier = ItemBatch.create_identifier(mode, name)
    return jsonify({"identifier": new_identifier})





# --------------------------------------------- workflow operation ----------------------------------------------




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





