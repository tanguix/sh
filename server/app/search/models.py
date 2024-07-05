
from app.database import db
import os
from app.logger import logger

# define the keys you want to exclude when frontend request all keys
exclude_keys = {"_id", "quantity", "password", "role", "authToken", "image_path"}


# most likely, this class is all method, right now it doesn't have data to initialize
class Collection:

    @staticmethod
    def get_all_collections():
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
    # Pass in collection name, based key you want to make the search on, your search value
    def search_by_key_value(collection_name, key, value):
        # Check
        if collection_name not in db.list_collection_names():
            return None

        # Return all keys from selected collections, later use scheme to do this as well
        sample_document = db[collection_name].find_one()
        if not sample_document:
            return None

        # Check if keys is in the scheme key list, if not check nested keys
        # Create query based those keys and searched value, e.g. {"tag": "white"} or {"additional_fields.weight": "light"}
        query = {key: value} if key in sample_document else {f"additional_fields.{key}": value}

        # Find all matched document with constructed query structure {key: value}
        results = list(db[collection_name].find(query))
        # Result list
        processed_results = []

        # Construct new document to send back, because some keys you don't want to send back
        for result in results:
            processed_result = {}
            for k, v in result.items():
                # Exclude keys in the black list
                if k in exclude_keys and k != "image_path":
                    continue
                if k == "additional_fields":
                    processed_result.update(v)  # Include additional fields directly

                # Construct the path url for frontend <img> to open
                elif k == 'image_path':
                    image_url = f"http://localhost:5000/search/api/images/{os.path.basename(v)}"
                    processed_result['image_url'] = image_url

                # Normal handling {key: value}
                else:
                    processed_result[k] = v

            # Append result
            processed_results.append(processed_result)
            print(processed_results)
        return processed_results


    @staticmethod
    def search_sample_tokens_by_user(user_name, user_role):
        # make the collection select more flexible later
        query = {"modifiedBy": {"$elemMatch": {"name": user_name, "role": user_role}}}
        documents = db.samples_list.find(query, {"sample_token": 1, "_id": 0})
        # this make the result into a set, {} parentheses means a set, not "set" operator is needed
        sample_tokens = {doc["sample_token"] for doc in documents}
        return list(sample_tokens)



