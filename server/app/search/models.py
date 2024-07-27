


from app.database import db
from app.logger import logger
import time
from datetime import datetime, timedelta

class Collection:
    @staticmethod
    def get_all_collections():
        return db.list_collection_names()

    @staticmethod
    def get_keys(collection_name):
        exclude_keys = {"_id", "quantity", "password", "role", "authToken", "image_path"}
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
    def process_timestamp_query(key, value, operator):
        if operator == 'exact':
            date = datetime.strptime(value, "%Y-%m-%d")
            start_of_day = int(date.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
            end_of_day = int((date.replace(hour=23, minute=59, second=59, microsecond=999999) + timedelta(seconds=1)).timestamp())
            return {key: {"$gte": start_of_day, "$lt": end_of_day}}
        elif operator == '>':
            timestamp = int(datetime.strptime(value, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
            return {key: {"$lt": timestamp}}
        elif operator == '<':
            timestamp = int(datetime.strptime(value, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999).timestamp())
            return {key: {"$gt": timestamp}}
        elif operator == 'range':
            start_timestamp = int(datetime.strptime(value[0], "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
            end_timestamp = int((datetime.strptime(value[1], "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999) + timedelta(seconds=1)).timestamp())
            return {key: {"$gte": start_timestamp, "$lt": end_timestamp}}
        else:
            raise ValueError(f"Invalid timestamp operator: {operator}")




    @staticmethod
    def search_by_multiple_criteria(collection_name, criteria, backend_local_url):
        if collection_name not in db.list_collection_names():
            logger.error(f"Collection {collection_name} not found")
            return None, 0

        query = {"$and": []}
        for criterion in criteria:
            key = criterion['key']
            value = criterion['value']

            logger.debug(f"Processing criterion: key={key}, value={value}")

            if key == 'timestamp':
                timestamp_query = Collection.process_timestamp_query(key, value, criterion.get('operator'))
                query["$and"].append(timestamp_query)
            elif key == 'inventory':
                try:
                    inStock_value = int(value)
                    inventory_query = {
                        "inventory": {
                            "$elemMatch": {
                                "inStock": inStock_value
                            }
                        }
                    }
                    query["$and"].append(inventory_query)
                    logger.debug(f"Inventory query: {inventory_query}")
                except ValueError:
                    logger.error(f"Invalid inventory value: {value}")
                    return None, 0
            else:
                search_values = [v.strip() for v in value.split(',')] if ',' in value else [value.strip()]
                field_path = key if key in db[collection_name].find_one() else f"additional_fields.{key}"
                if isinstance(db[collection_name].find_one().get(key, db[collection_name].find_one().get('additional_fields', {}).get(key)), list):
                    query["$and"].append({field_path: {"$all": search_values} if len(search_values) > 1 else {"$in": search_values}})
                else:
                    query["$and"].append({field_path: {"$in": search_values} if len(search_values) > 1 else value})

        pipeline = [
            {"$match": query},
            {"$project": {
                "quantity": 0,
                "password": 0,
                "role": 0,
                "authToken": 0,
            }},
            {"$addFields": {
                "unit_price": {
                    "$cond": {
                        "if": {"$isArray": "$unit_price"},
                        "then": {"$arrayElemAt": ["$unit_price", -1]},
                        "else": "$unit_price"
                    }
                },
                "unit_weight": {
                    "$cond": {
                        "if": {"$isArray": "$unit_weight"},
                        "then": {"$arrayElemAt": ["$unit_weight", -1]},
                        "else": "$unit_weight"
                    }
                },
                "inventory": {
                    "$cond": {
                        "if": {"$isArray": "$inventory"},
                        "then": {"$arrayElemAt": ["$inventory", -1]},
                        "else": "$inventory"
                    }
                }
            }}
        ]

        logger.debug(f"Final query: {query}")
        logger.debug(f"Aggregation pipeline: {pipeline}")

        results = list(db[collection_name].aggregate(pipeline))
        count = len(results)
        
        logger.debug(f"Number of results: {count}")

        if count == 0:
            logger.info(f"No matching documents found for query in collection {collection_name}")
            return None, 0

        processed_results = []

        for result in results:
            processed_result = {}
            for k, v in result.items():
                if k == "_id":
                    continue
                if k == "additional_fields":
                    processed_result.update(v)
                elif k == 'image_path':
                    image_path = v[7:] if v.startswith('images/') else v
                    image_url = f"{backend_local_url}/search/api/images/{image_path}"
                    processed_result['image_url'] = image_url
                else:
                    processed_result[k] = v
            processed_results.append(processed_result)

        return processed_results, count







    @staticmethod
    def search_sample_tokens_by_user(user_name, user_role):
        pipeline = [
            {"$match": {"modifiedBy": {"$elemMatch": {"name": user_name, "role": user_role}}}},
            {"$sort": {"timestamp": 1}},
            {"$group": {"_id": "$sample_token", "doc": {"$first": "$$ROOT"}}},
            {"$project": {"_id": 0, "sample_token": "$_id", "timestamp": "$doc.timestamp"}},
            {"$sort": {"timestamp": 1}}
        ]
        result = list(db.samples_list.aggregate(pipeline))
        return [doc['sample_token'] for doc in result]

    @staticmethod
    def search_workflow_tokens_by_user(user_name, user_role):
        query = {"owner": [user_name, user_role]}
        documents = db.workflows.find(query, {"workflow_id": 1, "timestamp": 1, "_id": 0})
        workflow_token_data = [
            {"workflow_id": doc["workflow_id"], "timestamp": doc.get("timestamp", int(time.time() * 1000))}
            for doc in documents
        ]
        sorted_workflow_token_data = sorted(workflow_token_data, key=lambda x: x["timestamp"], reverse=False)
        return [item["workflow_id"] for item in sorted_workflow_token_data]





    @staticmethod
    def get_categories_and_tags():
        logger.info("Fetching categories and tags from the database")
        try:
            categories = list(db.samples.distinct('categories'))
            tags = list(db.samples.distinct('tags'))
            logger.info(f"Successfully fetched {len(categories)} categories and {len(tags)} tags")
            logger.debug(f"Categories: {categories}")
            logger.debug(f"Tags: {tags}")
            return categories, tags
        except Exception as e:
            logger.error(f"Error in get_categories_and_tags: {e}", exc_info=True)
            raise






class ExchangeRate:


    @staticmethod
    def get_latest_rate():
        # Implement the logic to fetch the latest exchange rate
        # This is a placeholder implementation
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": int(time.time()),
            "base": "USD",
            "rates": {"EUR": 0.85, "GBP": 0.75, "JPY": 110.0}
        }
