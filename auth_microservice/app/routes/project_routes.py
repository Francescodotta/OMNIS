from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity 
from app import app
import app.helpers.project_helpers as project_helpers
import app.views.project_views as project_views
from app.models.auth_models import UserModel
from app import blacklist


bp = Blueprint('project', __name__)


@app.route('/api/project', methods=['POST'])
@jwt_required()
def create_project():
    result, status_code = project_views.create_project_views(request.json, get_jwt()["sub"])
    return jsonify(result), status_code


@bp.route('/api/project/<int:progressive_id>', methods=['GET'])
@jwt_required()
def get_project_by_progressive_id(progressive_id):
    username = get_jwt()["sub"]
    project, status_code = project_views.get_project_by_id_views(progressive_id, username)
    return project, status_code

@bp.route('/api/project/<int:progressive_id>', methods=['PUT'])
@jwt_required()
def update_project_by_progressive_id(progressive_id):
    username = get_jwt_identity()
    result, status_code = project_views.update_project_by_id_views(progressive_id, request.json, username)
    return jsonify(result), status_code

## add that only the PI of the project can remove it
@bp.route('/api/project/<int:progressive_id>', methods=['DELETE'])
@jwt_required()
def delete_project_by_progressive_id(progressive_id):
    user = get_jwt()["sub"]
    result, status_code = project_views.delete_project_by_progressive_id_views(progressive_id, user)
    return jsonify(result), status_code


#create the membership of a user to a project
@bp.route('/api/v1/project/<int:project_id>/members', methods=['POST'])
@jwt_required()
def create_membership(project_id):
    username = get_jwt()["sub"]
    result, status_code = project_views.create_member_views(request.json, username, project_id)
    print(result)
    return jsonify(result), status_code

@bp.route('/api/project/membership/<int:member_id>', methods=['GET'])
@jwt_required()
def get_member_by_id(member_id):
    username = get_jwt()["sub"]
    member, status_code = project_views.get_member_by_id_views(member_id, username)
    return member, status_code

@bp.route('/api/project/membership/<int:member_id>', methods=['PUT'])
@jwt_required()
def update_member_by_id(member_id):
    result, status_code = project_views.update_member_by_id_views(member_id, request.json)
    return jsonify(result), status_code

@bp.route('/api/project/membership/<int:member_id>', methods=['DELETE'])
@jwt_required()
def delete_member_by_id(member_id):
    username = get_jwt()["sub"]
    result, status_code = project_views.delete_member_by_id_views(member_id, username)
    return jsonify(result), status_code

@bp.route('/api/project/<int:project_id>/membership', methods=['GET'])
@jwt_required()
def get_members_by_project_id(project_id):
    username = get_jwt()["sub"]
    members, status_code = project_views.get_members_for_project_views(project_id, username)
    return members, status_code

# get all the projects of a user
@bp.route('/api/project/user', methods=['GET'])
@jwt_required()
def get_projects_for_user():
    user = get_jwt()
    projects, status_code = project_views.get_projects_for_user_views(user['sub'])
    return projects, status_code

## ottieni tutti i non-membri di un progetto
@bp.route('/api/project/<int:project_id>/nonmembers', methods=['GET'])
@jwt_required()
def get_nonmembers_for_project(project_id):
    username = get_jwt_identity()
    nonmembers, status_code = project_views.get_nonmembers_for_project_views(project_id, username)
    return nonmembers, status_code

# STANDARDIZED FIELDS ROUTES

# Create a standardized field for a project
@bp.route('/api/projects/<int:project_id>/standardized-fields', methods=['POST'])
@jwt_required()
def create_standardized_field_for_project(project_id):
    username = get_jwt()["sub"]
    result, status_code = project_views.create_standardized_field_for_project_views(request.json, username, project_id)
    return jsonify(result), status_code

# Get all standardized fields for a project (with optional field_type filter)
@bp.route('/api/projects/<int:project_id>/standardized-fields', methods=['GET'])
@jwt_required()
def get_standardized_fields_for_project(project_id):
    username = get_jwt()["sub"]
    field_type = request.args.get('field_type')  # Optional query parameter
    fields, status_code = project_views.get_standardized_fields_for_project_views(project_id, username, field_type)
    return jsonify(fields), status_code

# Get a specific standardized field by ID
@bp.route('/api/projects/<int:project_id>/standardized-fields/<int:field_id>', methods=['GET'])
@jwt_required()
def get_standardized_field_by_id(project_id, field_id):
    username = get_jwt()["sub"]
    field, status_code = project_views.get_standardized_field_by_id_views(field_id, username)
    return jsonify(field), status_code

# Update a standardized field
@bp.route('/api/projects/<int:project_id>/standardized-fields/<int:field_id>', methods=['PUT'])
@jwt_required()
def update_standardized_field_for_project(project_id, field_id):
    username = get_jwt()["sub"]
    result, status_code = project_views.update_standardized_field_for_project_views(field_id, request.json, username, project_id)
    return jsonify(result), status_code

# Delete a standardized field
@bp.route('/api/projects/<int:project_id>/standardized-fields/<int:field_id>', methods=['DELETE'])
@jwt_required()
def delete_standardized_field(project_id, field_id):
    username = get_jwt()["sub"]
    result, status_code = project_views.delete_standardized_field_views(field_id, username)
    return jsonify(result), status_code

# Clone a standardized field to the same or different project
@bp.route('/api/projects/<int:project_id>/standardized-fields/<int:field_id>/clone', methods=['POST'])
@jwt_required()
def clone_standardized_field(project_id, field_id):
    username = get_jwt()["sub"]
    target_project_id = request.json.get('target_project_id', project_id)
    result, status_code = project_views.clone_standardized_field_views(field_id, username, target_project_id)
    return jsonify(result), status_code

# Bulk create standardized fields
@bp.route('/api/projects/<int:project_id>/standardized-fields/bulk', methods=['POST'])
@jwt_required()
def bulk_create_standardized_fields(project_id):
    username = get_jwt()["sub"]
    fields_data = request.json.get('fields', [])
    result, status_code = project_views.bulk_create_standardized_fields_views(fields_data, username, project_id)
    return jsonify(result), status_code

# Get standardized field statistics for a project
@bp.route('/api/projects/<int:project_id>/standardized-fields/statistics', methods=['GET'])
@jwt_required()
def get_standardized_field_statistics(project_id):
    username = get_jwt()["sub"]
    statistics, status_code = project_views.get_standardized_field_statistics_views(project_id, username)
    return jsonify(statistics), status_code

# Export standardized fields configuration
@bp.route('/api/projects/<int:project_id>/standardized-fields/export', methods=['GET'])
@jwt_required()
def export_standardized_fields(project_id):
    username = get_jwt()["sub"]
    try:
        # Check project membership first
        membership, status_code = project_views.get_standardized_fields_for_project_views(project_id, username)
        if status_code != 200:
            return jsonify({"error": "Access denied"}), status_code
        
        # Export the configuration
        export_data = project_helpers.export_standardized_fields_config(project_id)
        return jsonify(export_data), 200
    except Exception as e:
        return jsonify({"error": "Export failed"}), 500

# Import standardized fields configuration
@bp.route('/api/projects/<int:project_id>/standardized-fields/import', methods=['POST'])
@jwt_required()
def import_standardized_fields(project_id):
    username = get_jwt()["sub"]
    try:
        # Check if user has permission (should be PI)
        user = UserModel.find_by_username(username)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        ownership, status_code = project_helpers.check_project_ownership(user['progressive_id'], project_id)
        if status_code != 200:
            return jsonify({"error": "Only project PI can import fields"}), 403
        
        config_data = request.json
        result, status_code = project_helpers.import_standardized_fields_config(config_data, project_id)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": "Import failed"}), 500

# Validate experiment data against standardized fields
@bp.route('/api/projects/<int:project_id>/standardized-fields/validate', methods=['POST'])
@jwt_required()
def validate_experiment_against_fields(project_id):
    username = get_jwt()["sub"]
    experiment_data = request.json.get('experiment_data', {})
    result, status_code = project_views.validate_experiment_against_standardized_fields_views(experiment_data, project_id, username)
    return jsonify(result), status_code

# Get field template for a specific field type
@bp.route('/api/standardized-fields/template/<field_type>', methods=['GET'])
@jwt_required()
def get_field_template(field_type):
    try:
        template = project_helpers.generate_field_template(field_type)
        return jsonify(template), 200
    except Exception as e:
        return jsonify({"error": "Failed to generate template"}), 500

# Check field usage safety before modification/deletion
@bp.route('/api/projects/<int:project_id>/standardized-fields/<int:field_id>/usage-check', methods=['GET'])
@jwt_required()
def check_field_usage_safety(project_id, field_id):
    username = get_jwt()["sub"]
    try:
        # Check project membership
        user = UserModel.find_by_username(username)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        membership, status_code = project_helpers.check_project_membership(user['progressive_id'], project_id)
        if status_code != 200:
            return jsonify({"error": "Access denied"}), status_code
        
        safety_check, status_code = project_helpers.check_field_usage_safety(field_id)
        return jsonify(safety_check), status_code
    except Exception as e:
        return jsonify({"error": "Safety check failed"}), 500

# LEGACY ROUTES (Updated to use new standardized fields system)

# Update the existing condition routes to use new system
@bp.route('/api/project/<int:project_id>/conditions', methods=['POST'])
@jwt_required()
def create_condition_for_project_legacy(project_id):
    """Legacy route - redirects to standardized fields"""
    username = get_jwt()["sub"]
    result, status_code = project_views.create_conditions_for_project_views(request.json, username, project_id)
    return jsonify(result), status_code

@bp.route('/api/project/<int:project_id>/conditions', methods=['GET'])
@jwt_required()
def get_conditions_for_project_legacy(project_id):
    """Legacy route - redirects to standardized fields"""
    username = get_jwt()["sub"]
    conditions, status_code = project_views.get_conditions_for_project_views(project_id, username)
    return jsonify(conditions), status_code

@bp.route('/api/project/condition/<int:progressive_id>', methods=['GET'])
@jwt_required()
def get_condition_by_progressive_id_legacy(progressive_id):
    """Legacy route - redirects to standardized fields"""
    username = get_jwt()["sub"]
    condition, status_code = project_views.get_condition_by_progressive_id_views(progressive_id, username)
    return jsonify(condition), status_code

@bp.route('/api/project/condition/<int:progressive_id>', methods=['PUT'])
@jwt_required()
def update_condition_for_project_legacy(progressive_id):
    """Legacy route - redirects to standardized fields"""
    username = get_jwt()["sub"]
    result, status_code = project_views.update_conditions_for_project_views(request.json, username, progressive_id)
    return jsonify(result), status_code
