from app import mongo_metabolomics_pipeline

class PipelineModel:
    """
    Model to handle pipeline data for metabolomics
    """

    @staticmethod
    def find_by_task_id(task_id):
        """
        Find pipeline data by chain ID
        """
        return mongo_metabolomics_pipeline.db.pipeline.find_one({"task_id": task_id})
    
    @staticmethod
    def update_by_task_id(task_id, data):
        """
        Update pipeline data by chain ID
        """
        return mongo_metabolomics_pipeline.db.pipeline.update_one({"task_id": task_id}, {"$set": data})

    # update the status field to success or failure
    @staticmethod
    def update_status_by_task_id(task_id, status):
        """
        Update the status of a pipeline by task ID
        """
        return mongo_metabolomics_pipeline.db.pipeline.update_one(
            {"task_id": task_id},
            {"$set": {"status": status}}
        )

class MetabolomicsMatrixModel:
    """
    Model to handle metabolomics matrix data
    """

    @staticmethod
    def find_by_progressive_id(progressive_id):
        """
        Find metabolomics matrix data by progressive ID
        """
        return mongo_metabolomics_pipeline.db.metabolomics_matrix.find_one({"progressive_id": progressive_id})
    
    