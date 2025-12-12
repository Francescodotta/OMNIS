from app import mongo_flow_cytometry_pipeline
import hashlib

# model for flow cytometry running pipeline
class FlowCytoPipelineRun:
    # get from progressive id
    @staticmethod
    def find_by_progressive_id(pipeline_run_id):
        return mongo_flow_cytometry_pipeline.db.flow_cyto_pipeline_run.find_one({"progressive_id": int(pipeline_run_id)})
    
    # get from chain id
    @staticmethod
    def find_by_chain_id(chain_id):
        return mongo_flow_cytometry_pipeline.db.flow_cyto_pipeline_run.find_one({"chain_id": chain_id})
    
    # update by chain id
    @staticmethod
    def update_by_chain_id(chain_id, data):
        return mongo_flow_cytometry_pipeline.db.flow_cyto_pipeline_run.update_one({"chain_id": chain_id}, {"$set": data})

        
    
class FlowCytometryModel:
    @staticmethod
    def find_by_progressive_id(flow_cytometry_id):
        return mongo_flow_cytometry_pipeline.db.flow_cytometry.find_one({"progressive_id": int(flow_cytometry_id)})
    
    @staticmethod
    def find_by_name(experiment_name):
        experiment_name_hash = hashlib.sha256(experiment_name.encode()).hexdigest()
        return mongo_flow_cytometry_pipeline.db.flow_cytometry.find_one({"experiment_name_hash": experiment_name_hash})
    