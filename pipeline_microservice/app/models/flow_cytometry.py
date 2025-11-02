from app import mongo_flow_cytometry_pipeline

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