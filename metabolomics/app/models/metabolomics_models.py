from app import mongo_metabolomics, mongo_auth
from app.utils import security
import hashlib
from cryptography.fernet import Fernet
import os 
from datetime import datetime
import json

FERNET_SECRET_KEY = os.getenv("FERNET_SECRET_KEY")


class MetabolomicsModel:
    @staticmethod
    def get_next_sequence():
        sequence = mongo_metabolomics.db.metabolomics_exp_counter.find_one_and_update(
            {"_id": "project_id"},
            {"$inc": {"sequence_value": 1}},
            return_document=True,
            upsert=True  # Aggiungi upsert=True per creare il documento se non esiste
        )

            # Se sequence è None, inizializza il contatore
        if sequence is None:
            mongo_metabolomics.db.metabolomics_exp_counter.insert_one({"_id": "project_id", "sequence_value": 1})
            return 1

        return sequence["sequence_value"]
            
    @staticmethod
    def create_metabolomics_data(data):
        data["progressive_id"] = MetabolomicsModel.get_next_sequence()  # Aggiungi il progressive_id
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        # Initialize standardized_fields as empty dict if not provided
        if "standardized_fields" not in data:
            data["standardized_fields"] = {}
        return mongo_metabolomics.db.metabolomics.insert_one(data)

    @staticmethod
    def find_by_object_id(metabolomics_id):
            return mongo_metabolomics.db.metabolomics.find_one({"_id": metabolomics_id})

    @staticmethod
    def find_by_progressive_id(metabolomics_id):
        return mongo_metabolomics.db.metabolomics.find_one({"progressive_id": metabolomics_id})

    @staticmethod
    def find_by_project_id(project_id):
        return mongo_metabolomics.db.metabolomics.find({"project_id": project_id})
    
    @staticmethod
    def find_by_name_and_project(project_id, experiment_name):
        experiment_name_hash = hashlib.sha256(experiment_name.encode()).hexdigest()
        return mongo_metabolomics.db.metabolomics.find_one({"project_id": project_id, "experiment_name_hash": experiment_name_hash})
    
    @staticmethod
    def find_by_name(experiment_name):
        experiment_name_hash = hashlib.sha256(experiment_name.encode()).hexdigest()
        return mongo_metabolomics.db.metabolomics.find_one({"experiment_name_hash": experiment_name_hash})
    
    @staticmethod
    def delete_metabolomics_by_id(metabolomics_id):
        return mongo_metabolomics.db.metabolomics.delete_one({"progressive_id": metabolomics_id})

    # === STANDARDIZED FIELDS ASSIGNMENT METHODS ===
    
    @staticmethod
    def assign_standardized_fields(metabolomics_id, field_assignments):
        """
        Assign standardized field values to a metabolomics experiment
        
        Args:
            metabolomics_id: The progressive_id of the metabolomics experiment
            field_assignments: Dict mapping field_name to field_value
            Example: {
                "condition": "treated", 
                "sample_preparation": "enzymatic_digestion",
                "treatment_duration": "24h"
            }
        """
        return mongo_metabolomics.db.metabolomics.update_one(
            {"progressive_id": metabolomics_id},
            {
                "$set": {
                    "standardized_fields": field_assignments,
                    "updated_at": datetime.utcnow()
                }
            }
        )

    @staticmethod
    def update_single_standardized_field(metabolomics_id, field_name, field_value):
        """
        Update a single standardized field for a metabolomics experiment
        
        Args:
            metabolomics_id: The progressive_id of the metabolomics experiment
            field_name: Name of the standardized field
            field_value: Value to assign to the field
        """
        return mongo_metabolomics.db.metabolomics.update_one(
            {"progressive_id": metabolomics_id},
            {
                "$set": {
                    f"standardized_fields.{field_name}": field_value,
                    "updated_at": datetime.utcnow()
                }
            }
        )

    @staticmethod
    def remove_standardized_field(metabolomics_id, field_name):
        """
        Remove a standardized field assignment from a metabolomics experiment
        """
        return mongo_metabolomics.db.metabolomics.update_one(
            {"progressive_id": metabolomics_id},
            {
                "$unset": {f"standardized_fields.{field_name}": ""},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    @staticmethod
    def get_experiments_with_standardized_fields(project_id):
        """
        Get all metabolomics experiments in a project with their standardized field assignments
        """
        return mongo_metabolomics.db.metabolomics.find(
            {"project_id": project_id},
            {
                "progressive_id": 1,
                "experiment_name": 1,
                "standardized_fields": 1,
                "created_at": 1,
                "updated_at": 1
            }
        )

    @staticmethod
    def find_experiments_by_field_value(project_id, field_name, field_value):
        """
        Find metabolomics experiments by standardized field value
        
        Args:
            project_id: Project ID
            field_name: Name of the standardized field
            field_value: Value to search for
        """
        return mongo_metabolomics.db.metabolomics.find({
            "project_id": project_id,
            f"standardized_fields.{field_name}": field_value
        })

    @staticmethod
    def get_field_value_distribution(project_id, field_name):
        """
        Get distribution of values for a specific standardized field across all experiments
        
        Returns: List of dicts with value counts and experiment details
        """
        pipeline = [
            {"$match": {"project_id": project_id}},
            {"$group": {
                "_id": f"$standardized_fields.{field_name}",
                "count": {"$sum": 1},
                "experiments": {
                    "$push": {
                        "progressive_id": "$progressive_id",
                        "experiment_name": "$experiment_name",
                        "created_at": "$created_at"
                    }
                }
            }},
            {"$sort": {"count": -1}}
        ]
        return list(mongo_metabolomics.db.metabolomics.aggregate(pipeline))

    @staticmethod
    def get_standardized_fields_summary(project_id):
        """
        Get a summary of all standardized fields usage across experiments in a project
        """
        pipeline = [
            {"$match": {"project_id": project_id}},
            {"$project": {
                "progressive_id": 1,
                "experiment_name": 1,
                "field_pairs": {"$objectToArray": "$standardized_fields"}
            }},
            {"$unwind": "$field_pairs"},
            {"$group": {
                "_id": "$field_pairs.k",
                "unique_values": {"$addToSet": "$field_pairs.v"},
                "usage_count": {"$sum": 1},
                "experiments_using": {"$addToSet": "$progressive_id"}
            }},
            {"$sort": {"usage_count": -1}}
        ]
        return list(mongo_metabolomics.db.metabolomics.aggregate(pipeline))

    @staticmethod
    def bulk_assign_standardized_fields(assignments):
        """
        Bulk assign standardized fields to multiple experiments
        
        Args:
            assignments: List of dicts with format:
            [
                {
                    "metabolomics_id": 123,
                    "field_assignments": {"condition": "treated", "time_point": "24h"}
                },
                ...
            ]
        """
        bulk_operations = []
        for assignment in assignments:
            bulk_operations.append({
                "updateOne": {
                    "filter": {"progressive_id": assignment["metabolomics_id"]},
                    "update": {
                        "$set": {
                            "standardized_fields": assignment["field_assignments"],
                            "updated_at": datetime.utcnow()
                        }
                    }
                }
            })
        
        if bulk_operations:
            return mongo_metabolomics.db.metabolomics.bulk_write(bulk_operations)
        return None

    @staticmethod
    def validate_field_assignment(project_id, field_name, field_value):
        """
        Validate a field assignment against the standardized field definition.
        If the field is not defined, allow it as a user-defined field.
        """
        try:
            # Get the standardized field definition from auth database
            field_def = mongo_auth.db.condition_projects.find_one({
                "project_id": project_id,
                "field_name": field_name
            })
            
            if not field_def:
                # Allow user-defined fields
                return True, "User-defined field"
            
            # Check if field has predefined values (select type)
            if field_def.get("field_values") and len(field_def["field_values"]) > 0:
                if field_value not in field_def["field_values"]:
                    return False, f"Value '{field_value}' not allowed. Valid values: {field_def['field_values']}"
            
            # Check data type validation
            data_type = field_def.get("data_type", "text")
            
            if data_type == "number":
                try:
                    float(field_value)
                except (ValueError, TypeError):
                    return False, f"Field '{field_name}' requires a numeric value"
            
            elif data_type == "boolean":
                if field_value not in [True, False, "true", "false", 1, 0, "1", "0"]:
                    return False, f"Field '{field_name}' requires a boolean value"
            
            elif data_type == "date":
                try:
                    datetime.fromisoformat(str(field_value))
                except ValueError:
                    return False, f"Field '{field_name}' requires a valid date format"
            
            # Check validation rules if any
            validation_rules = field_def.get("validation_rules", {})
            if validation_rules:
                # Add custom validation logic here based on your rules
                pass
            
            return True, "Valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def get_experiments_missing_required_fields(project_id):
        """
        Get experiments that are missing required standardized fields
        """
        # First get all required fields for the project
        required_fields = list(mongo_auth.db.condition_projects.find(
            {"project_id": project_id, "is_required": True},
            {"field_name": 1}
        ))
        
        if not required_fields:
            return []
        
        required_field_names = [field["field_name"] for field in required_fields]
        
        # Find experiments missing any required fields
        pipeline = [
            {"$match": {"project_id": project_id}},
            {
                "$project": {
                    "progressive_id": 1,
                    "experiment_name": 1,
                    "standardized_fields": 1,
                    "missing_fields": {
                        "$setDifference": [
                            required_field_names,
                            {"$ifNull": [{"$objectToArray": "$standardized_fields"}, []]}
                        ]
                    }
                }
            },
            {
                "$match": {
                    "$or": [
                        {"missing_fields": {"$ne": []}},
                        {"standardized_fields": {"$exists": False}}
                    ]
                }
            }
        ]
        
        return list(mongo_metabolomics.db.metabolomics.aggregate(pipeline))


# Keep existing classes unchanged
class AuthModel:
    @staticmethod
    def find_user_by_id(user_id):
        return mongo_auth.db.users.find_one({"progressive_id": user_id})
    
    @staticmethod
    def find_user_by_username(username):
        return mongo_auth.db.users.find_one({"username": username})


class ProjectModel:
    @staticmethod
    def find_by_id(project_id):
        return mongo_auth.db.projects.find_one({"progressive_id": int(project_id)})


class MemberModel:
    @staticmethod
    def find_by_project_id(project_id, user_id):
        return mongo_auth.db.members.find_one({"project_id": project_id, "user_id": user_id})


# Helper class to interact with standardized fields from auth database
class StandardizedFieldHelper:
    @staticmethod
    def get_project_standardized_fields(project_id, field_type=None):
        """
        Get standardized fields for a project from the auth database
        """
        query = {"project_id": project_id}
        if field_type and field_type != 'all':
            query["field_type"] = field_type
        
        return list(mongo_auth.db.condition_projects.find(query).sort("created_at", -1))

    @staticmethod
    def get_standardized_field_by_name(project_id, field_name):
        """
        Get a specific standardized field by name
        """
        return mongo_auth.db.condition_projects.find_one({
            "project_id": project_id,
            "field_name": field_name
        })

    @staticmethod
    def get_required_fields(project_id):
        """
        Get all required standardized fields for a project
        """
        return list(mongo_auth.db.condition_projects.find({
            "project_id": project_id,
            "is_required": True
        }))


# Keep existing PipelineModel unchanged
class PipelineModel:
    #get next sequence
    @staticmethod
    def get_next_sequence_value():
        sequence = mongo_metabolomics.db.pipeline_counter.find_one_and_update(
            {"_id": "project_id"},
            {"$inc": {"sequence_value": 1}},
            return_document=True,
            upsert=True  # Aggiungi upsert=True per creare il documento se non esiste
        )

            # Se sequence è None, inizializza il contatore
        if sequence is None:
            mongo_metabolomics.db.pipeline_counter.insert_one({"_id": "project_id", "sequence_value": 1})
            return 1

        return sequence["sequence_value"]
    
    @staticmethod
    def create_pipeline_data(data):
        data["progressive_id"] = PipelineModel.get_next_sequence_value()  # Aggiungi il progressive_id
        return mongo_metabolomics.db.pipeline.insert_one(data)
    
    @staticmethod
    def find_by_id(pipeline_id):
        return mongo_metabolomics.db.pipeline.find_one({"progressive_id": pipeline_id})
    
    @staticmethod
    def find_by_project_id(project_id):
        return mongo_metabolomics.db.pipeline.find({"project_id": project_id})
    
    @staticmethod
    def find_by_name(pipeline_name):
        pipeline_name_hash = hashlib.sha256(pipeline_name.encode()).hexdigest()
        return mongo_metabolomics.db.pipeline.find_one({"pipeline_name_hash": pipeline_name_hash})
    
    @staticmethod
    def find_by_progressive_id(progressive_id):
        return mongo_metabolomics.db.pipeline.find_one({"progressive_id": progressive_id})

    
    @staticmethod
    def delete_pipeline_by_id(pipeline_id):
        return mongo_metabolomics.db.pipeline.delete_one({"progressive_id": pipeline_id})