from datetime import datetime
from .. import mongo_flow_cytometry, mongo_auth
import os
from ..config import Config
import hashlib

class FlowCytometryModel:
    @staticmethod
    def get_next_sequence():
        sequence = mongo_flow_cytometry.db.flow_cyto_counter.find_one_and_update(
            {"_id": "project_id"},
            {"$inc": {"sequence_value": 1}},
            return_document=True,
            upsert=True  # Aggiungi upsert=True per creare il documento se non esiste
        )

        # Se sequence è None, inizializza il contatore
        if sequence is None:
            mongo_flow_cytometry.db.flow_cyto_counter.insert_one({"_id": "project_id", "sequence_value": 1})
            return 1

        return sequence["sequence_value"]

    @staticmethod
    def create_flow_cytometry_data(data):
        data["progressive_id"] = FlowCytometryModel.get_next_sequence()  # Aggiungi il progressive_id
        return mongo_flow_cytometry.db.flow_cytometry.insert_one(data)

    @staticmethod
    def find_by_object_id(flow_cytometry_id):
        return mongo_flow_cytometry.db.flow_cytometry.find_one({"_id": flow_cytometry_id})

    @staticmethod
    def find_by_progressive_id(flow_cytometry_id):
        return mongo_flow_cytometry.db.flow_cytometry.find_one({"progressive_id": int(flow_cytometry_id)})

    @staticmethod
    def find_by_project_id(project_id):
        return mongo_flow_cytometry.db.flow_cytometry.find({"project_id": project_id})

    @staticmethod
    def find_by_name(experiment_name):
        experiment_name_hash = hashlib.sha256(experiment_name.encode()).hexdigest()
        return mongo_flow_cytometry.db.flow_cytometry.find_one({"experiment_name_hash": experiment_name_hash})
    
    @staticmethod
    def delete_by_progressive_id(progressive_id):
        return mongo_flow_cytometry.db.flow_cytometry.delete_one({"progressive_id": int(progressive_id)})
    
    
    
class WorkspaceModel:
    @staticmethod
    def get_next_sequence():
        sequence = mongo_flow_cytometry.db.workspace_counter.find_one_and_update(
            {"_id": "workspace_id"},
            {"$inc": {"sequence_value": 1}},
            return_document=True,
            upsert=True  # Create the document if it doesn't exist
        )

        # If sequence is None, initialize the counter
        if sequence is None:
            mongo_flow_cytometry.db.workspace_counter.insert_one({"_id": "workspace_id", "sequence_value": 1})
            return 1

        return sequence["sequence_value"]

    @staticmethod
    def create_workspace_data(data):
        data["progressive_id"] = WorkspaceModel.get_next_sequence()  # Add the progressive_id
        return mongo_flow_cytometry.db.workspaces.insert_one(data)

    @staticmethod
    def find_by_object_id(workspace_id):
        return mongo_flow_cytometry.db.workspaces.find_one({"_id": workspace_id})

    @staticmethod
    def find_by_progressive_id(workspace_id):
        return mongo_flow_cytometry.db.workspaces.find_one({"progressive_id": int(workspace_id)})

    @staticmethod
    def find_by_project_id(project_id):
        return mongo_flow_cytometry.db.workspaces.find({"project_id": project_id})

    @staticmethod
    def delete_by_progressive_id(progressive_id):
        return mongo_flow_cytometry.db.workspaces.delete_one({"progressive_id": int(progressive_id)})   

    
    
# create the model for the flow cytometry pipeline
class FlowCytoPipeline:
    
    @staticmethod
    def get_next_sequence():
        sequence = mongo_flow_cytometry.db.flow_cyto_pipeline_counter.find_one_and_update(
            {"_id": "pipeline_id"},
            {"$inc": {"sequence_value": 1}},
            return_document=True,
            upsert=True  # Create the document if it doesn't exist
        )

        # If sequence is None, initialize the counter
        if sequence is None:
            mongo_flow_cytometry.db.flow_cyto_pipeline_counter.insert_one({"_id": "pipeline_id", "sequence_value": 1})
            return 1

        return sequence["sequence_value"]

    @staticmethod
    def create_pipeline_data(data):
        data["progressive_id"] = FlowCytoPipeline.get_next_sequence()  # Add the progressive_id
        return mongo_flow_cytometry.db.flow_cyto_pipeline.insert_one(data)

    @staticmethod
    def find_by_object_id(pipeline_id):
        return mongo_flow_cytometry.db.flow_cyto_pipeline.find_one({"_id": pipeline_id})

    @staticmethod
    def find_by_progressive_id(pipeline_id):
        return mongo_flow_cytometry.db.flow_cyto_pipeline.find_one({"progressive_id": int(pipeline_id)})

    @staticmethod
    def find_by_project_id(project_id):
        return mongo_flow_cytometry.db.flow_cyto_pipeline.find({"project_id": project_id})

    @staticmethod
    def delete_by_progressive_id(progressive_id):
        return mongo_flow_cytometry.db.flow_cyto_pipeline.delete_one({"progressive_id": int(progressive_id)})
    
    
# model for running pipeline
class FlowCytoPipelineRun:
    @staticmethod
    def get_next_sequence():
        sequence = mongo_flow_cytometry.db.flow_cyto_pipeline_run_counter.find_one_and_update(
            {"_id": "pipeline_run_id"},
            {"$inc": {"sequence_value": 1}},
            return_document=True,
            upsert=True  # Create the document if it doesn't exist
        )

        # If sequence is None, initialize the counter
        if sequence is None:
            mongo_flow_cytometry.db.flow_cyto_pipeline_run_counter.insert_one({"_id": "pipeline_run_id", "sequence_value": 1})
            return 1

        return sequence["sequence_value"]

    @staticmethod
    def create_pipeline_run_data(data):
        data["progressive_id"] = FlowCytoPipelineRun.get_next_sequence()  # Add the progressive_id
        return mongo_flow_cytometry.db.flow_cyto_pipeline_run.insert_one(data)
    
    @staticmethod
    def find_by_object_id(pipeline_run_id):
        return mongo_flow_cytometry.db.flow_cyto_pipeline_run.find_one({"_id": pipeline_run_id})
    
    @staticmethod
    def find_by_progressive_id(pipeline_run_id):
        return mongo_flow_cytometry.db.flow_cyto_pipeline_run.find_one({"progressive_id": int(pipeline_run_id)})
    
    # find by project id
    @staticmethod
    def find_by_project_id(project_id):
        return mongo_flow_cytometry.db.flow_cyto_pipeline_run.find({"project_id": str(project_id)})
    
    
    @staticmethod
    def find_by_pipeline_id(pipeline_id):
        return mongo_flow_cytometry.db.flow_cyto_pipeline_run.find({"pipeline_id": pipeline_id})
    
    @staticmethod
    def delete_by_progressive_id(progressive_id):
        # when deleting a pipeline run, delete also the files associated with the pipeline run
        pipeline_run = mongo_flow_cytometry.db.flow_cyto_pipeline_run.find_one({"progressive_id": int(progressive_id)})
        for field in pipeline_run.keys():
            print(field)
            if "path" in field:
                # if the file exists, delete it
                if os.path.exists(pipeline_run[field]):
                    os.remove(pipeline_run[field])
        return mongo_flow_cytometry.db.flow_cyto_pipeline_run.delete_one({"progressive_id": int(progressive_id)})
    
    @staticmethod
    def update_pipeline_run_data(pipeline_run_id, data):
        return mongo_flow_cytometry.db.flow_cyto_pipeline_run.update_one({"_id": pipeline_run_id}, {"$set": data})
    
     
class ProjectModel:
    @staticmethod
    def find_by_progressive_id(project_id):
        return mongo_auth.db.projects.find_one({"progressive_id": int(project_id)})
    
class UserModel:
    @staticmethod
    def find_by_username(username):
        return mongo_auth.db.users.find_one({"username": username})
    
class MemberModel:
    @staticmethod
    def find_by_user_id_project_id(user_id, project_id):
        return mongo_auth.db.members.find_one({"user_id": user_id, "project_id": project_id})