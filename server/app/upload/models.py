import uuid
from app.database import db
import time
from bson import ObjectId
from werkzeug.utils import secure_filename
import os
from app.logger import logger
from typing import List

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))  # Go up two levels to reach 'server'


# create item (sample) that need to be stored in the database
# [!] later you can defined other basic type here when needed
class Item:
    def __init__(self, reference_no, categories, tags, additional_fields, image_path):
        self.reference_no = reference_no
        self.categories = categories
        self.tags = tags
        self.additional_fields = additional_fields
        self.image_path = image_path

    # save and insert them into the database
    def save_item(self):
        data = {
            "reference_no": self.reference_no,
            "categories": self.categories,
            "tags": self.tags,
            "additional_fields": self.additional_fields,
            "image_path": self.image_path
        }
        # print(data)
        result = db.samples.insert_one(data)
        return result



class ItemBatch:
    def __init__(self, items):
        self.items = items
        self.sample_token = ''

    def save_items(self):
        # Process each item to ensure it fits the expected format
        data = []
        # all items use the same identifier
        self.sample_token = str(uuid.uuid4())
        for item in self.items:
            # generate a unique identifier for each item 
            # Initialize an empty dictionary to store the processed item
            # later when scheme is used, you can leverage that for reducing the number of loop 
            # match the keys in scheme as insertion, only loop those key pair not part of scheme
            processed_item = {"sample_token": self.sample_token}
            for key, value in item.items():
                processed_item[key] = value
            data.append(processed_item)

        # Insert the list of processed items into the collection
        result = db.samples_list.insert_many(data)
        # print(data)
        return result




from bson import ObjectId
from typing import Dict, Any

class Workflow:
    def __init__(self, name, frontend_id, is_locked, status):
        self._id = ObjectId()
        self.workflow_id = frontend_id
        self.name = name
        self.node_ids = []
        self.edges = []
        # self.status = status
        self.status = 'saved'               # mannully set for condition rendering (wf: saved and n:in progress)
        self.is_locked = is_locked

    def save(self):
        data = {
            "_id": self._id,
            "workflow_id": self.workflow_id,
            "name": self.name,
            "node_ids": self.node_ids,
            "edges": self.edges,
            "status": self.status,        # later if further operation exist, modify the changes
            "is_locked": self.is_locked
        }
        return db.workflows.insert_one(data)

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
                    # Fetch files for this section
                    files = list(db.files.find({"file_id": {"$in": section.get('file_ids', [])}}))
                    section['files'] = [{
                        "file_id": file['file_id'],
                        "name": file['name'],
                        "type": file['type'],
                        "size": file['size']
                    } for file in files]
                    node['sections'].append(section)
                workflow['nodes'].append(node)
            
            # Ensure edges are present and correctly formatted
            if 'edges' not in workflow or not workflow['edges']:
                workflow['edges'] = []

            # Update edges to include full node ids
            valid_edges = []
            for edge in workflow['edges']:
                from_node_id = node_map.get(edge['from'])
                to_node_id = node_map.get(edge['to'])
                if from_node_id and to_node_id:
                    valid_edges.append({'from': from_node_id, 'to': to_node_id})
            workflow['edges'] = valid_edges

            # Ensure is_locked is included in the response
            workflow['is_locked'] = workflow.get('is_locked', False)
            
            return workflow
        except Exception as e:
            print(f"Error fetching workflow with id {workflow_id}: {e}")
            return None















class Node:
    def __init__(self, workflow_id, node_id, label, status="Not Started"):
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
        for change in changes:
            try:
                if 'type' not in change or 'data' not in change:
                    raise KeyError("Change must have 'type' and 'data' keys")
                
                result = HandleWorkflow.process_change(change['type'], change['data'])
                results.append(result)
            except KeyError as e:
                logger.error(f"KeyError in change: {str(e)}")
                results.append({"error": f"Invalid change format: {str(e)}"})
            except ValueError as e:
                logger.error(f"ValueError in change: {str(e)}")
                results.append({"error": str(e)})
            except Exception as e:
                logger.error(f"Unexpected error processing change: {str(e)}")
                results.append({"error": "An unexpected error occurred"})
        return results




    @staticmethod
    def process_change(change_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
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
            frontend_id=data['id'], 
            is_locked=data.get('is_locked', False), 
            status=data.get('status', 'created')
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
            
            for section_data in node_data.get('sections', []):
                section_id = section_data.get('id') or f"section-{section_data['label'].lower()}-{int(time.time() * 1000)}"
                section = Section(
                    section_id=section_id,
                    node_id=node.node_id,
                    workflow_id=workflow.workflow_id,
                    label=section_data['label'],
                )
                section_result = section.save()
                section_id = section_result.inserted_id
                Node.push_section(node.node_id, str(section_id))

        workflow.save()
        return {
            "type": "create_workflow",
            "id": workflow.workflow_id,
            "name": workflow.name,
            "node_ids": workflow.node_ids,
            "edges": workflow.edges,
            "status": workflow.status,
            "is_locked": workflow.is_locked
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
        workflow_id = data['workflowId']
        workflow = db.workflows.find_one({"workflow_id": workflow_id})
        
        if workflow['is_locked']:
            raise ValueError(f"Cannot add node. Workflow {workflow_id} is locked.")
        
        node_data = data['node']
        new_edges = data.get('edges', [])

        node = Node(
            workflow_id=workflow_id,
            node_id=node_data['node_id'],
            label=node_data['label'],
            status=node_data.get('status', 'Not Started')
        )
        node.save()

        Workflow.push_node(workflow_id, node.node_id)
        Workflow.update_edges(workflow_id, new_edges)

        for section_data in node_data.get('sections', []):
            section_id = section_data.get('id') or f"section-{section_data['label'].lower()}-{int(time.time() * 1000)}"
            section = Section(
                section_id=section_id,
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
            "sections": [{"label": section_data['label'], "id": section_data.get('id')} for section_data in node_data.get('sections', [])]
        }



    @staticmethod
    def _update_node_status(data: Dict[str, Any]) -> Dict[str, Any]:
        workflow_id = data['workflowId']
        node_id = data['node_id']
        new_status = data['status']
        
        # Find the node, ensuring it belongs to the correct workflow
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
        workflow_id = data['workflowId']
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
        workflow_id = data['workflowId']
        node_id = data['nodeId']  # Changed from 'node_id' to 'nodeId'
        workflow = db.workflows.find_one({"workflow_id": workflow_id})
        
        if workflow['is_locked']:
            raise ValueError(f"Cannot add section. Workflow {workflow_id} is locked.")
        
        existing_section = db.sections.find_one({
            "node_id": node_id,
            "section_id": data['section']['id']
        })

        if existing_section:
            section_id = existing_section['_id']
            print(f"Using existing section: {section_id}")
        else:
            section = Section(
                section_id=data['section']['id'],
                node_id=node_id,
                workflow_id=workflow_id,
                label=data['section']['label']
            )
            section_result = section.save()
            section_id = section_result.inserted_id
            Node.push_section(node_id, str(section_id))
            print(f"Created new section: {section_id}")

        return {
            "type": "add_section",
            "id": str(section_id),
            "section_id": data['section']['id'],
            "node_id": node_id,
            "label": data['section']['label'],
        }
