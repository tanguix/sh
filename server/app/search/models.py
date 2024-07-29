


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
    def process_general_query(key, value):
        search_values = [v.strip() for v in value.split(',')] if ',' in value else [value.strip()]
        if len(search_values) > 1:
            return {key: {"$in": search_values}}
        return {key: value}



    @staticmethod
    def process_inventory_query(key, value, operator):
        try:
            if operator == 'range':
                min_value, max_value = map(int, value)
                return {key: {"$gte": min_value, "$lte": max_value}}
            elif operator == '>':
                return {key: {"$gt": int(value)}}
            elif operator == '<':
                return {key: {"$lt": int(value)}}
            elif operator == 'exact':
                return {key: int(value)}
            else:
                raise ValueError(f"Invalid inventory operator: {operator}")
        except ValueError:
            logger.error(f"Invalid inventory value or operator: value={value}, operator={operator}")
            raise ValueError(f"Invalid inventory value: {value}")




    @staticmethod
    def search_by_multiple_criteria(collection_name, criteria, backend_local_url):
        if collection_name not in db.list_collection_names():
            logger.error(f"Collection {collection_name} not found")
            return None, 0

        query = {"$and": []}
        logger.info(f"Received search criteria: {criteria}")

        for criterion in criteria:
            key = criterion['key']
            value = criterion['value']
            operator = criterion.get('operator', 'exact')

            logger.debug(f"Processing criterion: key={key}, value={value}, operator={operator}")

            try:
                if key == 'timestamp':
                    timestamp_query = Collection.process_timestamp_query(key, value, operator)
                    query["$and"].append(timestamp_query)
                elif key == 'total_inventory':
                    inventory_query = Collection.process_inventory_query(key, value, operator)
                    query["$and"].append(inventory_query)
                    logger.debug(f"Inventory query: {inventory_query}")
                else:
                    query["$and"].append(Collection.process_general_query(key, value))
            except ValueError as e:
                logger.error(str(e))
                return None, 0

        logger.debug(f"Final query: {query}")

        try:
            # Get the count of matching documents
            count = db[collection_name].count_documents(query)
            logger.info(f"Number of matching documents: {count}")

            if count == 0:
                logger.info(f"No matching documents found for query in collection {collection_name}")
                return None, 0

            # Fetch the actual documents
            results = list(db[collection_name].find(query))

            processed_results = Collection.process_results(results, backend_local_url)
            logger.debug(f"Processed {len(processed_results)} results")

            return processed_results, count
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return None, 0





    @staticmethod
    def process_results(results, backend_local_url):
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
                elif k in ['unit_price', 'unit_weight']:
                    processed_result[k] = v[-1] if isinstance(v, list) else v
                else:
                    processed_result[k] = v
            processed_results.append(processed_result)
        return processed_results




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
