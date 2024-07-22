
from app.database import db
from app.logger import logger
import time

from flask import current_app   # this line is for importing the config.py 

# define the keys you want to exclude when frontend request all keys
exclude_keys = {"_id", "quantity", "password", "role", "authToken", "image_path"}
backend_local_url = current_app.config['BACKEND_LOCAL_URL']     # correct way of using predefined variable in config.py


# most likely, this class is all method, right now it doesn't have data to initialize
class Collection:


    @staticmethod
    def get_all_collections():
        '''
        you can test the url, by printing out "backend_local_url" variable
        '''
        # print("your local host", backend_local_url)
        return db.list_collection_names()       # return all collections name in a database


    @staticmethod
    def get_keys(collection_name):
        # Check if collection_name passed in is valid
        if collection_name in db.list_collection_names():
            # later add checks, whenever a collection is created, make sure asking for scheme 
            # so at here you can display key options by querying scheme 
            # also add check if no scheme found, then use the below find random document and extract keys
            sample_document = db[collection_name].find_one()

            if sample_document:
                # Initialize a set to store the keys for efficient handling
                keys = set()

                # Iterate over the document's items
                for key, value in sample_document.items():
                    if key == "additional_fields" and isinstance(value, dict):
                        # Add keys from additional_fields
                        keys.update(value.keys())
                    elif key not in exclude_keys:
                        # Add keys from the main document, excluding sensitive ones and additional_fields itself
                        keys.add(key)

                return list(keys)
        return None



    @staticmethod
    def search_by_key_value(collection_name, key, value):
        if collection_name not in db.list_collection_names():
            return None

        sample_document = db[collection_name].find_one()
        if not sample_document:
            return None

        # Split the value into an array if it contains commas
        search_values = [v.strip() for v in value.split(',')] if ',' in value else [value.strip()]

        # Determine if the key is in the main document or in additional_fields
        if key in sample_document:
            field_path = key
        else:
            field_path = f"additional_fields.{key}"

        # Create a query based on whether the field is an array or not
        if isinstance(sample_document.get(key, sample_document.get('additional_fields', {}).get(key)), list):
            # If the field is an array, use $all for multiple values or $in for a single value
            query = {field_path: {"$all": search_values} if len(search_values) > 1 else {"$in": search_values}}
        else:
            # If the field is not an array, use exact match
            query = {field_path: value}

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
        query = {"modifiedBy": {"$elemMatch": {"name": user_name, "role": user_role}}}
        documents = db.samples_list.find(query, {"sample_token": 1, "timestamp": 1, "_id": 0})
        
        # Create a list of dictionaries containing sample_token and timestamp
        sample_token_data = [
            {"sample_token": doc["sample_token"], "timestamp": doc.get("timestamp", 0)}
            for doc in documents
        ]
        
        # Sort the list based on timestamp in descending order (newest first)
        sorted_sample_token_data = sorted(sample_token_data, key=lambda x: x["timestamp"], reverse=False)
        
        # Extract only the sample_tokens from the sorted list
        sorted_sample_tokens = [item["sample_token"] for item in sorted_sample_token_data]
        
        return sorted_sample_tokens





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



