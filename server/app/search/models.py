from app.database import db
from app.logger import logger
import time
from collections import defaultdict
from bson.int64 import Int64
from bson import json_util
import json
from flask import current_app

# define the keys you want to exclude when frontend requests all keys
exclude_keys = {"_id", "quantity", "password", "role", "authToken", "image_path"}
backend_local_url = current_app.config['BACKEND_LOCAL_URL']

class Collection:
    @staticmethod
    def get_all_collections():
        return db.list_collection_names()

    @staticmethod
    def get_keys(collection_name):
        if collection_name in db.list_collection_names():
            sample_document = db[collection_name].find_one()
            if sample_document:
                keys = set()
                for key, value in sample_document.items():
                    if key == "additional_fields" and isinstance(value, dict):
                        keys.update(value.keys())
                    elif key not in exclude_keys:
                        keys.add(key)
                return list(keys)
        return None

    @staticmethod
    def search_by_multiple_criteria(collection_name, criteria):
        if collection_name not in db.list_collection_names():
            return None

        query = {"$and": []}
        for criterion in criteria:
            key = criterion['key']
            value = criterion['value']

            search_values = [v.strip() for v in value.split(',')] if ',' in value else [value.strip()]

            field_path = key if key in db[collection_name].find_one() else f"additional_fields.{key}"

            if isinstance(db[collection_name].find_one().get(key, db[collection_name].find_one().get('additional_fields', {}).get(key)), list):
                query["$and"].append({field_path: {"$all": search_values} if len(search_values) > 1 else {"$in": search_values}})
            else:
                query["$and"].append({field_path: {"$in": search_values} if len(search_values) > 1 else value})

        results = list(db[collection_name].find(query))
        processed_results = []

        for result in results:
            processed_result = {}
            for k, v in result.items():
                if k in exclude_keys and k != "image_path":
                    continue
                if k == "additional_fields":
                    processed_result.update(v)
                elif k == 'image_path':
                    image_path = v[7:] if v.startswith('images/') else v
                    image_url = f"{backend_local_url}/search/api/images/{image_path}"
                    processed_result['image_url'] = image_url
                    logger.info(f"Image URL constructed: {image_url}")
                else:
                    processed_result[k] = v

            processed_results.append(processed_result)

        logger.info(f"Processed results: {processed_results}")
        return processed_results



    @staticmethod
    def search_sample_tokens_by_user(user_name, user_role):
        # First, let's check how many documents match our criteria
        match_count = db.samples_list.count_documents({
            "modifiedBy": {
                "$elemMatch": {
                    "name": user_name,
                    "role": user_role
                }
            }
        })
        print(f"Documents matching user criteria: {match_count}")

        pipeline = [
            # Match documents modified by the specific user
            {
                "$match": {
                    "modifiedBy": {
                        "$elemMatch": {
                            "name": user_name,
                            "role": user_role
                        }
                    }
                }
            },
            # Sort all documents by timestamp in descending order
            {
                "$sort": {"timestamp": 1}
            },
            # Group by sample_token, keeping the first (most recent) document for each
            {
                "$group": {
                    "_id": "$sample_token",
                    "doc": {"$first": "$$ROOT"}
                }
            },
            # Project only the sample_token and timestamp
            {
                "$project": {
                    "_id": 0,
                    "sample_token": "$_id",
                    "timestamp": "$doc.timestamp"
                }
            },
            # Final sort to ensure the most recent tokens are first
            {
                "$sort": {"timestamp": 1}
            }
        ]
        
        result = list(db.samples_list.aggregate(pipeline))
        print(f"Aggregation result: {json.dumps(result, default=json_util.default)}")
        return [doc['sample_token'] for doc in result]




    @staticmethod
    def search_workflow_tokens_by_user(user_name, user_role):
        query = {"owner": [user_name, user_role]}
        documents = db.workflows.find(query, {"workflow_id": 1, "timestamp": 1, "_id": 0})
        
        # Create a list of dictionaries containing workflow_id and timestamp
        workflow_token_data = [
            {
                "workflow_id": doc["workflow_id"], 
                "timestamp": doc.get("timestamp", int(time.time() * 1000))  # Use current time if no timestamp
            }
            for doc in documents
        ]
        
        # Sort the list based on timestamp in descending order (newest first)
        sorted_workflow_token_data = sorted(workflow_token_data, key=lambda x: x["timestamp"], reverse=False)
        
        # Extract only the workflow_ids from the sorted list
        sorted_workflow_tokens = [item["workflow_id"] for item in sorted_workflow_token_data]
        
        return sorted_workflow_tokens
