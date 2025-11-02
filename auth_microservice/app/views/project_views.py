from app.models.project_models import ProjectModel, MemberModel, ConditionProjects
from app.models.auth_models import UserModel
import app.helpers.project_helpers as project_helpers
import logging
from cryptography.fernet import Fernet
import os


# Configura logging per eventuali errori
logger = logging.getLogger("custom_info_logger")
# configura la crittografia
FERNET_SECRET_KEY = os.getenv('FERNET_SECRET_KEY')   


# PROJECT VIEWS
def create_project_views(data, user):
    validation_error, status_code = project_helpers.validate_data_for_project_creation(data, action="create")
    print(validation_error)
    # when the project is created, the user that created the project must be the PI of the project
    if status_code != 200:
        logger.error(f"Error creating project: {validation_error['message']}", extra={"username": user})
        return validation_error, status_code
    
    ProjectModel.create_project(data)
    logger.info(f"Project {data['name']} created successfully", extra={"username": user})
    # find the progressive id 
    project = ProjectModel.find_by_name(data['name'])
    
    user = UserModel.find_by_username(user)
    if user is None:
        logger.error(f"User {user} not found", extra={"username": user})
        # delete the project
        ProjectModel.delete_project(project['progressive_id'])
        return {"error": "User not found"}, 404

    # create the member for the project
    member_data = {
        "project_id": project['progressive_id'],
        "user_id": user['progressive_id'],
        "role": "PI"
    }
    validation_error, status_code = project_helpers.validate_data_member_creation(member_data, project['progressive_id'])
    if status_code != 200:
        logger.error(f"Error creating member for project: {validation_error['message']}", extra={"username": user})
        ProjectModel.delete_project(project['progressive_id'])
        logger.error(f"Project {project['name']} deleted due to error in PI creation", extra={"username": user})
        return validation_error, status_code
    MemberModel.create_member(member_data)
    logger.info(f"Member for project {project['name']} created successfully", extra={"username": user})
    return {"message": "Project created successfully", "progressive_id": project['progressive_id']}, 201

def get_project_by_id_views(progressive_id, username):
    user = UserModel.find_by_username(username)
    if user is None:
        logger.error(f"User {username} not found", extra={"username": username})
        return {"error": "User not found"}, 404
    # check project membership
    membership, status_code  = project_helpers.check_project_membership(user['progressive_id'], progressive_id)
    if status_code != 200:
        logger.error(f"Error getting project: {membership['error']}", extra={"username": username})
        return membership, status_code
    project = ProjectModel.find_by_progressive_id(progressive_id)
    if project is None:
        logger.error(f"Project not found", extra={"username": username})
        return {"error": "Project not found"}, 404
    project.pop("_id") 
    logger.info(f"Project {project['name']} retrieved successfully", extra={"username": username})
    return project, 200

def update_project_by_id_views(progressive_id, data, username):
    # validate the data
    project = ProjectModel.find_by_progressive_id(progressive_id)
    if project is None:
        logger.error(f"Project not found", extra={"username": username})
        return {"error": "Project not found"}, 404
    validation_error, status_code = project_helpers.validate_data_for_project_update(data, progressive_id)
    if status_code != 200:
        logger.error(f"Error updating project: {validation_error['message']}", extra={"username": username})
        return validation_error, status_code
    project = ProjectModel.update_project(progressive_id, data)
    logger.info(f"Project {project['name']} updated successfully", extra={"username": username})
    return {"message": "Project updated successfully"}, 200 

def delete_project_by_progressive_id_views(progressive_id, user):

    # project search
    project = ProjectModel.find_by_progressive_id(progressive_id)
    if project is None:
        logger.error(f"Project not found", extra={"username": user})
        return {"error": "Project not found"}, 404
    
    # user search
    user = UserModel.find_by_username(user)
    if user is None:
        logger.error(f"User not found", extra={"username": user})
        return {"error": "User not found"}, 404
    
    # membership of the user    
    member = MemberModel.find_by_user_id_and_project_id(user['progressive_id'], progressive_id)
    if member is None:
        logger.error(f"User not a member of the project", extra={"username": user})
        return {"error": "User not a member of the project"}, 404
    if member['role'] != "PI":
        logger.error(f"User not authorized to delete project", extra={"username": user})
        return {"error": "User not authorized to delete project"}, 401
    
    ProjectModel.delete_project(progressive_id)
    logger.info(f"Project {project['name']} deleted successfully", extra={"username": user})
    return {"message": "Project deleted successfully"}, 200


## MEMBERS VIEWS
def create_member_views(data, username, project_id):
    # get the user id
    user = UserModel.find_by_username(username)
    # transform the project_id and user id in int in the data
    data["user_id"] = int(data["user_id"])
    data["project_id"] = int(data["project_id"])
    if user is None:
        return {"error": "User not found"}, 404
    # check if the user is the PI of the project
    membership, status_code = project_helpers.check_project_ownership(int(user['progressive_id']), int(project_id))
    if status_code != 200:
        return membership, status_code
    # validate the data using the helper function
    validation_error, status_code = project_helpers.validate_data_member_creation(data, project_id)
    if status_code != 200:
        return validation_error, status_code
    # create the db instance
    MemberModel.create_member(data)
    return {"message": "Member created successfully"}, 201

def get_member_by_id_views(member_id, username):
    user = UserModel.find_by_username(username)
    if user is None:
        return {"error": "User not found"}, 404
    membership_result, status_code = project_helpers.check_project_membership(user['progressive_id'], member_id)
    print(membership_result)
    if status_code != 200:
        return membership_result, status_code
    member = MemberModel.find_by_progressive_id(member_id)
    if member is None:
        return {"error": "Member not found"}, 404
    member.pop("_id")
    return member, 200

def update_member_by_id_views(member_id, data):
    validation_error, status_code = project_helpers.validate_data_member_update(data, member_id)
    if status_code != 200:
        return validation_error, status_code
    member_result = MemberModel.update_member(member_id, data)
    # check if the member was updated
    if member_result.modified_count == 0:
        return {"error": "Member not updated"}, 500
    return {"message": "Member updated successfully"}, 200

def delete_member_by_id_views(member_id, user):
    user = UserModel.find_by_username(user)
    if user is None:
        return {"error": "User not found"}, 404
    membership, status_code = project_helpers.check_project_ownership(user['progressive_id'], member_id)
    if status_code != 200:
        return membership, status_code
    member = MemberModel.find_by_progressive_id(member_id)
    if member is None:
        return {"error": "Member not found"}, 404
    MemberModel.delete_member(member_id)
    return {"message": "Member deleted successfully"}, 200

# get all the members for a project
def get_members_for_project_views(project_id, username):
    user = UserModel.find_by_username(username)
    if user is None:
        return {"error": "User not found"}, 404
    # check that the user is a member of the project
    membership, status_code = project_helpers.check_project_membership(user['progressive_id'], project_id)
    if status_code != 200:
        return membership, status_code
    members = MemberModel.find_by_project_id(project_id)
    if members is None:
        return {"error": "Members not found"}, 404
    # members is a cursor object, convert it to a list
    members = list(members)
    # use the user_id to get the user data
    for member in members:
        member.pop("_id")
        user = UserModel.find_user_by_id(member['user_id'])
        member['username'] = user['username']
    return members, 200


# get all the projects of a user
def get_projects_for_user_views(user):
    user = UserModel.find_by_username(user)
    if user is None:
        return {"error": "User not found"}, 404
    projects = MemberModel.find_by_user_id(user['progressive_id'])
    if projects is None:
        return {"error": "Projects not found"}, 404
    projects = list(projects)
    proj_response = []
    for project in projects:
        project_data = ProjectModel.find_by_progressive_id(project['project_id'])
        project_data.pop("_id")
        proj_response.append(project_data)
    
    return proj_response, 200


# create member from project creation
def create_member_from_project_creation(project_id, user):
    print(f"Creating member for project {project_id} and user {user}")
    # create the data form
    # get the user id
    user = UserModel.find_by_username(user)
    if user is None:
        return {"error": "User not found"}, 404
    data = {
        "project_id": project_id,
        "user_id": user['progressive_id'],
        "role": "PI"
    }
    validation_error, status_code = project_helpers.validate_data_member_creation(data)
    if status_code != 200:
        return validation_error, status_code
    # create the db instance
    MemberModel.create_member(data)
    return {"message": "Member created successfully"}, 201


def get_nonmembers_for_project_views(project_id, username):
    user = UserModel.find_by_username(username)
    if user is None:
        return {"error": "User not found"}, 404
    # check that the user is a member of the project
    membership, status_code = project_helpers.check_project_membership(user['progressive_id'], project_id)
    if status_code != 200:
        return membership, status_code
    members = MemberModel.find_by_project_id(project_id)
    if members is None:
        return {"error": "Members not found"}, 404
    members = list(members)
    # get all the users
    users = UserModel.get_all_users()
    users = list(users)
    # create a list of usernames
    user_list = [user['progressive_id'] for user in users]
    # create a list of usernames of the members
    member_list = [member['user_id'] for member in members]
    # get the difference
    nonmembers = list(set(user_list) - set(member_list))
    # get all the users that are not members
    nonmembers_list = []
    for user in nonmembers:
        user_data = UserModel.find_user_by_id(user)
        user_data.pop("_id")
        nonmembers_list.append(user_data)
        
    # use the fernet key to decrypt the username
    fernet = Fernet(FERNET_SECRET_KEY)
    nonmembers = []
    # decrypt the username and pass it to the frontend
    for user in nonmembers_list:
        nonmembers.append({
            "progressive_id": user['progressive_id'],
            "username": user['username']
        })
    return nonmembers, 200


# CRUD OPERATIONS FOR STANDARDIZED FIELDS OF EXPERIMENTS IN THE SPECIFIC PROJECTS

# create a standardized field
def create_standardized_field_for_project_views(data, username, project_id):
    """
    Create a standardized field template for a project.
    Fields can be: conditions, sample_preparation, treatments, protocols, etc.
    
    Expected data structure:
    {
        "field_type": "condition|sample_preparation|treatment|protocol|custom",
        "field_name": "Temperature Condition",
        "field_description": "Temperature settings for the experiment",
        "field_values": ["4°C", "37°C", "RT"],  # predefined values (optional)
        "is_required": true,
        "data_type": "select|text|number|boolean|date",
        "validation_rules": {
            "min_length": 1,
            "max_length": 100,
            "pattern": "^[0-9]+°C$"  # regex for validation
        }
    }
    """
    # get the user id
    user = UserModel.find_by_username(username)
    if user is None:
        return {"error": "User not found"}, 404
    
    # check project membership and permissions
    membership, status_code = project_helpers.check_project_membership(user['progressive_id'], project_id)
    if status_code != 200:
        return membership, status_code
    
    # check that the project exists in the database
    project = ProjectModel.find_by_progressive_id(project_id)
    if project is None:
        return {"error": "Project not found"}, 404
    
    # validate the standardized field data
    validation_error, status_code = project_helpers.validate_standardized_field_data(data, project_id, action="create")
    if status_code != 200:
        return validation_error, status_code
    
    # create the standardized field
    field_id = ConditionProjects.create_standardized_field(data, project_id)
    logger.info(f"Standardized field '{data['field_name']}' created for project {project_id}", 
                extra={"username": username})
    
    return {
        "message": "Standardized field created successfully", 
        "field_id": field_id
    }, 201
    

def update_standardized_field_for_project_views(field_id, data, username, project_id):
    """Update an existing standardized field"""
    user = UserModel.find_by_username(username)
    if user is None:
        return {"error": "User not found"}, 404
    
    # check project membership and permissions
    membership, status_code = project_helpers.check_project_membership(user['progressive_id'], project_id)
    if status_code != 200:
        return membership, status_code
    
    # check that the field exists
    existing_field = ConditionProjects.find_standardized_field_by_id(field_id)
    if existing_field is None:
        return {"error": "Standardized field not found"}, 404
    
    # validate the updated data
    validation_error, status_code = project_helpers.validate_standardized_field_data(data, project_id, action="update", field_id=field_id)
    if status_code != 200:
        return validation_error, status_code
    
    # update the standardized field
    ConditionProjects.update_standardized_field(field_id, data)
    logger.info(f"Standardized field {field_id} updated for project {project_id}", 
                extra={"username": username})
    
    return {"message": "Standardized field updated successfully"}, 200


def get_standardized_fields_for_project_views(project_id, username, field_type=None):
    """Get all standardized fields for a project, optionally filtered by type"""
    user = UserModel.find_by_username(username)
    if user is None:
        return {"error": "User not found"}, 404
    
    # check project membership
    membership, status_code = project_helpers.check_project_membership(user['progressive_id'], project_id)
    if status_code != 200:
        return membership, status_code
    
    # check that the project exists
    project = ProjectModel.find_by_progressive_id(project_id)
    if project is None:
        return {"error": "Project not found"}, 404
    
    # get standardized fields for the project
    if field_type:
        fields = ConditionProjects.find_standardized_fields_by_project_and_type(project_id, field_type)
    else:
        fields = ConditionProjects.find_standardized_fields_by_project_id(project_id)
    
    if fields is None:
        return {"error": "No standardized fields found"}, 404
    
    fields = list(fields)
    # remove the _id field from each field and add metadata
    for field in fields:
        field.pop("_id")
        # Add usage statistics
        field["usage_count"] = ConditionProjects.count_field_usage_in_experiments(field["progressive_id"])
        field["last_used"] = ConditionProjects.get_field_last_usage(field["progressive_id"])
    
    return fields, 200

def get_standardized_field_by_id_views(field_id, username):
    """Get a specific standardized field by its ID"""
    user = UserModel.find_by_username(username)
    if user is None:
        return {"error": "User not found"}, 404
    
    # get the standardized field
    field = ConditionProjects.find_standardized_field_by_id(field_id)
    if field is None:
        return {"error": "Standardized field not found"}, 404
    
    # check project membership
    membership, status_code = project_helpers.check_project_membership(user['progressive_id'], field['project_id'])
    if status_code != 200:
        return membership, status_code
    
    field.pop("_id")
    # Add usage statistics
    field["usage_count"] = ConditionProjects.count_field_usage_in_experiments(field["progressive_id"])
    field["experiments_using"] = ConditionProjects.get_experiments_using_field(field["progressive_id"])
    
    logger.info(f"Standardized field {field_id} retrieved successfully", extra={"username": username})
    return field, 200


def delete_standardized_field_views(field_id, username):
    """Delete a standardized field (only if not used in any experiments)"""
    user = UserModel.find_by_username(username)
    if user is None:
        return {"error": "User not found"}, 404
    
    # get the standardized field
    field = ConditionProjects.find_standardized_field_by_id(field_id)
    if field is None:
        return {"error": "Standardized field not found"}, 404
    
    # check project ownership (only PI can delete standardized fields)
    ownership, status_code = project_helpers.check_project_ownership(user['progressive_id'], field['project_id'])
    if status_code != 200:
        return ownership, status_code
    
    # check if field is being used in any experiments
    usage_count = ConditionProjects.count_field_usage_in_experiments(field_id)
    if usage_count > 0:
        return {
            "error": "Cannot delete standardized field that is being used in experiments",
            "usage_count": usage_count
        }, 400
    
    # delete the standardized field
    ConditionProjects.delete_standardized_field(field_id)
    logger.info(f"Standardized field {field_id} deleted from project {field['project_id']}", 
                extra={"username": username})
    
    return {"message": "Standardized field deleted successfully"}, 200


def clone_standardized_field_views(field_id, username, target_project_id):
    """Clone a standardized field to another project"""
    user = UserModel.find_by_username(username)
    if user is None:
        return {"error": "User not found"}, 404
    
    # get the source field
    source_field = ConditionProjects.find_standardized_field_by_id(field_id)
    if source_field is None:
        return {"error": "Source standardized field not found"}, 404
    
    # check membership in both projects
    source_membership, status_code = project_helpers.check_project_membership(user['progressive_id'], source_field['project_id'])
    if status_code != 200:
        return source_membership, status_code
    
    target_membership, status_code = project_helpers.check_project_membership(user['progressive_id'], target_project_id)
    if status_code != 200:
        return target_membership, status_code
    
    # prepare data for cloning (remove project-specific fields)
    clone_data = {
        "field_type": source_field["field_type"],
        "field_name": f"{source_field['field_name']} (Copy)",
        "field_description": source_field.get("field_description", ""),
        "field_values": source_field.get("field_values", []),
        "is_required": source_field.get("is_required", False),
        "data_type": source_field["data_type"],
        "validation_rules": source_field.get("validation_rules", {})
    }
    
    # validate the cloned field data
    validation_error, status_code = project_helpers.validate_standardized_field_data(clone_data, target_project_id, action="create")
    if status_code != 200:
        return validation_error, status_code
    
    # create the cloned field
    new_field_id = ConditionProjects.create_standardized_field(clone_data, target_project_id)
    logger.info(f"Standardized field {field_id} cloned to project {target_project_id} as {new_field_id}", 
                extra={"username": username})
    
    return {
        "message": "Standardized field cloned successfully",
        "new_field_id": new_field_id
    }, 201


def bulk_create_standardized_fields_views(fields_data, username, project_id):
    """Create multiple standardized fields at once"""
    user = UserModel.find_by_username(username)
    if user is None:
        return {"error": "User not found"}, 404
    
    # check project membership and permissions
    membership, status_code = project_helpers.check_project_membership(user['progressive_id'], project_id)
    if status_code != 200:
        return membership, status_code
    
    # check that the project exists
    project = ProjectModel.find_by_progressive_id(project_id)
    if project is None:
        return {"error": "Project not found"}, 404
    
    # validate all fields data
    validation_errors = []
    for i, field_data in enumerate(fields_data):
        validation_error, status_code = project_helpers.validate_standardized_field_data(field_data, project_id, action="create")
        if status_code != 200:
            validation_errors.append(f"Field {i+1}: {validation_error['error']}")
    
    if validation_errors:
        return {"error": "Validation failed", "details": validation_errors}, 400
    
    # create all fields
    try:
        field_ids = ConditionProjects.bulk_create_standardized_fields(fields_data, project_id)
        logger.info(f"Bulk created {len(field_ids)} standardized fields for project {project_id}", 
                    extra={"username": username})
        
        return {
            "message": f"Successfully created {len(field_ids)} standardized fields",
            "field_ids": field_ids
        }, 201
    except Exception as e:
        logger.error(f"Error in bulk creating standardized fields: {str(e)}", extra={"username": username})
        return {"error": "Failed to create standardized fields"}, 500


def get_standardized_field_statistics_views(project_id, username):
    """Get statistics about standardized fields usage in a project"""
    user = UserModel.find_by_username(username)
    if user is None:
        return {"error": "User not found"}, 404
    
    # check project membership
    membership, status_code = project_helpers.check_project_membership(user['progressive_id'], project_id)
    if status_code != 200:
        return membership, status_code
    
    # check that the project exists
    project = ProjectModel.find_by_progressive_id(project_id)
    if project is None:
        return {"error": "Project not found"}, 404
    
    try:
        statistics = ConditionProjects.get_field_statistics(project_id)
        
        # Calculate summary statistics
        total_fields = len(statistics)
        required_fields = sum(1 for field in statistics if field.get('is_required', False))
        used_fields = sum(1 for field in statistics if field.get('usage_count', 0) > 0)
        
        summary = {
            "total_fields": total_fields,
            "required_fields": required_fields,
            "used_fields": used_fields,
            "unused_fields": total_fields - used_fields,
            "usage_rate": (used_fields / total_fields * 100) if total_fields > 0 else 0
        }
        
        return {
            "summary": summary,
            "field_details": statistics
        }, 200
        
    except Exception as e:
        logger.error(f"Error getting standardized field statistics: {str(e)}", extra={"username": username})
        return {"error": "Failed to retrieve statistics"}, 500


def validate_experiment_against_standardized_fields_views(experiment_data, project_id, username):
    """Validate experiment data against project's standardized fields"""
    user = UserModel.find_by_username(username)
    if user is None:
        return {"error": "User not found"}, 404
    
    # check project membership
    membership, status_code = project_helpers.check_project_membership(user['progressive_id'], project_id)
    if status_code != 200:
        return membership, status_code
    
    try:
        validation_errors = project_helpers.validate_experiment_data_against_standardized_fields(experiment_data, project_id)
        
        if validation_errors:
            return {
                "valid": False,
                "errors": validation_errors
            }, 400
        
        return {
            "valid": True,
            "message": "Experiment data is valid against standardized fields"
        }, 200
        
    except Exception as e:
        logger.error(f"Error validating experiment data: {str(e)}", extra={"username": username})
        return {"error": "Failed to validate experiment data"}, 500


# Legacy functions for backward compatibility
def create_conditions_for_project_views(data, username, project_id):
    """Legacy function - use create_standardized_field_for_project_views instead"""
    # Convert old condition format to new standardized field format
    standardized_data = {
        "field_type": "condition",
        "field_name": data.get("name", "Condition"),
        "field_description": data.get("description", ""),
        "field_values": data.get("values", []),
        "is_required": data.get("required", False),
        "data_type": data.get("type", "text"),
        "validation_rules": data.get("validation", {})
    }
    
    return create_standardized_field_for_project_views(standardized_data, username, project_id)


def update_conditions_for_project_views(data, username, project_id):
    """Legacy function - deprecated in favor of individual field updates"""
    user = UserModel.find_by_username(username)
    if user is None:
        return {"error": "User not found"}, 404
    
    # check that the project exists
    project = ProjectModel.find_by_progressive_id(project_id)
    if project is None:
        return {"error": "Project not found"}, 404
    
    # This function is deprecated - return appropriate message
    return {
        "message": "This function is deprecated. Please use update_standardized_field_for_project_views for individual field updates."
    }, 200


def get_conditions_for_project_views(project_id, username):
    """Legacy function - use get_standardized_fields_for_project_views instead"""
    return get_standardized_fields_for_project_views(project_id, username, field_type="condition")


def get_condition_by_progressive_id_views(progressive_id, username):
    """Legacy function - use get_standardized_field_by_id_views instead"""
    return get_standardized_field_by_id_views(progressive_id, username)