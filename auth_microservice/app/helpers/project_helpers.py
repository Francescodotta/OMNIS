from app.models.project_models import ProjectModel, MemberModel, ConditionProjects
from app.models.auth_models import UserModel

# validate project data
def validate_data_for_project_creation(data, action):
    print(data)
    # take the fields value from the model and check that the data contains all the fields

    if ProjectModel.db_fields is None:
        return {"error": "Internal server error: db_fields is not defined"}, 500

    if not all(key in data for key in ProjectModel.db_fields.keys()):
        print(data)
        return {"error": "Missing fields"}, 400

    # check that the data types are correct
    for key in data:
        if not isinstance(data[key], ProjectModel.db_fields[key]):
            print("error data type")
            return {"error": f"Invalid type for field {key}"}, 400
    
    # check that the project name is unique --> add the decrypt step to find the project name 
    if action == "create":
        if ProjectModel.find_by_name(data['name']):
            return {"error": "A project with this name already exists"}, 400

    return None, 200


# funzione per validare i dati da mettere in PUT per la modifica di un progetto
def validate_data_for_project_update(data, progressive_id):
    # check that the data contains at least one field
    if len(data) == 0:
        return {"error": "Missing fields"}, 400

    # check that the data types are correct
    for key in data:
        if not isinstance(data[key], ProjectModel.db_fields[key]):
            return {"error": f"Invalid type for field {key}"}, 400

    # check that the project name is unique, it can be the same as its own name
    if 'name' in data:
        project = ProjectModel.find_by_name(data['name'])
        if project and project['progressive_id'] != progressive_id:
            return {"error": "A project with this name already exists"}, 400

    # check the lenght of the project name
    if 'name' in data:
        if len(data['name']) > 50:
            return {"error": "Project name too long"}, 400
        if len(data['name']) < 3:
            return {"error": "Project name too short"}, 400

    return None, 200


# check ownership
def check_project_ownership(user_id, project_id):
    member = MemberModel.find_by_user_id_and_project_id(user_id, project_id)
    # check that the user is a member of the project
    if member is None:
        return {"error": "User is not a member of the project"}, 400
    if member['role'] != "PI":
        return {"error": "User is not the PI of the project"}, 400
    return None, 200


## VALIDATE MEMBER DATA
def validate_data_member_creation(data, project_id):
    if MemberModel.db_fields is None:
        return {"error": "Internal server error: db_fields is not defined"}, 500

    if not all(key in data for key in MemberModel.db_fields.keys()):
        return {"error": "Missing fields"}, 400

    for key in data:
        if not isinstance(data[key], MemberModel.db_fields[key]):
            print(project_id.dtype)
            return {"error": f"Invalid type for field {key}"}, 400

    # check that the user_id exists in the user db
    user = UserModel.find_user_by_id(int(data['user_id']))
    if user is None:
        return {"error": "User not found"}, 404
    
    # check that the project_id exists in the project db
    project = ProjectModel.find_by_progressive_id(project_id)
    if project is None:
        return {"error": "Project not found"}, 404
    
    # check that the user is not already a member of the project
    member = MemberModel.find_by_user_id_and_project_id(int(data['user_id']), project_id)
    if member:
        return {"error": "User is already a member of the project"}, 400
    
    return None, 200


def validate_data_member_update(data, member_id):
    # find the member in the db
    member = MemberModel.find_by_progressive_id(member_id)
    if member is None:
        return {"error": "Member not found"}, 404
    # the data must contain only the role field
    if "role" not in data:
        return {"error": "Missing fields"}, 400
    # check that the data types are correct
    if not isinstance(data['role'], MemberModel.db_fields['role']):
        return {"error": "Invalid type for field role"}, 400
    # check that the role is a valid role
    if data['role'] not in ["PI", "Co-PI", "Member"]:
        return {"error": "Invalid role"}, 400
    # check that there are no other updated field other than role
    if len(data) > 1:
        return {"error": "You can update only the role of the member"}, 400
    return None, 200

def check_project_membership(user_id, project_id):
    member = MemberModel.find_by_user_id_and_project_id(user_id, project_id)
    if member is None:
        return {"error": "User is not a member of the project"}, 400
    return None, 200


def validate_experiment_data_against_standardized_fields(experiment_data, project_id):
    """
    Validate experiment data against the project's standardized fields
    This function should be called when creating/updating experiments
    """
    # get all required standardized fields for the project
    required_fields = ConditionProjects.find_required_standardized_fields_by_project_id(project_id)
    
    validation_errors = []
    
    for field in required_fields:
        field_name = field["field_name"]
        field_type = field["data_type"]
        validation_rules = field.get("validation_rules", {})
        
        # check if required field is present
        if field["is_required"] and field_name not in experiment_data:
            validation_errors.append(f"Required field '{field_name}' is missing")
            continue
        
        if field_name in experiment_data:
            value = experiment_data[field_name]
            
            # validate data type
            if not validate_field_data_type(value, field_type):
                validation_errors.append(f"Field '{field_name}' has invalid data type. Expected: {field_type}")
            
            # validate against predefined values
            if field.get("field_values") and value not in field["field_values"]:
                validation_errors.append(f"Field '{field_name}' value must be one of: {field['field_values']}")
            
            # validate against custom rules
            if validation_rules:
                rule_errors = validate_against_custom_rules(value, validation_rules, field_name)
                validation_errors.extend(rule_errors)
    
    return validation_errors

def validate_standardized_field_data(data, project_id, action="create", field_id=None):
    """Validate standardized field data structure and rules"""
    required_fields = ["field_type", "field_name", "data_type"]
    
    # check required fields
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing required field: {field}"}, 400
    
    # validate field_type
    valid_types = ["condition", "sample_preparation", "treatment", "protocol", "custom"]
    if data["field_type"] not in valid_types:
        return {"error": f"Invalid field_type. Must be one of: {valid_types}"}, 400
    
    # validate data_type
    valid_data_types = ["select", "text", "number", "boolean", "date"]
    if data["data_type"] not in valid_data_types:
        return {"error": f"Invalid data_type. Must be one of: {valid_data_types}"}, 400
    
    # check for duplicate field names in the same project
    if action == "create" or (action == "update" and "field_name" in data):
        existing_field = ConditionProjects.find_standardized_field_by_name_and_project(
            data["field_name"], project_id, exclude_id=field_id
        )
        if existing_field:
            return {"error": f"Field name '{data['field_name']}' already exists in this project"}, 400
    
    return {"message": "Validation passed"}, 200

def validate_field_data_type(value, expected_type):
    """Validate if a value matches the expected data type"""
    try:
        if expected_type == "text":
            return isinstance(value, str)
        elif expected_type == "number":
            return isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit())
        elif expected_type == "boolean":
            return isinstance(value, bool) or value in ["true", "false", "True", "False", 1, 0]
        elif expected_type == "date":
            from datetime import datetime
            if isinstance(value, str):
                datetime.strptime(value, "%Y-%m-%d")
                return True
            return False
        elif expected_type == "select":
            return isinstance(value, str)
    except:
        return False
    
    return True

def validate_against_custom_rules(value, rules, field_name):
    """Validate value against custom validation rules"""
    errors = []
    
    if "min_length" in rules and len(str(value)) < rules["min_length"]:
        errors.append(f"Field '{field_name}' must be at least {rules['min_length']} characters")
    
    if "max_length" in rules and len(str(value)) > rules["max_length"]:
        errors.append(f"Field '{field_name}' must not exceed {rules['max_length']} characters")
    
    if "pattern" in rules:
        import re
        if not re.match(rules["pattern"], str(value)):
            errors.append(f"Field '{field_name}' does not match required pattern")
    
    if "min_value" in rules and isinstance(value, (int, float)) and value < rules["min_value"]:
        errors.append(f"Field '{field_name}' must be at least {rules['min_value']}")
    
    if "max_value" in rules and isinstance(value, (int, float)) and value > rules["max_value"]:
        errors.append(f"Field '{field_name}' must not exceed {rules['max_value']}")
    
    return errors

def validate_standardized_field_creation_batch(fields_data, project_id):
    """Validate multiple standardized fields for batch creation"""
    validation_errors = []
    field_names = set()
    
    for i, field_data in enumerate(fields_data):
        # Validate individual field
        validation_error, status_code = validate_standardized_field_data(field_data, project_id, action="create")
        if status_code != 200:
            validation_errors.append(f"Field {i+1}: {validation_error['error']}")
        
        # Check for duplicate names within the batch
        field_name = field_data.get("field_name")
        if field_name in field_names:
            validation_errors.append(f"Field {i+1}: Duplicate field name '{field_name}' in batch")
        field_names.add(field_name)
    
    if validation_errors:
        return {"error": "Batch validation failed", "details": validation_errors}, 400
    
    return {"message": "Batch validation passed"}, 200


def generate_field_template(field_type):
    """Generate a template for creating standardized fields"""
    templates = {
        "condition": {
            "field_type": "condition",
            "field_name": "New Condition",
            "field_description": "Describe the experimental condition",
            "field_values": [],
            "is_required": False,
            "data_type": "select",
            "validation_rules": {}
        },
        "sample_preparation": {
            "field_type": "sample_preparation",
            "field_name": "Sample Preparation Step",
            "field_description": "Describe the sample preparation procedure",
            "field_values": [],
            "is_required": True,
            "data_type": "text",
            "validation_rules": {
                "min_length": 5,
                "max_length": 500
            }
        },
        "treatment": {
            "field_type": "treatment",
            "field_name": "Treatment Protocol",
            "field_description": "Describe the treatment applied",
            "field_values": [],
            "is_required": False,
            "data_type": "text",
            "validation_rules": {}
        },
        "protocol": {
            "field_type": "protocol",
            "field_name": "Protocol Reference",
            "field_description": "Reference to the protocol used",
            "field_values": [],
            "is_required": False,
            "data_type": "text",
            "validation_rules": {}
        },
        "custom": {
            "field_type": "custom",
            "field_name": "Custom Field",
            "field_description": "Custom field description",
            "field_values": [],
            "is_required": False,
            "data_type": "text",
            "validation_rules": {}
        }
    }
    
    return templates.get(field_type, templates["custom"])


def validate_field_dependencies(field_data, project_id):
    """Validate if field has dependencies on other fields"""
    # This can be extended to check for field dependencies
    # For now, just basic validation
    dependencies = field_data.get("dependencies", [])
    
    if dependencies:
        for dep_field_id in dependencies:
            dep_field = ConditionProjects.find_standardized_field_by_id(dep_field_id)
            if not dep_field or dep_field["project_id"] != project_id:
                return {"error": f"Dependent field {dep_field_id} not found in project"}, 400
    
    return {"message": "Dependencies validated"}, 200


def check_field_usage_safety(field_id):
    """Check if it's safe to modify/delete a field based on its usage"""
    usage_count = ConditionProjects.count_field_usage_in_experiments(field_id)
    
    if usage_count == 0:
        return {"safe": True, "message": "Field is not used in any experiments"}, 200
    elif usage_count <= 5:
        return {
            "safe": False, 
            "warning": True,
            "message": f"Field is used in {usage_count} experiments. Proceed with caution."
        }, 200
    else:
        return {
            "safe": False,
            "warning": False,
            "message": f"Field is heavily used in {usage_count} experiments. Modification not recommended."
        }, 400


def sanitize_field_data(field_data):
    """Sanitize and clean field data before saving"""
    sanitized = field_data.copy()
    
    # Clean field name
    if "field_name" in sanitized:
        sanitized["field_name"] = sanitized["field_name"].strip()
    
    # Clean description
    if "field_description" in sanitized:
        sanitized["field_description"] = sanitized["field_description"].strip()
    
    # Clean field values
    if "field_values" in sanitized and isinstance(sanitized["field_values"], list):
        sanitized["field_values"] = [str(value).strip() for value in sanitized["field_values"] if str(value).strip()]
    
    # Ensure validation rules is a dict
    if "validation_rules" not in sanitized:
        sanitized["validation_rules"] = {}
    
    return sanitized


def export_standardized_fields_config(project_id):
    """Export standardized fields configuration for backup/import"""
    fields = list(ConditionProjects.find_standardized_fields_by_project_id(project_id))
    
    export_data = {
        "project_id": project_id,
        "export_date": mongo.db.condition_projects.find_one()["created_at"] if fields else None,
        "fields": []
    }
    
    for field in fields:
        field.pop("_id", None)
        field.pop("progressive_id", None)
        field.pop("project_id", None)
        field.pop("created_at", None)
        field.pop("updated_at", None)
        export_data["fields"].append(field)
    
    return export_data


def import_standardized_fields_config(config_data, project_id):
    """Import standardized fields configuration from backup"""
    validation_errors = []
    
    if "fields" not in config_data:
        return {"error": "Invalid configuration format"}, 400
    
    # Validate all fields first
    for i, field_data in enumerate(config_data["fields"]):
        validation_error, status_code = validate_standardized_field_data(field_data, project_id, action="create")
        if status_code != 200:
            validation_errors.append(f"Field {i+1}: {validation_error['error']}")
    
    if validation_errors:
        return {"error": "Import validation failed", "details": validation_errors}, 400
    
    # Import all fields
    try:
        field_ids = ConditionProjects.bulk_create_standardized_fields(config_data["fields"], project_id)
        return {
            "message": f"Successfully imported {len(field_ids)} standardized fields",
            "field_ids": field_ids
        }, 201
    except Exception as e:
        return {"error": f"Import failed: {str(e)}"}, 500
