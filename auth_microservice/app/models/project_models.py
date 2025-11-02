from app import mongo
from bson import ObjectId


class ProjectModel():
    # define the mandatory fields of the model
    db_fields = {
        "name": str,
        "description": str,
        "field": str
    }

    @staticmethod
    def get_next_sequence():
        sequence = mongo.db.project_counter.find_one_and_update(
            {"_id": "project_id"},
            {"$inc": {"sequence_value": 1}},
            return_document=True,
            upsert=True  # Aggiungi upsert=True per creare il documento se non esiste
        )

        # Se sequence è None, inizializza il contatore
        if sequence is None:
            mongo.db.project_counter.insert_one({"_id": "project_id", "sequence_value": 1})
            return 1

        return sequence["sequence_value"]

    @staticmethod
    def create_project(project_data):
        project_data["progressive_id"] = ProjectModel.get_next_sequence()
        return mongo.db.projects.insert_one(project_data)

    @staticmethod
    def find_by_progressive_id(progressive_id):
        return mongo.db.projects.find_one({"progressive_id": progressive_id})

    @staticmethod
    def find_by_name(name):
        return mongo.db.projects.find_one({"name": name})
    
    @staticmethod
    def find_by_field(field):
        return mongo.db.projects.find({"field": field})

    @staticmethod
    def update_project(progressive_id, updated_data):
        return mongo.db.projects.update_one({"progressive_id": progressive_id}, {"$set": updated_data})
    
    @staticmethod
    def delete_project(progressive_id):
        # delete all the members of the project
        mongo.db.members.delete_many({"project_id": progressive_id})
        return mongo.db.projects.delete_one({"progressive_id": progressive_id})


class MemberModel():
    db_fields = {
        "user_id": int,
        "project_id": int,
        "role": str
    }

    @staticmethod
    def get_next_sequence():
        sequence = mongo.db.member_counter.find_one_and_update(
            {"_id": "project_id"},
            {"$inc": {"sequence_value": 1}},
            return_document=True,
            upsert=True  # Aggiungi upsert=True per creare il documento se non esiste
        )

        # Se sequence è None, inizializza il contatore
        if sequence is None:
            mongo.db.member_counter.insert_one({"_id": "project_id", "sequence_value": 1})
            return 1

        return sequence["sequence_value"]

    @staticmethod
    def create_member(member_data):
        member_data["progressive_id"] = MemberModel.get_next_sequence()
        return mongo.db.members.insert_one(member_data)
    
    @staticmethod
    def find_by_progressive_id(progressive_id):
        return mongo.db.members.find_one({"progressive_id": progressive_id})

    @staticmethod
    def find_by_user_id(user_id):
        return mongo.db.members.find({"user_id": user_id})
    
    @staticmethod
    def find_by_user_id_and_project_id(user_id, project_id):
        return mongo.db.members.find_one({"user_id": user_id, "project_id": project_id})
    
    @staticmethod
    def find_by_project_id(project_id):
        return mongo.db.members.find({"project_id": project_id})
    
    @staticmethod
    def find_by_role(role):
        return mongo.db.members.find({"role": role})
    
    @staticmethod
    def update_member(progressive_id, updated_data):
        return mongo.db.members.update_one({"progressive_id": progressive_id}, {"$set": updated_data})
    
    @staticmethod
    def delete_member(progressive_id):
        return mongo.db.members.delete_one({"progressive_id": progressive_id})
    
    @staticmethod
    def find_by_user_id_and_project_id(user_id, project_id):
        return mongo.db.members.find_one({"user_id": user_id, "project_id": project_id})

class ConditionProjects():
    @staticmethod
    def get_next_sequence():
        sequence = mongo.db.condition_projects_counter.find_one_and_update(
            {"_id": "condition_project_id"},  # Changed from "project_id" to be more specific
            {"$inc": {"sequence_value": 1}},
            return_document=True,
            upsert=True
        )

        # Se sequence è None, inizializza il contatore
        if sequence is None:
            mongo.db.condition_projects_counter.insert_one({"_id": "condition_project_id", "sequence_value": 1})
            return 1

        return sequence["sequence_value"]

    @staticmethod
    def create_standardized_field(field_data, project_id):
        """Create a new standardized field for a project"""
        from datetime import datetime
        field_data["progressive_id"] = ConditionProjects.get_next_sequence()
        field_data["project_id"] = project_id
        field_data["created_at"] = datetime.utcnow()
        field_data["updated_at"] = datetime.utcnow()
        result = mongo.db.condition_projects.insert_one(field_data)
        return field_data["progressive_id"]
    
    @staticmethod
    def create_condition_projects(condition_data, project_id):
        """Legacy method - kept for backward compatibility"""
        return ConditionProjects.create_standardized_field(condition_data, project_id)
    
    @staticmethod
    def find_by_progressive_id(progressive_id):
        """Find a standardized field by its progressive ID"""
        return mongo.db.condition_projects.find_one({"progressive_id": progressive_id})
    
    @staticmethod
    def find_standardized_field_by_id(field_id):
        """Find a standardized field by its ID"""
        return mongo.db.condition_projects.find_one({"progressive_id": field_id})
    
    @staticmethod
    def find_by_project_id(project_id):
        """Find all standardized fields for a project"""
        return mongo.db.condition_projects.find({"project_id": project_id})
    
    @staticmethod
    def find_standardized_fields_by_project_id(project_id):
        """Find all standardized fields for a project"""
        return mongo.db.condition_projects.find({"project_id": project_id})
    
    @staticmethod
    def find_standardized_fields_by_project_and_type(project_id, field_type):
        """Find standardized fields by project and field type"""
        return mongo.db.condition_projects.find({"project_id": project_id, "field_type": field_type})
    
    @staticmethod
    def find_required_standardized_fields_by_project_id(project_id):
        """Find all required standardized fields for a project"""
        return mongo.db.condition_projects.find({"project_id": project_id, "is_required": True})
    
    @staticmethod
    def update_standardized_field(progressive_id, updated_data):
        """Update a standardized field"""
        updated_data["updated_at"] = mongo.db.condition_projects.find_one({"progressive_id": progressive_id})
        return mongo.db.condition_projects.update_one(
            {"progressive_id": progressive_id}, 
            {"$set": updated_data}
        )
    
    @staticmethod
    def update_condition_projects(data, project_id):
        """Legacy method - kept for backward compatibility"""
        # This method needs to be clarified - what should it update?
        # For now, assuming it updates all fields for a project
        return mongo.db.condition_projects.update_many(
            {"project_id": project_id}, 
            {"$set": data}
        )
    
    @staticmethod
    def delete_standardized_field(progressive_id):
        """Delete a standardized field"""
        return mongo.db.condition_projects.delete_one({"progressive_id": progressive_id})
    
    @staticmethod
    def delete_condition_project(progressive_id):
        """Legacy method - kept for backward compatibility"""
        return ConditionProjects.delete_standardized_field(progressive_id)
    
    @staticmethod
    def find_standardized_field_by_name_and_project(field_name, project_id, exclude_id=None):
        """Find a standardized field by name and project, optionally excluding a specific ID"""
        query = {"field_name": field_name, "project_id": project_id}
        if exclude_id:
            query["progressive_id"] = {"$ne": exclude_id}  # Changed from ObjectId to progressive_id
        return mongo.db.condition_projects.find_one(query)
    
    @staticmethod
    def count_field_usage_in_experiments(field_id):
        """Count how many experiments use this standardized field"""
        # This assumes you have an experiments collection that references standardized fields
        return mongo.db.experiments.count_documents({
            "$or": [
                {"standardized_fields.field_id": field_id},
                {"conditions.field_id": field_id},
                {"sample_preparation.field_id": field_id}
            ]
        })
    
    @staticmethod
    def get_field_last_usage(field_id):
        """Get the last usage date of a standardized field"""
        # Find the most recent experiment that used this field
        experiment = mongo.db.experiments.find_one(
            {
                "$or": [
                    {"standardized_fields.field_id": field_id},
                    {"conditions.field_id": field_id},
                    {"sample_preparation.field_id": field_id}
                ]
            },
            sort=[("created_at", -1)]  # Most recent first
        )
        return experiment.get("created_at") if experiment else None
    
    @staticmethod
    def get_experiments_using_field(field_id):
        """Get all experiments that use this standardized field"""
        return list(mongo.db.experiments.find(
            {
                "$or": [
                    {"standardized_fields.field_id": field_id},
                    {"conditions.field_id": field_id},
                    {"sample_preparation.field_id": field_id}
                ]
            },
            {"_id": 1, "name": 1, "progressive_id": 1, "created_at": 1}
        ))
    
    @staticmethod
    def bulk_create_standardized_fields(fields_data, project_id):
        """Create multiple standardized fields at once"""
        prepared_fields = []
        for field_data in fields_data:
            field_data["progressive_id"] = ConditionProjects.get_next_sequence()
            field_data["project_id"] = project_id
            prepared_fields.append(field_data)
        
        result = mongo.db.condition_projects.insert_many(prepared_fields)
        return [field["progressive_id"] for field in prepared_fields]
    
    @staticmethod
    def get_field_statistics(project_id):
        """Get statistics about standardized fields usage in a project"""
        pipeline = [
            {"$match": {"project_id": project_id}},
            {
                "$lookup": {
                    "from": "experiments",
                    "let": {"field_id": "$progressive_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$or": [
                                        {"$in": ["$$field_id", "$standardized_fields.field_id"]},
                                        {"$in": ["$$field_id", "$conditions.field_id"]},
                                        {"$in": ["$$field_id", "$sample_preparation.field_id"]}
                                    ]
                                }
                            }
                        }
                    ],
                    "as": "usage"
                }
            },
            {
                "$project": {
                    "field_name": 1,
                    "field_type": 1,
                    "is_required": 1,
                    "usage_count": {"$size": "$usage"},
                    "last_used": {"$max": "$usage.created_at"}
                }
            }
        ]
        
        return list(mongo.db.condition_projects.aggregate(pipeline))
    
    @staticmethod
    def validate_field_constraints(field_id, value):
        """Validate a value against a standardized field's constraints"""
        field = ConditionProjects.find_by_progressive_id(field_id)
        if not field:
            return False, "Field not found"
        
        # Check if value is in predefined values (if any)
        if field.get("field_values") and value not in field["field_values"]:
            return False, f"Value must be one of: {field['field_values']}"
        
        # Check data type validation
        data_type = field.get("data_type", "text")
        validation_rules = field.get("validation_rules", {})
        
        # Add your validation logic here based on data_type and validation_rules
        # This is a simplified example
        if data_type == "number":
            try:
                float(value)
            except ValueError:
                return False, "Value must be a number"
        
        return True, "Valid"
