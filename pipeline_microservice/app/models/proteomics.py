from app import mongo_proteomics_pipeline

# create the model for the proteomics pipeline
class ProteomicsPipelineModel:
    """
    Model to handle the database integration for the proteomics pipeline data
    
    
    """
    
    @staticmethod
    def find_by_task_id(task_id):
        return mongo_proteomics_pipeline.db.pipeline.find_one({'task_id':task_id})
    
    @staticmethod
    def update_by_task_id(task_id, data):
        return mongo_proteomics_pipeline.db.pipeline.update_one({'task_id':task_id}, {'$set':data})
