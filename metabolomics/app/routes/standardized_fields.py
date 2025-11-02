from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.metabolomics_models import MetabolomicsModel, StandardizedFieldHelper
from app.helpers import metabolomics_helpers
import json


bp = Blueprint('standardized_fields', __name__)

# ========== STANDARDIZED FIELDS ASSIGNMENT ROUTES ==========

@bp.route('/api/v1/project/<project_id>/experiments/<experiment_id>/standardized_fields', methods=['POST'])
@jwt_required()
def assign_standardized_fields(project_id, experiment_id):
    """
    Assign standardized field values to a metabolomics experiment
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'field_assignments' not in data:
            return jsonify({"error": "field_assignments required"}), 400
        
        field_assignments = data['field_assignments']
        
        # Check if experiment exists and belongs to project
        experiment = MetabolomicsModel.find_by_progressive_id(int(experiment_id))
        if not experiment:
            return jsonify({"error": "Experiment not found"}), 404
        
        if experiment['project_id'] != project_id:
            return jsonify({"error": "Experiment does not belong to this project"}), 403
        
        # Validate each field assignment
        validation_errors = []
        for field_name, field_value in field_assignments.items():
            is_valid, error_msg = MetabolomicsModel.validate_field_assignment(
                project_id, field_name, field_value
            )
            if not is_valid:
                validation_errors.append(f"{field_name}: {error_msg}")
        
        if validation_errors:
            return jsonify({
                "error": "Validation failed",
                "details": validation_errors
            }), 400
        
        # Assign the standardized fields
        result = MetabolomicsModel.assign_standardized_fields(
            int(experiment_id), field_assignments
        )
        
        if result.modified_count > 0:
            return jsonify({
                "message": "Standardized fields assigned successfully",
                "experiment_id": experiment_id,
                "assigned_fields": field_assignments
            }), 200
        else:
            return jsonify({"error": "Failed to assign standardized fields"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# ========== FIELD DEFINITIONS ROUTES ==========

@bp.route('/api/v1/project/<project_id>/standardized_fields/definitions', methods=['GET'])
@jwt_required()
def get_project_standardized_fields(project_id):
    """
    Get standardized field definitions for a project
    """
    try:
        user_id = get_jwt_identity()
        field_type = request.args.get('field_type', None)
        
        standardized_fields = StandardizedFieldHelper.get_project_standardized_fields(
            project_id, field_type
        )
        
        # Remove MongoDB ObjectId
        for field in standardized_fields:
            field.pop('_id', None)
        
        return jsonify({
            "project_id": project_id,
            "field_type": field_type or "all",
            "standardized_fields": standardized_fields,
            "total_count": len(standardized_fields)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@bp.route('/api/v1/project/<project_id>/standardized_fields/validate', methods=['POST'])
@jwt_required()
def validate_field_assignment_endpoint(project_id):
    """
    Validate a field assignment against project standardized field definitions
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'field_name' not in data or 'field_value' not in data:
            return jsonify({"error": "field_name and field_value required"}), 400
        
        field_name = data['field_name']
        field_value = data['field_value']
        
        is_valid, error_msg = MetabolomicsModel.validate_field_assignment(
            project_id, field_name, field_value
        )
        
        return jsonify({
            "project_id": project_id,
            "field_name": field_name,
            "field_value": field_value,
            "is_valid": is_valid,
            "message": error_msg if not is_valid else "Valid",
            "status": "valid" if is_valid else "invalid"
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


