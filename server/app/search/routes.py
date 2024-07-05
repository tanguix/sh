
from flask import Blueprint, request, jsonify, send_file
from app.logger import logger
from app.search.models import Collection
import os
# from app.database import db  # Make sure to import your database connection
from bson import ObjectId

# Blueprint object
search_bp = Blueprint('search', __name__)


# return all collections 
@search_bp.route('/api/collections', methods=['GET'])
def find_collection():
    try:
        # Get all collections from the database as a list of names (strings)
        collections = Collection.get_all_collections()

        # Filter out the 'users' collection if it exists
        filtered_collections = [collection for collection in collections if collection != 'users']

        # Return the filtered list of collections
        return jsonify({"collections": filtered_collections}), 200

    except Exception as e:
        logger.error(f"Error fetching collections: {e}")
        return jsonify({"error": "Internal server error"}), 500



# catch the collections, return all keys
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


# search document based on key-value pair
@search_bp.route('/api/searched_result', methods=['GET'])
def searched_result():
    collection_name = request.args.get('collection')
    key = request.args.get('key')
    value = request.args.get('value')

    if not collection_name or not key or not value:
        return jsonify({"error": "Collection, key, and value must be provided"}), 400

    try:
        # method is handled in the class
        results = Collection.search_by_key_value(collection_name, key, value)
        if results:
            # print(results)
            return jsonify(results), 200
        else:
            return jsonify({"error": "No matching documents found"}), 404
    except Exception as e:
        logger.error(f"Error searching collection {collection_name}: {e}")
        return jsonify({"error": "Internal server error"}), 500


# because image path is constructed during search_by_key_value() method in the models.py 
# so the url is already sent back to frontend <img> tag, and whenever <img> is needed to be display 
# this trigger the default url GET method, and send to here
@search_bp.route('/api/images/<filename>', methods=['GET'])
def get_image(filename):

    # Use absolute path relative to the main run.py, 
    # setting the current directory as basic directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # images folder is stored two levels up
    IMAGE_FOLDER = os.path.join(BASE_DIR, '../../images')
    # extract filename, construct file path
    image_path = os.path.join(IMAGE_FOLDER, filename)

    try:
        # send the file based on path
        return send_file(image_path, mimetype='image/png')

    except FileNotFoundError:
        return jsonify({"error": "Image not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching image {filename}: {e}")
        return jsonify({"error": "Internal server error"}), 500




@search_bp.route('/api/get_sample_tokens', methods=['POST'])
def get_sample_tokens():

    # temp: direct collection setup in the method

    try:
        data = request.json
        user_name = data.get('name')
        user_role = data.get('role')

        if not user_name or not user_role:
            return jsonify({"error": "Invalid user data"}), 400

        sample_tokens = Collection.search_sample_tokens_by_user(user_name, user_role)
        print(sample_tokens)

        # current user_name is simple assigned, make sure to modify it when it gets complex
        return jsonify({"sample_tokens": sample_tokens, "username": user_name}), 200
    except Exception as e:
        logger.error(f"Error fetching sample tokens: {e}")
        return jsonify({"error": str(e)}), 500





