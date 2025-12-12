import os
import json
import flowkit as fk
from uuid import uuid4

def load_hierarchy(json_path):
    """
    Load gating hierarchy from the JSON file.
    Returns a dictionary with at least a "gates" list.
    """
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    # If not present, initialize an empty hierarchy
    return {"gates": []}

def save_hierarchy(json_path, hierarchy):
    """
    Save the gating hierarchy to the JSON file.
    """
    with open(json_path, 'w') as f:
        json.dump(hierarchy, f, indent=2)

def find_gate_by_id(gates, gate_id):
    """
    Recursively search for a gate with the given gating_element_id.
    """
    for gate in gates:
        if gate.get("progressive_id") == gate_id:
            return gate
        if "children" in gate:
            found = find_gate_by_id(gate["children"], gate_id)
            if found:
                return found
    return None

def add_gate_to_hierarchy(json_path, new_gate):
    """
    Add a new gate to the JSON hierarchy file.
    new_gate is expected to be a dictionary containing at least:
      - "gating_element_id": a unique identifier (should match the database id)
      - "parent_id": the id of the parent gate (or None if root)
      - other parameters (name, vertices, transformation info, etc.)
    """
    hierarchy = load_hierarchy(json_path)
    parent_id = new_gate.get("parent_id")
    
    if not parent_id:
        # If no parent, add directly at the root level.
        hierarchy["gates"].append(new_gate)
    else:
        # Try to find the parent gate in the current hierarchy.
        parent_gate = find_gate_by_id(hierarchy["gates"], parent_id)
        if parent_gate:
            if "children" not in parent_gate:
                parent_gate["children"] = []
            parent_gate["children"].append(new_gate)
        else:
            # If no parent found, optionally add the gate at the root level.
            hierarchy["gates"].append(new_gate)
    
    save_hierarchy(json_path, hierarchy)

def build_session_from_hierarchy(session, hierarchy):
    """
    Recursively add gating elements (gates) into the flowkit session based on the JSON hierarchy.
    The caller supplies a flowkit session and the hierarchy data (as a dict). Each gate in the hierarchy 
    is processed by reading its name, vertices, columns (including transformations), and then adding it 
    to the session. Child gates are recursively processed.
    """

    def process_gate(gate, parent_gate_path=("root",)):
        # Retrieve information from the gate entry.
        name = gate["name"]
        columns = gate.get("columns", {})
        x_column = columns.get("xColumn")
        y_column = columns.get("yColumn")
        vertices = gate.get("vertices")
        
        # Initialize transformation information.
        x_transform_id = None
        y_transform_id = None
    

        if columns.get("xTransformation"):
            progressive_id_x= str(uuid4())
            print(progressive_id_x)
            x_trans = columns["xTransformation"]
            if x_trans.get("type") == "log":
                x_transform_id = f"{x_column}_{name}_{x_trans.get('type')}_{progressive_id_x}"
                x_transform_fk = fk.transforms.WSPLogTransform(
                    offset=x_trans.get("params", {}).get("offset", 1),
                    decades=x_trans.get("params", {}).get("decades", 4.5)
                )
                session.add_transform(x_transform_id, x_transform_fk)

        if columns.get("yTransformation"):
            progressive_id_y = str(uuid4())
            y_trans = columns["yTransformation"]
            if y_trans.get("type") == "log":
                y_transform_id = f"{y_column}_{name}_{y_trans.get('type')}_{progressive_id_y}"
                y_transform_fk = fk.transforms.WSPLogTransform(
                    offset=y_trans.get("params", {}).get("offset", 1),
                    decades=y_trans.get("params", {}).get("decades", 4.5)
                )
                session.add_transform(y_transform_id, y_transform_fk)

        # Create flowkit Dimensions.
        x_dim = fk.Dimension(
            x_column,
            compensation_ref="uncompensated",
            transformation_ref=x_transform_id
        )
        y_dim = fk.Dimension(
            y_column,
            compensation_ref="uncompensated",
            transformation_ref=y_transform_id
        )
        # Create the polygon gate with the given vertices.
        new_gate = fk.gates.PolygonGate(
            name,
            dimensions=[x_dim, y_dim],
            vertices=vertices
        )
        # Add the gate in the session at the appropriate path.
        session.add_gate(new_gate, gate_path=parent_gate_path)

        # Recursively process children gates if they exist.
        for child in gate.get("children", []):
            process_gate(child, parent_gate_path=(name,))

    # Process every top-level gate in the hierarchy.
    for gate in hierarchy.get("gates", []):
        process_gate(gate)
        
        
# retrieve data from parent id
def build_session_from_hierarchy_v2(session, hierarchy):
    """
    Recursively add gating elements (gates) into the flowkit session based on the JSON hierarchy.
    The caller supplies a flowkit session and the hierarchy data (as a dict). Each gate in the hierarchy 
    is processed by reading its name, vertices, columns (including transformations), and then adding it 
    to the session. Child gates are recursively processed.
    """

    def process_gate(gate, parent_gate_path=("root",)):
        # Retrieve information from the gate entry.
        name = gate["name"]
        columns = gate.get("columns", {})
        x_column = columns.get("xColumn")
        y_column = columns.get("yColumn")
        vertices = gate.get("vertices")
        
        # Initialize transformation information.
        x_transform_id = None
        y_transform_id = None
    

        if columns.get("xTransformation"):
            progressive_id_x = str(uuid4())
            print(progressive_id_x)
            x_trans = columns["xTransformation"]
            if x_trans.get("type") == "log":
                x_transform_id = f"{x_column}_{name}_{x_trans.get('type')}_{progressive_id_x}"
                x_transform_fk = fk.transforms.WSPLogTransform(
                    offset=x_trans.get("params", {}).get("offset", 1),
                    decades=x_trans.get("params", {}).get("decades", 4.5)
                )
                session.add_transform(x_transform_id, x_transform_fk)

        if columns.get("yTransformation"):
            progressive_id_y = str(uuid4())
            y_trans = columns["yTransformation"]
            if y_trans.get("type") == "log":
                y_transform_id = f"{y_column}_{name}_{y_trans.get('type')}_{progressive_id_y}"
                y_transform_fk = fk.transforms.WSPLogTransform(
                    offset=y_trans.get("params", {}).get("offset", 1),
                    decades=y_trans.get("params", {}).get("decades", 4.5)
                )
                session.add_transform(y_transform_id, y_transform_fk)

        # Create flowkit Dimensions.
        x_dim = fk.Dimension(
            x_column,
            compensation_ref="uncompensated",
        )
        y_dim = fk.Dimension(
            y_column,
            compensation_ref="uncompensated",
        )
        # Create the polygon gate with the given vertices.
        new_gate = fk.gates.PolygonGate(
            name,
            dimensions=[x_dim, y_dim],
            vertices=vertices
        )
        # Add the gate in the session at the appropriate path.
        session.add_gate(new_gate, gate_path=parent_gate_path)

        # Recursively process children gates if they exist.
        for child in gate.get("children", []):
            # Append the current gate's name to preserve the full hierarchical path.
            process_gate(child, parent_gate_path=parent_gate_path + (name,))

    # Process every top-level gate in the hierarchy.
    for gate in hierarchy.get("gates", []):
        process_gate(gate)