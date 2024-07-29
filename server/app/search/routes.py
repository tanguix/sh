

from flask import Blueprint, request, jsonify, send_file, current_app
from app.logger import logger
from app.search.models import Collection, ExchangeRate
import os
import json

search_bp = Blueprint('search', __name__)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
IMAGE_FOLDER = os.path.join(SERVER_DIR, 'images')
FILE_FOLDER = os.path.join(SERVER_DIR, 'files')

if not os.path.exists(FILE_FOLDER):
    os.makedirs(FILE_FOLDER)

@search_bp.route('/api/collections', methods=['GET'])
def find_collection():
    try:
        collections = Collection.get_all_collections()
        filtered_collections = [collection for collection in collections if collection != 'users']
        return jsonify({"collections": filtered_collections}), 200
    except Exception as e:
        logger.error(f"Error fetching collections: {e}")
        return jsonify({"error": "Internal server error"}), 500

@search_bp.route('/api/keys', methods=['GET'])
def find_key():
    collection_name = request.args.get('collection')
    if not collection_name:
        return jsonify({"error": "Collection name must be provided"}), 400

    try:
        keys = Collection.get_keys(collection_name)
        if keys:
            return jsonify({"keys": keys}), 200
        else:
            return jsonify({"error": "No documents found in the collection"}), 404
    except Exception as e:
        logger.error(f"Error fetching keys for {collection_name}: {e}")
        return jsonify({"error": "Internal server error"}), 500




@search_bp.route('/api/searched_result', methods=['GET'])
def searched_result():
    collection_name = request.args.get('collection')
    criteria = json.loads(request.args.get('criteria', '[]'))
    logger.info(f"Received search request for collection: {collection_name}, criteria: {criteria}")
    
    if not collection_name or not criteria:
        logger.error("Collection and search criteria must be provided")
        return jsonify({"error": "Collection and search criteria must be provided"}), 400

    try:
        backend_local_url = current_app.config['BACKEND_LOCAL_URL']
        results, count = Collection.search_by_multiple_criteria(collection_name, criteria, backend_local_url)
        if results:
            logger.info(f"Search successful. Returned {count} results.")
            return jsonify({"results": results, "count": count}), 200
        else:
            logger.info(f"No matching documents found for query in collection {collection_name}")
            return jsonify({"error": "No matching documents found", "count": 0}), 404
    except Exception as e:
        logger.error(f"Error searching collection {collection_name}: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500




@search_bp.route('/api/images/<path:filename>', methods=['GET'])
def get_image(filename):
    image_path = os.path.join(IMAGE_FOLDER, filename)
    logger.info(f"Attempting to serve image: {image_path}")
    try:
        return send_file(image_path, mimetype='image/jpeg')
    except FileNotFoundError:
        logger.error(f"Image not found: {image_path}")
        return jsonify({"error": "Image not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching image {filename}: {e}")
        return jsonify({"error": "Internal server error"}), 500




@search_bp.route('/api/get_sample_tokens', methods=['POST'])
def get_sample_tokens():
    try:
        data = request.json
        user_name = data.get('name')
        user_role = data.get('role')
        if not user_name or not user_role:
            return jsonify({"error": "Invalid user data"}), 400
        
        sorted_sample_tokens = Collection.search_sample_tokens_by_user(user_name, user_role)
        return jsonify({"sample_tokens": sorted_sample_tokens, "username": user_name}), 200
    except Exception as e:
        logger.error(f"Error in get_sample_tokens: {str(e)}")
        return jsonify({"error": str(e)}), 500




@search_bp.route('/api/get_workflow_tokens', methods=['POST'])
def get_workflow_tokens():
    try:
        data = request.json
        user_name = data.get('name')
        user_role = data.get('role')
        if not user_name or not user_role:
            return jsonify({"error": "Invalid user data"}), 400
        workflow_tokens = Collection.search_workflow_tokens_by_user(user_name, user_role)
        return jsonify({"workflow_tokens": workflow_tokens, "username": user_name}), 200
    except Exception as e:
        logger.error(f"Error fetching workflow tokens: {e}")
        return jsonify({"error": str(e)}), 500




@search_bp.route('/api/exchange_rate', methods=['GET'])
def get_exchange_rate():
    try:
        exchange_rate = ExchangeRate.get_latest_rate()
        return jsonify(exchange_rate), 200
    except Exception as e:
        logger.error(f"Error fetching exchange rate: {e}")
        return jsonify({"error": "Internal server error"}), 500






@search_bp.route('/api/categories_and_tags', methods=['GET'])
def get_categories_and_tags():
    logger.info("Received request for categories and tags")
    try:
        logger.debug("Attempting to fetch categories and tags from the database")
        categories, tags = Collection.get_categories_and_tags()
        logger.info(f"Successfully fetched {len(categories)} categories and {len(tags)} tags")
        logger.debug(f"Categories: {categories}")
        logger.debug(f"Tags: {tags}")
        return jsonify({"categories": categories, "tags": tags}), 200
    except Exception as e:
        logger.error(f"Error fetching categories and tags: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
