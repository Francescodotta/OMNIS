import os
import flowkit as fk
from flask import Blueprint, request, jsonify
from app.models import flow_cytometry as fc
from app.models import gating as gt
from app.helpers import flow_cytometry_helpers as fch
from app.utils import gating as g_utils
from app.utils import security as sec
import pandas as pd
import numpy as np
from datetime import datetime
import json

from app.utils.gating_hierarchy import add_gate_to_hierarchy, find_gate_by_id, build_session_from_hierarchy, build_session_from_hierarchy_v2


FLOW_CYTOMETRY_SAVE_PATH = os.getenv("FLOW_CYTOMETRY_SAVE_PATH")

# function to render the gating view page, without the parent id 
def get_fcs_gating_view_by_progressive_id(username, project_id, flow_cytometry_id):
    
    # check the project
    response, status_code = sec.check_permission(username, project_id)
    if status_code != 200:
        return response, status_code
    
    flow_cyto = fc.FlowCytometryModel.find_by_progressive_id(flow_cytometry_id)
    if flow_cyto is None:
        return jsonify({"error": "Flow cytometry data not found"}), 404
    
    flow_cyto.pop("_id")
    if "workspace_id" in flow_cyto:
        flow_cyto.pop("workspace_id")
    
    flow_cyto_decrypted = fch.decrypt_flow_cytometry_data(flow_cyto)
    df = g_utils.read_fcs_data(os.path.join(FLOW_CYTOMETRY_SAVE_PATH, flow_cyto_decrypted["file_path"]))

    # Convert DataFrame columns to native Python objects
    # Example: replace NaN with None, ensure Numeric types become float/int, etc.
    df = df.where(pd.notnull(df), None)
    for col in df.select_dtypes(include=[np.number]).columns:
        # Convert numeric columns to Python float (or int if you prefer)
        df[col] = df[col].apply(lambda x: float(x) if x is not None else None)
    for col in df.select_dtypes(include=[np.datetime64]).columns:
        # Convert datetime columns to string
        df[col] = df[col].apply(lambda x: x.isoformat() if x is not None else None)

    # Use only the first level of the columns
    df.columns = df.columns.get_level_values(0)
        
    if len(df)> 30000:
        # reduce randomly the len of the dataframe
        df = df.sample(n=30000)
    
    df_dict = df.to_dict(orient='records')
    return jsonify({"data": df_dict}), 200




#### CRUD OPERATIONS FOR GATING STRATEGY ####

# Function to create a new gating strategy
def create_gating_strategy_views(username, project_id, flow_cytometry_id, data):
    """
    Function that handles the creation of a new gating strategy.
    
    The create gating strategy view is called when the user wants to create a new gating strategy for a specific flow cytometry object.
    The user must provide the name and the description of the gating strategy.
    The gating strategy will be created with the first gate element in the strategy.
    
    The structure of the data is the following:
    {
        "name": "gating_strategy_name",
        "description": "gating_strategy_description"
    }
    
    The response will be a success message if the gating strategy is created successfully.
    The response will be an error message if the project does not exist, the user does not exist, the user does not have permissions for the project, the flow cytometry object does not exist, the data is missing or the gating strategy is not created successfully.
    """
    
    try:
        # the project must exist
        response, status_code = sec.check_permission(username, project_id)
        if status_code != 200:
            return response, status_code
        
        # the flow cytometry object must exist
        flow_cytometry_object = fc.FlowCytometryModel.find_by_progressive_id(flow_cytometry_id)
        if flow_cytometry_object is None:
            return jsonify({"error": "Flow cytometry object not found"}), 404
        
        # check that the flow cytometry object is associated with the project
        if flow_cytometry_object["project_id"] != project_id:
            return jsonify({"error": "Flow cytometry object not associated with project"}), 404
        
        # check that there is no duplicate gating strategy name associated with the flow cytometry object
        if gt.GateStrategyModel.get_gate_strategy_by_flow_cytometry_id_and_name(flow_cytometry_id, data["name"]) is not None:
            return jsonify({"error": "Duplicate gating strategy name for the flow cytometry object"}), 400
        
        # the data must contain the required fields
        required_fields = ["name", "description"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # generate the progressive id for the gating strategy
        gating_strategy_id = gt.GateStrategyModel.get_next_sequence()
        
        # created and updated added in the gating strategy model
        data["created_at"] = datetime.now()
        data["updated_at"] = datetime.now()
        
        # set the gml path , for the moment to not use the gml file 
        gml_path = os.path.join(FLOW_CYTOMETRY_SAVE_PATH, f"{data['name']}.gml")
        
        # create the gating strategy
        gating_strategy_data = {
            "progressive_id": gating_strategy_id,
            "name": data["name"],
            "description": data["description"],
            "project_id": project_id,
            "flow_cytometry_id": flow_cytometry_id,
            "created_by": username,
            "last_modified_by": username,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        # get the next sequence for the gating strategy
        next_sequence = gt.GateStrategyModel.get_next_sequence()
        
        # create the gating strategy
        gating_strategy_data["progressive_id"] = next_sequence
        
        # save the gating strategy to the database
        gt.GateStrategyModel.create_gate_strategy(gating_strategy_data)
        
        # the gml file will be created with the first gate element in the strategy
        # return the success message
        return jsonify({"message": "Gating strategy created successfully"}), 201
    
    except Exception as e:
        print(f"Error in create_gating_strategy_views: {str(e)}")
        return jsonify({"error": str(e)}), 500


# function to get all the gating strategies for a specific flow cytometry object
def get_all_gating_strategies_for_flow_cytometry(username, project_id, flow_cytometry_id):
    """
    This function handles the retrieval of all the gating strategies that are associated with a specific flow cytometry object.
    The response will be a list of gating strategies.
    The response will be an error message if the project does not exist, the user does not exist, the user does not have permissions for the project, the flow cytometry object does not exist or the gating strategies are not found.
    """
    
    try:
        # check that the project exists
        response, status_code = sec.check_permission(username, project_id)
        if status_code != 200:
            return response, status_code
    
    
        # check that the flow cytometry object exists
        flow_cytometry_object = fc.FlowCytometryModel.find_by_progressive_id(flow_cytometry_id)
        if flow_cytometry_object is None:
            return jsonify({"error": "Flow cytometry object not found"}), 404
        
        # retrieve all the gating strategies for the flow cytometry object
        gating_strategies = gt.GateStrategyModel.get_gate_strategy_by_flow_cytometry_id(flow_cytometry_id)
        
        # if there are no gating strategies, return an empty list
        if gating_strategies is None:
            return jsonify({"gating_strategies": []}), 200
        
        # list of gating strategies
        gating_strategies = list(gating_strategies)
        
        # pop the _id from each gating strategy
        for gating_strategy in gating_strategies:
            gating_strategy.pop("_id")
        
        # return the gating strategies
        return jsonify({"data": gating_strategies}), 200
    
    except Exception as e:
        print(f"Error in get_all_gating_strategies_for_flow_cytometry: {str(e)}")
        return jsonify({"error": str(e)}), 500


# get gating strategy by progressive id
def get_gating_strategy_by_progressive_id(username, project_id, flow_cytometry_id, gating_strategy_id):
    """
    This function handles the retrieval of a gating strategy by its progressive id.
    """
    try:
        # check that the project exists
        response, status_code = sec.check_permission(username, project_id)
        if status_code != 200:
            return response, status_code
        
        # retrieve the gating strategy
        gating_strategy = gt.GateStrategyModel.get_gate_strategy_by_progressive_id(int(gating_strategy_id))
        # pop the _id from the gating strategy
        gating_strategy.pop("_id")
        
        # check that the gating strategy is associated with the flow cytometry object
        if gating_strategy["flow_cytometry_id"] != flow_cytometry_id:
            return jsonify({"error": "Gating strategy not associated with flow cytometry object"}), 404
        
        # return the gating strategy
        return jsonify({"data": gating_strategy}), 200
    
    except Exception as e:
        print(f"Error in get_gating_strategy_by_progressive_id: {str(e)}")
        return jsonify({"error": str(e)}), 500



# function to update a gating strategy
def update_gating_strategy(username, project_id, flow_cytometry_id, gating_strategy_id, data):
    """
    Function that handles the update of a gating strategy.
    """
    try:
        # do all the checks
        response, status_code = sec.check_permission(username, project_id)
        if status_code != 200:
            return response, status_code
        
        # retrieve the flow cytometry object
        flow_cytometry_object = fc.FlowCytometryModel.find_by_progressive_id(flow_cytometry_id)
        if flow_cytometry_object is None:
            return jsonify({"error": "Flow cytometry object not found"}), 404
        
        # get the old gml file name
        old_gml_file_name = gt.GateStrategyModel.get_gate_strategy_by_progressive_id(gating_strategy_id)["gating_strategy_name"]
        
        # only the name and the description can be updated
        if "gating_strategy_name" in data:
            gt.GateStrategyModel.update_gate_strategy_by_id(gating_strategy_id, {"gating_strategy_name": data["gating_strategy_name"]})
        
        if "gating_strategy_description" in data:
            gt.GateStrategyModel.update_gate_strategy_by_id(gating_strategy_id, {"gating_strategy_description": data["gating_strategy_description"]})
        
        # rename the old gml file with the new name
        os.rename(os.path.join(FLOW_CYTOMETRY_SAVE_PATH, f"{old_gml_file_name}.gml"), os.path.join(FLOW_CYTOMETRY_SAVE_PATH, f"{data['gating_strategy_name']}.gml"))
        
        # return the success message
        return jsonify({"message": "Gating strategy updated successfully"}), 200
    
    except Exception as e:
        print(f"Error in update_gating_strategy: {str(e)}")
        return jsonify({"error": str(e)}), 500



# function to delete a gating strategy
def delete_gating_strategy(username, project_id, flow_cytometry_id, gating_strategy_id):
    """
    Function that handles the deletion of a gating strategy.
    """
    try:
        # do all the checks
        response, status_code = sec.check_permission(username, project_id)
        if status_code != 200:
            return response, status_code
        
        # retrieve the flow cytometry object
        print(gating_strategy_id)
        flow_cytometry_object = fc.FlowCytometryModel.find_by_progressive_id(flow_cytometry_id)
        if flow_cytometry_object is None:
            return jsonify({"error": "Flow cytometry object not found"}), 404
        
        # retrieve the gating strategy
        gating_strategy = gt.GateStrategyModel.get_gate_strategy_by_progressive_id(int(gating_strategy_id))
        if gating_strategy is None:
            return jsonify({"error": "Gating strategy not found"}), 404

        # check that the gating strategy is associated with the flow cytometry object
        print(gating_strategy)
        if gating_strategy["flow_cytometry_id"] != flow_cytometry_id:
            return jsonify({"error": "Gating strategy not associated with flow cytometry object"}), 404
        
        # check that the gml path is present in the gating strategy
        if gating_strategy["name"] is None:
            return jsonify({"error": "Gating strategy name not found"}), 404
                
        # delete the gating strategy from the database
        gt.GateStrategyModel.delete_gate_strategy_by_progressive_id(gating_strategy_id)
        
        # return the success message
        return jsonify({"message": "Gating strategy deleted successfully"}), 200
    
    except Exception as e:
        print(f"Error in delete_gating_strategy: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    
    
## CRUD OPERATIONS FOR GATING ELEMENTS ##

# Add this at the top of the file with your other constants
def get_gml_path(project_id, gating_strategy_id, filename):
    """Helper function to generate the GML file path and create directories if needed"""
    try:
        # Define the paths
        base_path = os.path.join(FLOW_CYTOMETRY_SAVE_PATH, "gating")  # Add "gating" subdirectory
        project_path = os.path.join(base_path, str(project_id))
        strategy_path = os.path.join(project_path, str(gating_strategy_id))
        
        # Create each directory level if it doesn't exist
        os.makedirs(base_path, exist_ok=True)  # Create gating directory
        os.makedirs(project_path, exist_ok=True)  # Create project directory
        os.makedirs(strategy_path, exist_ok=True)  # Create strategy directory
        
        # Return the full path to the GML file
        full_path = os.path.join(strategy_path, f"{filename}.gml")
        print(f"Created GML path: {full_path}")  # Debug print
        
        return full_path
        
    except Exception as e:
        print(f"Error creating directories: {str(e)}")
        raise Exception(f"Failed to create directory structure: {str(e)}")

# function to create a new gating element
def create_gating_element_views(username, project_id, flow_cytometry_id, gating_strategy_id, data):
    """
    Create a new gating element with FlowKit transformations
    """
    try:
        response, status_code = sec.check_permission(username, project_id)
        if status_code != 200:
            return response, status_code

        # retrieve the flow cytometry object
        flow_cytometry_object = fc.FlowCytometryModel.find_by_progressive_id(flow_cytometry_id)
        if flow_cytometry_object is None:
            return jsonify({"error": "Flow cytometry object not found"}), 404
        
        # retrieve the gating strategy
        gating_strategy = gt.GateStrategyModel.get_gate_strategy_by_progressive_id(int(gating_strategy_id))
        if gating_strategy is None:
            return jsonify({"error": "Gating strategy not found"}), 404
        
        # check that the gating strategy is associated with the flow cytometry object
        if gating_strategy["flow_cytometry_id"] != flow_cytometry_id:
            return jsonify({"error": "Gating strategy not associated with flow cytometry object"}), 404
        
        # check that the name is present
        if "name" not in data:
            return jsonify({"error": "Name not found"}), 400
        
        # check that the vertices are present
        if "vertices" not in data:
            return jsonify({"error": "Vertices not found"}), 400
        
        # check that the columns are present
        if "columns" not in data:
            return jsonify({"error": "Columns not found"}), 400
        
        # Initialize variables
        gating_strategy_name = gating_strategy["name"]
        parent_id = data.get("parentId")
        name = data["name"]
        
        # Extract transformation information
        columns = data.get("columns", {})
        x_column = columns.get("xColumn")
        y_column = columns.get("yColumn")

        # Process X and Y transformations
        transform_id_x, x_transformation = g_utils.process_transformation(
            columns.get("xTransformation"), 
            x_column
        )
        transform_id_y, y_transformation = g_utils.process_transformation(
            columns.get("yTransformation"), 
            y_column
        )
        
        
        
        print(columns.get("yTransformation"))
        
        # Create dimensions 
        x_channel = fk.Dimension(
            x_column,
            compensation_ref="uncompensated"
        )
        y_channel = fk.Dimension(
            y_column,
            compensation_ref="uncompensated"
        )

        # Convert vertices
        vertices = [(float(v['x']), float(v['y'])) for v in data["vertices"]]

        # Get the proper GML file path
        gml_path = get_gml_path(project_id, gating_strategy_id, gating_strategy_name)

        # Create the new gate with transformation support
        new_gate = fk.gates.PolygonGate(
            name,
            dimensions=[x_channel, y_channel],
            vertices=vertices
        )

        # Load or create the gating strategy
        if os.path.exists(gml_path):
            print(f"Loading existing GML file: {gml_path}")
            try:
                gating_strategy_obj = fk.parse_gating_xml(gml_path)
            except Exception as e:
                print(f"Error loading existing GML file: {str(e)}")
                return jsonify({"error": f"Error loading existing gating strategy: {str(e)}"}), 500
        else:
            print("Creating new gating strategy")
            gating_strategy_obj = fk.GatingStrategy()

        # Add the new gate to the strategy
        try:
            gating_strategy_obj.add_gate(new_gate, gate_path=("root",))
            

        except Exception as e:
            print(f"Error adding gate to strategy: {str(e)}")
            return jsonify({"error": f"Error adding gate to strategy: {str(e)}"}), 500

        print(f"Saving gating strategy to: {gml_path}")

        # Save the GML file
        try:
            fk.export_gatingml(
                gating_strategy_obj, 
                gml_path, 
                sample_id=flow_cytometry_id,
            )
        except Exception as e:
            print(f"Error saving GML file: {str(e)}")
            return jsonify({"error": f"Error saving gating strategy: {str(e)}"}), 500

        # Update the gating strategy in the database with the new path
        gt.GateStrategyModel.update_gate_strategy_by_id(
            int(gating_strategy_id), 
            {"gml_path": gml_path}
        )

        # Update the gating element data to include detailed transformation information
        gating_element_data = {
            "name": name,
            "vertices": vertices,
            "columns": {
                "xColumn": x_column,
                "yColumn": y_column,
                "xTransformation": columns.get("xTransformation"),
                "yTransformation": columns.get("yTransformation")
            },
            "parent_id": parent_id,
            "gating_strategy_id": gating_strategy_id,
            "flow_cytometry_id": flow_cytometry_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "created_by": username,
            "last_modified_by": username
        }
        
        # Create the gating element in the database
        gt.GatingElementModel.create_gating_element(gating_element_data)
        
        
        
        return jsonify({
            "message": "Gating element created successfully",
        }), 201

    except Exception as e:
        print(f"Error in create_gating_element_views: {str(e)}")
        return jsonify({"error": str(e)}), 500

# function to create a new gating element using the Session class
def create_gating_element_views_v2(username, project_id, flow_cytometry_id, gating_strategy_id, data):
    ## CHECK PART
    try:
        response, status_code = sec.check_permission(username, project_id)
        if status_code != 200:
            return response, status_code

        # Retrieve the flow cytometry object.
        flow_cytometry_object = fc.FlowCytometryModel.find_by_progressive_id(flow_cytometry_id)
        if flow_cytometry_object is None:
            return jsonify({"error": "Flow cytometry object not found"}), 404

        # Retrieve the gating strategy.
        gating_strategy = gt.GateStrategyModel.get_gate_strategy_by_progressive_id(int(gating_strategy_id))
        if gating_strategy is None:
            return jsonify({"error": "Gating strategy not found"}), 404

        # Check that the gating strategy is associated with the flow cytometry object.
        if gating_strategy["flow_cytometry_id"] != flow_cytometry_id:
            return jsonify({"error": "Gating strategy not associated with flow cytometry object"}), 404

        # Validate required fields.
        if "name" not in data:
            return jsonify({"error": "Name not found"}), 400
        if "vertices" not in data:
            return jsonify({"error": "Vertices not found"}), 400
        if "columns" not in data:
            return jsonify({"error": "Columns not found"}), 400
    except Exception as e:
        print(f"Error in create_gating_element_views_v2: {str(e)}")
        return jsonify({"error": str(e)}), 500

    ## FLOW CYTOMETRY PART: UPDATE THE JSON HIERARCHY AND REBUILD THE SESSION
    try:
        # Basic variables.
        gating_strategy_name = gating_strategy["name"]
        parent_id = data.get("parentId")  # May be None, indicating a top-level gate.
        name = data["name"]

        # Determine the JSON hierarchy file path.
        # (We derive a path from the project and gating strategy; adjust as needed.)
        gml_path = get_gml_path(project_id, gating_strategy_id, gating_strategy_name)
        json_hierarchy_path = gml_path.replace(".gml", ".json")

        # Decrypt and extract the file path of the flow cytometry sample.
        file_path = sec.decrypt_data(flow_cytometry_object["file_path"])
        sample_id = sec.decrypt_data(flow_cytometry_object["filename"])  # Not used here but available if needed

        # Define transformation parameters from the provided columns.
        columns = data.get("columns", {})
        x_column = columns.get("xColumn")
        y_column = columns.get("yColumn")
        x_transformation = columns.get("xTransformation")
        y_transformation = columns.get("yTransformation")
        
        

        # Convert vertices (strings) to floats.
        vertices = [(float(v['x']), float(v['y'])) for v in data["vertices"]]
        # if the transformation is log 
        ## apply transformation to only the x value
        if x_transformation.get("type") == "log":
            print(x_transformation)
            decades_x = x_transformation.get("params").get("decades")
            offset_x = x_transformation.get("params").get("offset")
            print("\n\n\n\n original vertices: \n\n\n\n\n", vertices)
            # Restore only x-values
            vertices = [
                (g_utils.inverse_log_transform(vx, offset_x, decades_x), vy)
                for vx, vy in vertices
            ]
            print("restored_vertices: \n\n\n")
            print(vertices)
            
        if x_transformation.get("type") == "biexponential":
            print(x_transformation)
            negative_x = x_transformation.get("params").get("negative")
            width_x = x_transformation.get("params").get("width")
            positive_x = x_transformation.get("params").get("positive")
            max_value_x = x_transformation.get("params").get("max_value")
            print("\n\n\n\n original vertices: \n\n\n\n\n", vertices)
            # Restore only x-values
            vertices = [
                (g_utils.inverse_biexponential_transform(vx, negative_x, width_x, positive_x, max_value_x), vy)
                for vx, vy in vertices
            ]
            print("restored_vertices: \n\n\n")
            print(vertices)
            
        if y_transformation.get("type") == "log":
            print(y_transformation)
            decades_y = y_transformation.get("params").get("decades")
            offset_y = y_transformation.get("params").get("offset")
            vertices = [
                (vx, g_utils.inverse_log_transform(vy, offset_y, decades_y))
                for vx, vy in vertices
            ]
            print("\n\n\n Restored y vertices \n\n\n\n", vertices)
            
        if y_transformation.get("type") == "biexponential":
            print(y_transformation)
            negative_y = y_transformation.get("params").get("negative")
            width_y = y_transformation.get("params").get("width")
            positive_y = y_transformation.get("params").get("positive")
            max_value_y = y_transformation.get("params").get("max_value")
            vertices = [
                (vx, g_utils.inverse_biexponential_transform(vy, negative_y, width_y, positive_y, max_value_y))
                for vx, vy in vertices
            ]
            print("\n\n\n Restored y vertices \n\n\n\n", vertices)

        # Prepare caching gating element data.
        gating_element_data = {
            "name": name,
            "vertices": vertices,
            "columns": {
                "xColumn": x_column,
                "yColumn": y_column,
                "xTransformation": {
                    "type": x_transformation.get("type"),
                    "params": x_transformation.get("params")
                } if x_transformation else None,
                "yTransformation": {
                    "type": y_transformation.get("type"),
                    "params": y_transformation.get("params")
                } if y_transformation else None
            },
            "parent_id": parent_id,
            "gating_strategy_id": gating_strategy_id,
            "flow_cytometry_id": flow_cytometry_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "created_by": username,
            "last_modified_by": username
        }

        # Create the gating element in the database.
        # The model will automatically add a progressive_id into gating_element_data.
        gt.GatingElementModel.create_gating_element(gating_element_data)
        gating_element_data.pop("_id", None)

        # ----- Parent-Child Handling in the JSON Hierarchy -----
        # Load the existing hierarchy, or initialize with a default "root" element.
        if os.path.exists(json_hierarchy_path):
            with open(json_hierarchy_path, "r") as f:
                hierarchy = json.load(f)
            # Ensure the default "root" element exists.
            if "root" not in hierarchy:
                hierarchy["root"] = {"name": "root", "children": []}
        else:
            hierarchy = {"root": {"name": "root", "children": []}}

        if parent_id is None:
            # No parent specified; add as a child of the "root" element.
            hierarchy["root"]["children"].append(gating_element_data)
        else:
            # Parent is specified; search among the children of "root".
            parent_gate = find_gate_by_id(hierarchy["root"]["children"], int(parent_id))
            if parent_gate is None:
                return jsonify({"error": "Parent gating element not found in hierarchy"}), 404
            if "children" not in parent_gate:
                parent_gate["children"] = []
            parent_gate["children"].append(gating_element_data)

        # Save the updated JSON hierarchy.
        with open(json_hierarchy_path, "w") as f:
            json.dump(hierarchy, f, indent=2)
        # ----- End Parent-Child Handling -----

        # Now, rebuild the flowkit session solely from the JSON hierarchy.
        session = fk.Session(fcs_samples=file_path)
        if os.path.exists(json_hierarchy_path):
            with open(json_hierarchy_path, "r") as f:
                updated_hierarchy = json.load(f)
            # Build the session from the children of the default "root".
            build_session_from_hierarchy_v2(session, {"gates": updated_hierarchy["root"]["children"]})
        else:
            print("Warning: Gating hierarchy JSON file not found. Creating session without gating hierarchy info.")

        # modify the gating_strategy path
        # Update the gating strategy in the database with the new path
        gt.GateStrategyModel.update_gate_strategy_by_id(
            int(gating_strategy_id), 
            {"gml_path": json_hierarchy_path}
        )
        
        # Since GML files are no longer used, we simply bypass any export.
        # The updated session (built solely from JSON) will be used downstream.
        return jsonify({
            "message": "Gating element created successfully",
        }), 201
    except Exception as e:
        print("Error in creation of gating element: ", e)
        return jsonify({"error": str(e)}), 500


# function to get all the gating elements for a specific gating strategy
def get_all_gating_elements_for_gating_strategy(username, project_id, flow_cytometry_id, gating_strategy_id):
    """
    This function handles the retrieval of all the gating elements for a specific gating strategy.
    """
    try:
        response, status_code = sec.check_permission(username, project_id)
        if status_code != 200:
            return response, status_code
        # check that the flow cytometry object exists
        flow_cytometry_object = fc.FlowCytometryModel.find_by_progressive_id(flow_cytometry_id)
        if flow_cytometry_object is None:
            return jsonify({"error": "Flow cytometry object not found"}), 404
        
        # check that the gating strategy exists 
        gating_strategy = gt.GateStrategyModel.get_gate_strategy_by_progressive_id(int(gating_strategy_id))
        if gating_strategy is None:
            return jsonify({"error": "Gating strategy not found"}), 404
        
        # check that the gating strategy is associated with the flow cytometry object
        if gating_strategy["flow_cytometry_id"] != flow_cytometry_id:
            return jsonify({"error": "Gating strategy not associated with flow cytometry object"}), 404
        
        # retrieve all the gating elements for the gating strategy
        gating_elements = list(gt.GatingElementModel.get_gating_elements_by_gating_strategy_id(gating_strategy_id))
        print("Raw gating elements:", gating_elements)  # Debug print

        # Clean up the elements and ensure proper type conversion
        cleaned_elements = []
        for gating_element in gating_elements:
            # Convert parent_id to integer if it exists, otherwise None
            parent_id = gating_element.get("parent_id")
            if parent_id is not None:
                try:
                    parent_id = int(parent_id)
                except (ValueError, TypeError):
                    print(f"Warning: Invalid parent_id format: {parent_id}")
                    parent_id = None

            # Convert progressive_id to integer
            progressive_id = gating_element.get("progressive_id")
            if progressive_id is not None:
                try:
                    progressive_id = int(progressive_id)
                except (ValueError, TypeError):
                    print(f"Warning: Invalid progressive_id format: {progressive_id}")
                    continue  # Skip this element if progressive_id is invalid

            element = {
                "progressive_id": progressive_id,
                "name": gating_element.get("name"),
                "parent_id": parent_id,  # Now properly converted to int or None
                "gating_strategy_id": gating_element.get("gating_strategy_id"),
                "vertices": gating_element.get("vertices"),
                "columns": gating_element.get("columns")
            }
            cleaned_elements.append(element)
        
        print("Cleaned elements:", cleaned_elements)  # Debug print

        # build the tree of gating elements
        gating_element_tree = g_utils.build_gating_element_tree(cleaned_elements)        
        print("Final tree:", gating_element_tree)  # Debug print

        return jsonify({"data": gating_element_tree}), 200
    except Exception as e:
        print(f"Error in get_all_gating_elements_for_gating_strategy: {str(e)}")
        return jsonify({"error": str(e)}), 500
    


# function to get the flow cytometry data from a parent id
def get_flow_cytometry_data_from_parent_id(username, project_id, flow_cytometry_id, gating_strategy_id, gating_element_id):
    """
    Retrieves flow cytometry data by performing the gating process as defined
    in the JSON hierarchy. The function rebuilds the FlowKit session from the JSON file,
    locates the target gate, and uses the session's analysis method to return the
    filtered DataFrame.
    """
    try:
        print("The filter is working")
        response, status_code = sec.check_permission(username, project_id)
        if status_code != 200:
            return response, status_code

        # Retrieve the flow cytometry object.
        flow_cytometry_object = fc.FlowCytometryModel.find_by_progressive_id(flow_cytometry_id)
        if flow_cytometry_object is None:
            return jsonify({"error": "Flow cytometry object not found"}), 404

        # Retrieve the gating strategy.
        print(f"Gating strategy id: {gating_strategy_id}")
        gating_strategy = gt.GateStrategyModel.get_gate_strategy_by_progressive_id(int(gating_strategy_id))
        if gating_strategy is None:
            return jsonify({"error": "Gating strategy not found"}), 404

        # Retrieve the gating element.
        gating_element = gt.GatingElementModel.get_gating_by_progressive_id(int(gating_element_id))
        if gating_element is None:
            return jsonify({"error": "Gating element not found"}), 404

        # Check that the gating element is associated with the gating strategy.
        if gating_element["gating_strategy_id"] != gating_strategy_id:
            return jsonify({"error": "Gating element not associated with gating strategy"}), 404

        # Decrypt the flow cytometry object.
        flow_cytometry_object = fch.decrypt_flow_cytometry_data(flow_cytometry_object)
        print("Decrypted FCS object:", flow_cytometry_object)
        
        # Determine the JSON hierarchy file path.
        # Derive the JSON file path from the gating strategy's stored "gml_path"
        # by replacing the extension with "_hierarchy.json".
        json_hierarchy_path = gating_strategy["gml_path"].replace(".gml", "_hierarchy.json")
        if not os.path.exists(json_hierarchy_path):
            return jsonify({"error": "Gating hierarchy file not found"}), 404

        with open(json_hierarchy_path, "r") as f:
            gating_hierarchy = json.load(f)
        print("Loaded gating hierarchy:", gating_hierarchy)

        # Rebuild the FlowKit session based solely on the JSON hierarchy.
        # Assume the FCS sample file path is stored (and already decrypted) in flow_cytometry_object.
        file_path = flow_cytometry_object["file_path"]
        session = fk.Session(fcs_samples=file_path)
        # The JSON hierarchy is expected to have a "root" element with "children"
        build_session_from_hierarchy_v2(session, {"gates": gating_hierarchy["root"]["children"]})
        
        # Locate the target gate structure in the JSON hierarchy using its progressive_id.
        gating_gate_structure = find_gate_by_id(gating_hierarchy["root"]["children"],
                                                  gating_element["progressive_id"])
        if gating_gate_structure is None:
            return jsonify({"error": "Gating element structure not found in hierarchy"}), 404

        # Retrieve the gate's name from the JSON structure.
        target_gate_name = gating_gate_structure["name"]
        print("Target gate name:", target_gate_name)
        
        # Retrieve the actual gate object from the session.
        try:
            # Assuming session.get_gate() allows retrieval by gate name.
            target_gate = session.get_gate(target_gate_name)
        except Exception as e:
            print("Error retrieving gate from session:", e)
            return jsonify({"error": f"Error retrieving gate from session: {e}"}), 500
        
        if target_gate is None:
            return jsonify({"error": "Gate not found in FlowKit session"}), 404

        # Use the actual FlowKit session to perform the gating.
        # @flowkit_doc: The session will re-create the various gates and then perform
        # the sample analysis. We assume the session's analyze_samples() method accepts a gate name
        # get the sample df 
        # and returns a filtered DataFrame.
        ids = session.get_sample_ids()[0]
        try:
            session.analyze_samples(ids, verbose=True)
            print(session.get_gate_ids)
            gated_df = session.get_gate_events(ids, target_gate_name)
        except Exception as e:
            print("Error analyzing samples:", e)
            return jsonify({"error": f"Error analyzing samples: {e}"}), 500
        
        print("Gated data (first 10 rows):", gated_df.head())
        
        # Use only the first level of the columns
        gated_df.columns = gated_df.columns.get_level_values(0)
        
        # Calculate statistics
        mean_values = gated_df.mean()
        std_values = gated_df.std()
        median_values = gated_df.median()

        # Create a new DataFrame for the statistics
        statistics_df = pd.DataFrame({
            'Mean': mean_values,
            'Standard Deviation': std_values,
            'Median': median_values
        }).transpose()  # Transpose to get the correct orientation

        # Print the statistics DataFrame
        print("Statistics DataFrame:\n", statistics_df)
        
        
        # Convert the dataframes to dictionaries
        gated_data = gated_df.to_dict(orient="records")
        statistics_data = statistics_df.to_dict(orient="records")
        
        print(statistics_data)
        
        return jsonify({"data": gated_data, "statistics": statistics_data}), 200
    except Exception as e:
        print(f"Error in get_flow_cytometry_data_from_parent_id: {str(e)}")
        return jsonify({"error": str(e)}), 500
        


def delete_gating_element_views(username, project_id, flow_cytometry_id, gating_strategy_id, gating_element_id):
    response, status_code = sec.check_permission(username, project_id)
    if status_code != 200:
        return response, status_code
    
    # logic to delete the gating element 
    gt.GatingElementModel.delete_gating_by_progressive_id(gating_element_id)
    
    pass 

      
    

    
    