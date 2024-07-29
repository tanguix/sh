



import uuid
from app.database import db
from bson import ObjectId
from typing import Dict, Any
from werkzeug.utils import secure_filename
import os
from app.logger import logger
from typing import List
import json
import time
from pymongo import UpdateOne

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))

def json_serialize(obj):
    def convert(o):
        if isinstance(o, ObjectId):
            return str(o)
        return o.__dict__ if hasattr(o, '__dict__') else str(o)
    
    return json.dumps(obj, default=convert, indent=2)

class Item:
    def __init__(self, **kwargs):
        self.reference_no = kwargs.get('reference_no')
        self.side_reference_nos = [ref.strip() for ref in kwargs.get('side_reference_no', '').split(',') if ref.strip()]
        self.categories = kwargs.get('categories', [])
        self.tags = kwargs.get('tags', [])
        self.additional_fields = kwargs.get('additional_fields', {})
        self.image_path = kwargs.get('image_path')
        self.additional_image_paths = kwargs.get('additional_image_paths', [])
        self.timestamp = kwargs.get('timestamp', int(time.time()))
        self.unit_price = self._parse_unit_input(kwargs.get('unit_price'), kwargs.get('username'))
        self.unit_weight = self._parse_unit_input(kwargs.get('unit_weight'), kwargs.get('username'))
        self.source = kwargs.get('source')
        self.address = kwargs.get('address') or None
        self.phone = kwargs.get('phone') or None
        self.inventory = self._parse_inventory(kwargs.get('inventory'), kwargs.get('username'))
        self.total_inventory = self._calculate_total_inventory()

    def _parse_inventory(self, inventory, username):
        if inventory and inventory.strip():
            return [{
                "putIn": int(inventory),
                "takeOut": 0,
                "by": username,
                "timestamp": self.timestamp
            }]
        return []

    def _calculate_total_inventory(self):
        total = sum(item['putIn'] - item['takeOut'] for item in self.inventory)
        return max(total, 0)  # Ensure total_inventory is never negative

    def _parse_unit_input(self, input_str, username):
        if not input_str:
            return []
        num, unit = map(str.strip, input_str.split(','))
        return [{
            "num": float(num),
            "unit": unit,
            "timestamp": self.timestamp,
            "upload": username
        }]

    def save_item(self):
        if not self.validate_references():
            raise ValueError("Reference validation failed")
        data = self.__dict__
        result = db.samples.insert_one(data)
        return result

    def validate_references(self):
        if not self.reference_no:
            raise ValueError("Reference number cannot be empty")

        if not self.are_side_references_unique(self.side_reference_nos):
            raise ValueError("Side reference numbers are not unique")
        
        self.reference_no = f"{self.reference_no}{self.timestamp}x"
        if not self.is_reference_no_unique(self.reference_no):
            raise ValueError("Generated reference number is not unique")
        return True

    @classmethod
    def from_form_data(cls, form_data, files):
        data = {}
        for key, value in form_data.items():
            if key in ['tags', 'categories', 'additional_fields']:
                data[key] = json.loads(value)
            else:
                data[key] = value

        if 'image' in files:
            file = files['image']
            filename = secure_filename(file.filename)
            directory = os.path.splitext(filename)[0]
            os.makedirs(os.path.join(SERVER_DIR, 'images', directory), exist_ok=True)
            file_path = os.path.join(SERVER_DIR, 'images', directory, filename)
            file.save(file_path)
            data['image_path'] = f'images/{directory}/{filename}'

        additional_images = []
        for key, file in files.items():
            if key.startswith('additional_image_'):
                filename = secure_filename(file.filename)
                directory = os.path.splitext(data['image_path'].split('/')[-1])[0]
                file_path = os.path.join(SERVER_DIR, 'images', directory, filename)
                file.save(file_path)
                additional_images.append(f'/images/{directory}/{filename}')
        data['additional_image_paths'] = additional_images

        return cls(**data)

    @staticmethod
    def is_reference_unique(abbreviation: str, full_name: str):
        logger.info(f"Checking uniqueness for abbreviation: {abbreviation}, full_name: {full_name}")
        result = db.reference_table.find_one({
            'reference_number_table': {
                '$elemMatch': {abbreviation: {'$exists': True}}
            }
        })
        if result:
            return False
        for doc in db.reference_table.find():
            for ref in doc.get('reference_number_table', []):
                if full_name in ref.values():
                    logger.info(f"Found matching full_name: {full_name}")
                    return False
        logger.info("Reference is unique")
        return True

    @staticmethod
    def add_reference(full_name: str, abbreviation: str):
        logger.info(f"Attempting to add reference: {abbreviation} - {full_name}")
        if not Item.is_reference_unique(abbreviation, full_name):
            logger.warning(f"Reference abbreviation already exists: {abbreviation} - {full_name}")
            raise ValueError("Reference abbreviation already exists")
        new_reference = {abbreviation: full_name}
        result = db.reference_table.update_one(
            {},
            {'$push': {'reference_number_table': new_reference}},
            upsert=True
        )
        success = result.modified_count > 0 or result.upserted_id is not None
        logger.info(f"Add reference result: {'Success' if success else 'Failure'}")
        return success

    @staticmethod
    def get_all_references():
        result = db.reference_table.find_one({})
        if result and 'reference_number_table' in result:
            return [
                {'abbreviation': list(ref.keys())[0], 'fullName': list(ref.values())[0]}
                for ref in result['reference_number_table']
            ]
        return []

    @staticmethod
    def are_side_references_unique(side_refs):
        if len(side_refs) != len(set(side_refs)):
            return False
        for ref in side_refs:
            if db.samples.find_one({"side_reference_nos": ref}):
                return False
        return True

    @staticmethod
    def is_reference_no_unique(ref_no):
        return db.samples.find_one({"reference_no": ref_no}) is None







class ItemBatch:
    def __init__(self, items):
        self.items = items
        self.main_sample_token = self._determine_main_sample_token()
        self.timestamp = int(time.time() * 1000)  # Current time in milliseconds
        logger.info(f"ItemBatch initialized with {len(items)} items and main_sample_token: {self.main_sample_token}")

    def _determine_main_sample_token(self):
        for item in self.items:
            if 'sample_token' in item and item['sample_token']:
                return item['sample_token']
        return str(uuid.uuid4())

    def remove_sample(self, sample_data):
        logger.info(f"Attempting to remove sample: {sample_data}")
        
        query = {key: value for key, value in sample_data.items() if key not in ['_remove']}
        
        items_to_remove = list(db.samples_list.find(query))
        
        if not items_to_remove:
            logger.warning(f"No items found matching the criteria: {query}")
            return []
        
        result = db.samples_list.delete_many(query)
        
        removed_ids = [str(item['_id']) for item in items_to_remove]
        logger.info(f"Removed {result.deleted_count} items matching the criteria. IDs: {removed_ids}")
        
        return removed_ids






    def save_items(self):
        logger.info("Starting save_items method")
        try:
            items_to_update = []
            items_to_insert = []
            processed_reference_nos = set()

            for item in self.items:
                existing_item = self._find_existing_item(item)
                
                if existing_item:
                    if existing_item['sample_token'] != self.main_sample_token:
                        new_item = self._process_item(item)
                        items_to_insert.append(new_item)
                    else:
                        update_operation = self._prepare_update_operation(item, existing_item)
                        if update_operation:
                            items_to_update.append((existing_item['_id'], update_operation))
                else:
                    new_item = self._process_item(item)
                    items_to_insert.append(new_item)
                
                processed_reference_nos.add(item.get('reference_no'))

            logger.info(f"Processed {len(self.items)} items")
            logger.info(f"Items to update: {len(items_to_update)}")
            logger.info(f"Items to insert: {len(items_to_insert)}")
            logger.info(f"Processed reference numbers: {processed_reference_nos}")

            updated_ids = self._perform_bulk_update(items_to_update)
            inserted_ids = self._insert_new_items(items_to_insert)
            self._remove_obsolete_items(processed_reference_nos)

            return self._create_result(inserted_ids, updated_ids)

        except Exception as e:
            logger.exception(f"Error in save_items: {str(e)}")
            raise



    def _prepare_update_operation(self, new_item, existing_item):
        update_operation = {'$set': {}, '$unset': {}}
        
        for key in existing_item:
            if key not in new_item and key not in ['_id', 'sample_token', 'timestamp', 'original_inventory']:
                update_operation['$unset'][key] = ""

        for key, value in new_item.items():
            if key not in ['_id', 'sample_token', 'timestamp', 'original_inventory']:
                if value is None:
                    update_operation['$unset'][key] = ""
                else:
                    if key in ['categories', 'tags']:
                        update_operation['$set'][key] = value if isinstance(value, list) else [value]
                    elif key == 'inventory':
                        update_operation['$set'][key] = value
                        update_operation['$set']['calculated_inventory'] = self._calculate_inventory(value)
                    else:
                        update_operation['$set'][key] = value
        
        update_operation['$set']['timestamp'] = self.timestamp

        if not update_operation['$set']:
            del update_operation['$set']
        if not update_operation['$unset']:
            del update_operation['$unset']

        return update_operation





    def _perform_bulk_update(self, items_to_update):
        updated_ids = []
        if items_to_update:
            bulk_operations = [
                UpdateOne({'_id': item_id}, update_operation)
                for item_id, update_operation in items_to_update
            ]
            
            if bulk_operations:
                update_result = db.samples_list.bulk_write(bulk_operations)
                updated_ids = [str(item_id) for item_id, _ in items_to_update]
                logger.info(f"Updated {update_result.modified_count} existing items. Updated IDs: {updated_ids}")
        return updated_ids

    def _insert_new_items(self, items_to_insert):
        inserted_ids = []
        if items_to_insert:
            insert_result = db.samples_list.insert_many(items_to_insert)
            inserted_ids = [str(id) for id in insert_result.inserted_ids]
            logger.info(f"Inserted {len(inserted_ids)} new items. Inserted IDs: {inserted_ids}")
        return inserted_ids

    def _remove_obsolete_items(self, processed_reference_nos):
        result = db.samples_list.delete_many({
            'sample_token': self.main_sample_token,
            'reference_no': {'$nin': list(processed_reference_nos)}
        })
        logger.info(f"Removed {result.deleted_count} obsolete items from the main set.")



    def _process_item(self, item):
        processed_item = {
            "sample_token": self.main_sample_token,
            "timestamp": self.timestamp
        }
        for key, value in item.items():
            if key not in ['_id', 'sample_token', 'timestamp', 'original_inventory', 'calculated_inventory']:
                if key == 'inventory':
                    processed_item[key] = value
                    processed_item['calculated_inventory'] = self._calculate_inventory(value)
                else:
                    processed_item[key] = value
        return processed_item

    def _calculate_inventory(self, inventory):
        return sum(item.get('putIn', 0) - item.get('takeOut', 0) for item in inventory)




    def _find_existing_item(self, item):
        if 'reference_no' in item:
            existing = db.samples_list.find_one({
                'reference_no': item['reference_no'],
                'sample_token': self.main_sample_token
            })
            if existing:
                logger.info(f"Found existing item with reference_no: {item['reference_no']} in main set")
                return existing
        return None

    def _create_result(self, inserted_ids, updated_ids):
        class Result:
            def __init__(self, inserted_ids, modified_ids):
                self.inserted_ids = inserted_ids or []
                self.modified_ids = modified_ids

        return Result(inserted_ids, updated_ids)






class Workflow:
    def __init__(self, name, workflow_id, is_locked, status, owner, timestamp=None):
        self._id = ObjectId()
        self.workflow_id = workflow_id
        self.name = name
        self.node_ids = []
        self.edges = []
        self.status = 'saved'
        self.is_locked = is_locked
        self.owner = owner
        self.timestamp = timestamp or int(time.time() * 1000)  # Use provided timestamp or current time

    def save(self):
        data = {
            "_id": self._id,
            "workflow_id": self.workflow_id,
            "name": self.name,
            "node_ids": self.node_ids,
            "edges": self.edges,
            "status": self.status,
            "is_locked": self.is_locked,
            "owner": self.owner,
            "timestamp": self.timestamp
        }
        return db.workflows.insert_one(data)



    @staticmethod
    def update_status(workflow_id: str, status: str):
        return db.workflows.update_one(
            {"workflow_id": workflow_id},
            {"$set": {"status": status}}
        )


    @staticmethod
    def update_lock_status(workflow_id, is_locked):
        return db.workflows.update_one(
            {"workflow_id": workflow_id},
            {"$set": {"is_locked": is_locked}}
        )

    @staticmethod
    def update_edges(workflow_id, edges):
        return db.workflows.update_one(
            {"workflow_id": workflow_id},
            {"$set": {"edges": edges}}
        )

    @staticmethod
    def push_node(workflow_id, node_id):
        return db.workflows.update_one(
            {"workflow_id": workflow_id},
            {"$push": {"node_ids": node_id}}
        )

    @staticmethod
    def remove_node(workflow_id, node_id):
        return db.workflows.update_one(
            {"workflow_id": workflow_id},
            {"$pull": {"node_ids": node_id}}
        )

    @staticmethod
    def confirm_workflow(workflow_id):
        return db.workflows.update_one(
            {"workflow_id": workflow_id},
            {"$set": {"status": "confirmed"}}
        )

    @staticmethod
    def get_workflow_by_id(workflow_id):
        try:
            workflow = db.workflows.find_one({"workflow_id": workflow_id})
            if not workflow:
                return None
            workflow['_id'] = str(workflow['_id'])

            nodes = list(db.nodes.find({"workflow_id": workflow_id}))
            workflow['nodes'] = []
            node_map = {node['node_id']: node['node_id'] for node in nodes}
            for node in nodes:
                node['_id'] = str(node['_id'])
                node['id'] = node['id'] if 'id' in node else node['node_id']

                sections = list(db.sections.find({"node_id": node['node_id']}))
                node['sections'] = []

                for section in sections:
                    section['_id'] = str(section['_id'])
                    files = list(db.files.find({"file_id": {"$in": section.get('file_ids', [])}}))
                    section['files'] = [{
                        "file_id": file['file_id'],
                        "name": file['name'],
                        "type": file['type'],
                        "size": file['size']
                    } for file in files]
                    node['sections'].append(section)
                workflow['nodes'].append(node)
            
            if 'edges' not in workflow or not workflow['edges']:
                workflow['edges'] = []

            valid_edges = []
            for edge in workflow['edges']:
                from_node_id = node_map.get(edge['from'])
                to_node_id = node_map.get(edge['to'])
                if from_node_id and to_node_id:
                    valid_edges.append({'from': from_node_id, 'to': to_node_id})
            workflow['edges'] = valid_edges

            workflow['is_locked'] = workflow.get('is_locked', False)
            workflow['owner'] = workflow.get('owner', [])  # Include owner in the returned data
            workflow['timestamp'] = workflow.get('timestamp', int(time.time() * 1000))
            
            return workflow
        except Exception as e:
            print(f"Error fetching workflow with id {workflow_id}: {e}")
            return None

    @staticmethod
    def get_locked_workflows():
        try:
            return db.workflows.find({"is_locked": True}, {"workflow_id": 1, "_id": 0})
        except Exception as e:
            print(f"Error fetching locked workflows: {e}")
            return []











class Node:
    def __init__(self, workflow_id, node_id, label, status="Sleep"):
        self._id = ObjectId()
        self.node_id = node_id
        self.workflow_id = workflow_id
        self.label = label
        self.status = status
        self.section_ids = []

    def save(self):
        data = {
            "_id": self._id,
            "node_id": self.node_id,
            "workflow_id": self.workflow_id,
            "label": self.label,
            "status": self.status,
            "section_ids": self.section_ids
        }
        return db.nodes.insert_one(data)

    @staticmethod
    def update_status(node_id, status):
        return db.nodes.update_one(
            {"node_id": node_id},
            {"$set": {"status": status}}
        )

    @staticmethod
    def push_section(node_id, section_id):
        return db.nodes.update_one(
            {"node_id": node_id},
            {"$push": {"section_ids": section_id}}
        )





class Section:
    def __init__(self, section_id, node_id, workflow_id, label):
        self._id = ObjectId()
        self.section_id = section_id
        self.node_id = node_id
        self.workflow_id = workflow_id
        self.label = label
        self.file_ids = []  # Initialize with an empty array



    def save(self):
        data = {
            "_id": self._id,
            "section_id": self.section_id,
            "node_id": self.node_id,
            "workflow_id": self.workflow_id,
            "label": self.label,
            "file_ids": self.file_ids
        }
        return db.sections.insert_one(data)



    @staticmethod
    def push_file_id(workflow_id, node_id, section_id, file_id):
        if section_id == 'undefined' or not section_id:
            logger.error(f"Invalid section_id: {section_id} for workflow_id: {workflow_id}, node_id: {node_id}")
            return None

        try:
            # Try to convert section_id to ObjectId
            section_object_id = ObjectId(section_id)
        except:
            # If conversion fails, use the string as is
            section_object_id = section_id

        query = {
            "workflow_id": workflow_id,
            "node_id": node_id,
            "$or": [{"_id": section_object_id}, {"section_id": section_id}]
        }
        update = {"$push": {"file_ids": file_id}}

        logger.info(f"Attempting to update section. Query: {query}, Update: {update}")

        result = db.sections.update_one(query, update)

        if result.matched_count == 0:
            logger.error(f"No section found for workflow_id: {workflow_id}, node_id: {node_id}, section_id: {section_id}")
            return None
        elif result.modified_count == 0:
            logger.warning(f"Section found but not modified. Possible duplicate file_id: {file_id}")
        
        return result




    @staticmethod
    def get_files(section_id):
        section = db.sections.find_one({"_id": ObjectId(section_id)})
        if section and 'file_ids' in section:
            return list(db.files.find({"file_id": {"$in": section['file_ids']}}))
        return []








class File:
    def __init__(self, file_id, name, type, size, path):
        self._id = ObjectId()
        self.file_id = file_id
        self.name = name
        self.type = type
        self.size = size
        self.path = path



    @staticmethod
    def allowed_file(filename):
        ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx'}  # Added 'docx'
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



    @staticmethod
    def save_file(file_data):
        return db.files.insert_one(file_data)



    
    @staticmethod
    def get_file_by_id(file_id):
        file = db.files.find_one({"file_id": file_id})
        if file:
            return {
                "file_id": file["file_id"],
                "name": file["name"],
                "type": file["type"],
                "size": file["size"],
                "path": os.path.join(SERVER_DIR, file["path"]),  # This should now correctly point to the 'files' directory
            }
        return None


    @staticmethod
    def process_multiple_uploads(files, file_data_array, workflow_id, node_id, section_id, FILE_FOLDER):
        results = []
        for file, file_data in zip(files, file_data_array):
            if file.filename == '':
                continue

            if file and File.allowed_file(file.filename):
                result = File.process_single_upload(file, file_data, workflow_id, node_id, section_id, FILE_FOLDER)
                results.append(result)
            else:
                results.append({
                    "error": "Invalid file type",
                    "file_name": file.filename
                })
        return results



    @staticmethod
    def process_single_upload(file, file_data, workflow_id, node_id, section_id, FILE_FOLDER):
        try:
            filename = secure_filename(file.filename)
            relative_path = os.path.join('files', filename)
            absolute_path = os.path.join(FILE_FOLDER, filename)
            file.save(absolute_path)

            file_document = {
                "file_id": file_data['file_id'],
                "name": file_data['name'],
                "type": file_data['type'],
                "size": file_data['size'],
                "path": relative_path  # Store the relative path
            }

            # Insert file document into files collection
            file_result = db.files.insert_one(file_document)


            if file_result.inserted_id:
                # Update the section with the new file_id
                section_result = Section.push_file_id(workflow_id, node_id, section_id, file_data['file_id'])
                
                if section_result and section_result.modified_count > 0:
                    return {
                        "message": "File uploaded successfully",
                        "file_id": file_data['file_id']
                    }
                else:
                    logger.error(f"Failed to update section. Section result: {section_result}")
                    return {
                        "error": "Failed to update section with file ID",
                        "file_id": file_data['file_id']
                    }
            else:
                logger.error(f"Failed to insert file document for file_id: {file_data['file_id']}")
                return {
                    "error": "Failed to insert file document",
                    "file_id": file_data['file_id']
                }
        except Exception as e:
            logger.exception(f"Error processing file upload: {str(e)}")
            return {
                "error": f"Error processing file upload: {str(e)}",
                "file_id": file_data['file_id']
            }





    @staticmethod
    def get_file_for_download(workflow_id, node_id, section_id, file_id):
        section = db.sections.find_one({
            "workflow_id": workflow_id,
            "node_id": node_id,
            "section_id": section_id,
            "file_ids": {"$in": [file_id]}
        })
        
        if not section:
            return None, "File not found in the specified section"
        
        file_info = File.get_file_by_id(file_id)
        
        if not file_info:
            return None, "File not found"
        
        file_path = file_info['path']
        
        if not os.path.exists(file_path):
            return None, f"File not found on server at path: {file_path}"
        
        return file_info, None








class HandleWorkflow:



    @staticmethod
    def process_changes(changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        workflow_ids = set()

        for change in changes:
            try:
                if 'type' not in change or 'data' not in change:
                    raise KeyError("Change must have 'type' and 'data' keys")
                
                if 'workflow_id' not in change['data']:
                    raise KeyError("Change data must include workflow_id")

                workflow_ids.add(change['data']['workflow_id'])
                
                result = HandleWorkflow.process_change(change['type'], change['data'])
                results.append(result)
            except KeyError as e:
                logger.error(f"KeyError in change: {str(e)}")
                results.append({"error": f"Invalid change format: {str(e)}", "type": change.get('type', 'unknown')})
            except ValueError as e:
                logger.error(f"ValueError in change: {str(e)}")
                results.append({"error": str(e), "type": change.get('type', 'unknown')})
            except Exception as e:
                logger.error(f"Unexpected error processing change: {str(e)}")
                results.append({"error": "An unexpected error occurred", "type": change.get('type', 'unknown')})

        # Check if all changes are for the same workflow
        if len(workflow_ids) != 1:
            error_message = "All changes must be for the same workflow"
            logger.error(error_message)
            results.append({"error": error_message, "type": "multiple_workflows"})
            return results

        # After processing all changes, update the workflow status
        if results and all(result.get('success', False) for result in results):
            workflow_id = list(workflow_ids)[0]  # Safe to use [0] as we've confirmed there's only one ID
            Workflow.update_status(workflow_id, "saved")

        return results



    @staticmethod
    def process_change(change_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if change_type == 'create_workflow':
                return HandleWorkflow._create_workflow(data)
            elif change_type == 'confirm_workflow':
                return HandleWorkflow._confirm_workflow(data)
            elif change_type == 'remove_node':
                return HandleWorkflow._remove_node(data)
            elif change_type == 'add_node':
                return HandleWorkflow._add_node(data)
            elif change_type == 'add_section':
                return HandleWorkflow._add_section(data)
            elif change_type == 'update_node_status':
                return HandleWorkflow._update_node_status(data)
            elif change_type == 'update_lock_status':
                return HandleWorkflow._update_lock_status(data)
            else:
                raise ValueError(f"Unknown change type: {change_type}")
        except KeyError as e:
            logger.error(f"Missing key in change data for type '{change_type}': {str(e)}")
            return {"error": f"Missing data for {change_type}: {str(e)}", "type": change_type}
        except Exception as e:
            logger.error(f"Error processing change of type '{change_type}': {str(e)}")
            return {"error": f"Error processing {change_type}: {str(e)}", "type": change_type}








    @staticmethod
    def _confirm_workflow(data: Dict[str, Any]) -> Dict[str, Any]:
        workflow_id = data['id']
        Workflow.confirm_workflow(workflow_id)
        return {
            "type": "confirm_workflow",
            "id": workflow_id,
            "status": "confirmed"
        }



    @staticmethod
    def _create_workflow(data: Dict[str, Any]) -> Dict[str, Any]:
        workflow = Workflow(
            name=data['name'], 
            workflow_id=data['workflow_id'], 
            is_locked=data.get('is_locked', False), 
            status=data.get('status', 'created'),
            owner=data.get('owner', []),  # Include owner data
            timestamp=data.get('timestamp'),  # Use provided timestamp if available
        )
        workflow.edges = data.get('edges', [])
        
        for node_data in data.get('nodes', []):
            node = Node(
                workflow_id=workflow.workflow_id,
                node_id=node_data['node_id'],
                label=node_data['label'],
                status=node_data['status']
            )
            node.save()
            workflow.node_ids.append(node.node_id)
            
            print(f"\nProcessing node: {node.label}")
            for section_data in node_data.get('sections', []):
                print(f"\nSection data: {section_data}")
                section = Section(
                    section_id=section_data.get('section_id'),
                    node_id=node.node_id,
                    workflow_id=workflow.workflow_id,
                    label=section_data['label'],
                )
                section_result = section.save()
                section_id = str(section_result.inserted_id)
                Node.push_section(node.node_id, section_id)
                print(f"Saved section: {section.label} with id: {section_id}")

        workflow.save()
        print(f"\nWorkflow saved: {workflow.name} with id: {workflow.workflow_id}")
        return {
            "type": "create_workflow",
            "id": workflow.workflow_id,
            "name": workflow.name,
            "node_ids": workflow.node_ids,
            "edges": workflow.edges,
            "status": workflow.status,
            "is_locked": workflow.is_locked,
            "owner": workflow.owner,  # Include owner in the return data
            "timestamp": workflow.timestamp,
        }



    @staticmethod
    def _update_lock_status(data: Dict[str, Any]) -> Dict[str, Any]:
        workflow_id = data['workflow_id']
        is_locked = data['is_locked']
        
        result = Workflow.update_lock_status(workflow_id, is_locked)
        
        if result.modified_count == 0:
            raise ValueError(f"Failed to update lock status for workflow with id {workflow_id}")
        
        return {
            "type": "update_lock_status",
            "workflow_id": workflow_id,
            "is_locked": is_locked
        }


    @staticmethod
    def _add_node(data: Dict[str, Any]) -> Dict[str, Any]:
        workflow_id = data['workflow_id']
        workflow = db.workflows.find_one({"workflow_id": workflow_id})
        
        if workflow['is_locked']:
            raise ValueError(f"Cannot add node. Workflow {workflow_id} is locked.")
        
        node_data = data['node']
        new_edges = data.get('edges', [])

        node = Node(
            workflow_id=workflow_id,
            node_id=node_data['node_id'],
            label=node_data['label'],
            status=node_data.get('status', 'Sleep')
        )
        node.save()

        Workflow.push_node(workflow_id, node.node_id)
        Workflow.update_edges(workflow_id, new_edges)

        for section_data in node_data.get('sections', []):
            section = Section(
                section_id=section_data['section_id'],
                node_id=node.node_id,
                workflow_id=node.workflow_id,
                label=section_data['label']
            )
            section_result = section.save()
            section_id = section_result.inserted_id
            Node.push_section(node.node_id, str(section_id))


        return {
            "type": "add_node",
            "node_id": node.node_id,
            "label": node.label,
            "status": node.status,
            "sections": [{"label": section_data['label'], "id": section_data.get('section_id')} for section_data in node_data.get('sections', [])]
        }



    @staticmethod
    def _update_node_status(data: Dict[str, Any]) -> Dict[str, Any]:
        workflow_id = data.get('workflow_id')
        node_id = data.get('node_id')
        new_status = data.get('status')
        
        if not all([workflow_id, node_id, new_status]):
            missing = [k for k in ['workflow_id', 'node_id', 'status'] if k not in data]
            raise KeyError(f"Missing required data for updating node status: {', '.join(missing)}")
        
        node = db.nodes.find_one({"workflow_id": workflow_id, "node_id": node_id})
        if not node:
            raise ValueError(f"Node with id {node_id} not found in workflow {workflow_id}")
        
        old_status = node['status']
        if old_status != new_status:
            result = Node.update_status(node_id, new_status)
            
            if result.modified_count == 0:
                raise ValueError(f"Failed to update status for node with id {node_id} in workflow {workflow_id}")
            
            return {
                "type": "update_node_status",
                "workflow_id": workflow_id,
                "node_id": node_id,
                "status": new_status,
                "old_status": old_status,
                "updated": True
            }
        else:
            return {
                "type": "update_node_status",
                "workflow_id": workflow_id,
                "node_id": node_id,
                "status": new_status,
                "old_status": old_status,
                "updated": False
            }










    @staticmethod
    def _remove_node(data: Dict[str, Any]) -> Dict[str, Any]:
        workflow_id = data['workflow_id']
        workflow = db.workflows.find_one({"workflow_id": workflow_id})
        
        if workflow['is_locked']:
            raise ValueError(f"Cannot remove node. Workflow {workflow_id} is locked.")
        
        node_id = data['node_id']
        new_edges = data.get('edges', [])
        
        print(f"Attempting to remove node {node_id} from workflow {workflow_id}")
        
        if not workflow:
            raise ValueError(f"Workflow with id {workflow_id} not found")
        
        node = db.nodes.find_one({"node_id": node_id})
        if not node:
            raise ValueError(f"Node with id {node_id} not found")
        
        section_ids = node.get('section_ids', [])
        for section_id in section_ids:
            db.sections.delete_one({"_id": ObjectId(section_id)})
            print(f"Deleted section {section_id}")
        
        node_result = db.nodes.delete_one({"node_id": node_id})
        print(f"Node deletion result: {node_result.deleted_count} document(s) deleted")
        
        workflow_result = Workflow.remove_node(workflow_id, node_id)
        edge_result = Workflow.update_edges(workflow_id, new_edges)
        print(f"Workflow update result: {workflow_result.modified_count} document(s) modified")
        print(f"Edge update result: {edge_result.modified_count} document(s) modified")
        
        
        return {
            "type": "remove_node",
            "node_id": node_id,
            "node_deleted": node_result.deleted_count,
            "workflow_updated": workflow_result.modified_count,
            "edges_updated": edge_result.modified_count,
            "sections_deleted": len(section_ids)
        }






    @staticmethod
    def _add_section(data: Dict[str, Any]) -> Dict[str, Any]:
        workflow_id = data.get('workflow_id')
        node_id = data.get('node_id')
        section_data = data.get('section')

        if not all([workflow_id, node_id, section_data]):
            raise ValueError(f"Missing required data for adding section: {data}")

        workflow = db.workflows.find_one({"workflow_id": workflow_id})
        if not workflow:
            raise ValueError(f"Workflow with id {workflow_id} not found")

        if workflow.get('is_locked'):
            raise ValueError(f"Cannot add section. Workflow {workflow_id} is locked.")

        node = db.nodes.find_one({"node_id": node_id, "workflow_id": workflow_id})
        if not node:
            raise ValueError(f"Node with id {node_id} not found in workflow {workflow_id}")

        section = Section(
            section_id=section_data['section_id'],
            node_id=node_id,
            workflow_id=workflow_id,
            label=section_data['label']
        )
        section_result = section.save()
        section_id = str(section_result.inserted_id)
        Node.push_section(node_id, section_id)

        print(f"\nAdded new section: {section.label} with id: {section_id} to node: {node_id}")

        return {
            "type": "add_section",
            "id": section_id,
            "section_id": section_data['section_id'],
            "node_id": node_id,
            "label": section_data['label'],
        }
