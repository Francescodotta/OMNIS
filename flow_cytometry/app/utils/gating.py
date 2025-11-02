import flowkit as fk
from app.models import flow_cytometry as fc
from app.models import gating as gt
import os
import json
import pandas as pd
from app.helpers import flow_cytometry_helpers as fch
import numpy as np
import xml.etree.ElementTree as ET
from xml.dom import minidom
import math


# environment variables flow cytometry
FLOW_CYTOMETRY_SAVE_PATH = os.getenv("FLOW_CYTOMETRY_SAVE_PATH")


# def gml path 
def read_fcs_data(fcs_file_path):
    """
    Read FCS data from a file and return a downsampled DataFrame
    """
    # read the fcs file
    downsampled_data = fk.Sample(fcs_file_path).as_dataframe(source="raw")
    
    # subsample the data
    return downsampled_data



def read_fcs_file(flow_cytometry_id):
    """
    Function to read the fcs file and return the data as a Sample object
    
    Args:
        flow_cytometry_id (str): The flow cytometry id
        
    Returns:
        Sample: The Sample object
    """

    flow_cyto = fc.FlowCytometryModel.find_by_progressive_id(flow_cytometry_id)
    if flow_cyto is None:
        return None
    
    flow_cyto.pop("_id")
    if "workspace_id" in flow_cyto:
        flow_cyto.pop("workspace_id")
    
    flow_cyto_decrypted = fch.decrypt_flow_cytometry_data(flow_cyto)
    fcs_file_path = os.path.join(FLOW_CYTOMETRY_SAVE_PATH, flow_cyto_decrypted["file_path"])
    sample = fk.Sample(fcs_file_path)
    return sample


## create function for gating
def create_gating(sample, dim_a, dim_b, vertices, gate_name, gml_path, parent_gate = 'root', gating_strat = None):
    """
    This function handles the gating creation process saving the gating strategy in a gml file

    Parameters:
    sample (fk.Sample): sample to be gated
    dim_a (fk.Dimension): dimension a
    dim_b (fk.Dimension): dimension b
    vertices (list): list of vertices
    gate_name (str): name of the gate
    parent_gate (str): name of the parent gate
    gating_strat (str): path to the gating strategy file

    Returns:
    session (fk.Session): session object
    """
    session = fk.Session(gating_strategy=gating_strat)
    session.add_samples(sample)
    gate = fk.gates.PolygonGate(gate_name = gate_name, dimensions=[dim_a, dim_b], vertices=vertices)
    ## find parent path
    print(parent_gate)
    if parent_gate == 'root':
        session.add_gate(gate, gate_path=(parent_gate,))
    else:
        ## find the path of the entire parent gate
        gate_ids = session.get_gate_ids()
        print(gate_ids)
        ## iterate over gate_ids
        for gate_id in gate_ids:
            print(gate_id)
            if gate_id[0] == parent_gate:
                parent_path_list = list(gate_id[1])
                parent_path_list.append(parent_gate)
                parent_path = tuple(parent_path_list)
        session.add_gate(gate, gate_path=parent_path)
    session.export_gml(gml_path)
    return session


def create_gating_gml_file(data, flow_cytometry_id):
    """
    Create a GML file for a new gating element.
    
    Parameters:
        data (dict): The data containing gating element details including:
            - name: name of the gate
            - vertices: list of vertex coordinates
            - columns: dict with X and Y channel names
            - parent_path: tuple containing the path to parent gate
        flow_cytometry_id (int): The ID of the flow cytometry object.
        
    Returns:
        str: The path to the created GML file or None if failed.
    """
    try:
        # Create a new gating strategy
        gating_strategy = fk.GatingStrategy()

        # Create the gate
        x_channel = fk.Dimension(data["columns"]["xColumn"])
        y_channel = fk.Dimension(data["columns"]["yColumn"])
        new_gate = fk.gates.PolygonGate(data["name"], 
                                      dimensions=[x_channel, y_channel], 
                                      vertices=data["vertices"])
        
        parent_path = data.get("parent_path")
        ## create a tuple from the parent path with ("root", None)
        print(parent_path)
        gating_strategy.add_gate(new_gate, gate_path=parent_path)

        # Define the path where the new GML file will be saved
        gml_path = os.path.join(os.getenv("FLOW_CYTOMETRY_SAVE_PATH"), f"{data['name']}.gml")

        # Export the gating strategy to a GML file
        fk.export_gatingml(gating_strategy, gml_path, sample_id=flow_cytometry_id)

        return gml_path

    except Exception as e:
        print(f"Error in create_gating_gml_file: {str(e)}")
        return None 
    
    
# perform a gating element tree
def build_gating_element_tree(gating_elements):
    """
    This function is able to build a tree of gating elements from a list of gating elements.
    """
    # create a dictionary of the gating elements
    element_dict = {element['progressive_id']: element for element in gating_elements}
    # create a list to store the tree
    tree = []

    # at the top of the tree, we have the root element, which doesn't have a gating element instance in the db  
    root_element = {
        "progressive_id": None,
        "name": "root",
        "parent_id": None,
        "children": []
    }
    tree.append(root_element)

    # iterate over the gating elements
    for element in gating_elements:
        # get the parent id
        parent_id = element.get('parent_id')
        # if the parent id is not None, then add the element to the parent element
        if parent_id:
            # get the parent element
            parent_element = element_dict.get(parent_id)
            # if the parent element exists, then add the element to the parent element
            if parent_element:
                # if the parent element does not have a children attribute, then create one
                if 'children' not in parent_element:
                    parent_element['children'] = []
                # add the element to the parent element
                parent_element['children'].append(element)
        # if the parent id is None, then add the last "root" element to the tree   
        else:
            # if the tree is empty, then add the element to the tree
            if not tree:
                tree.append(element)
            # if the tree is not empty, then add the element to the last element in the tree
            else:
                tree[-1]['children'].append(element)

    return tree    
    
# get flow cytometry data from gml file and gating element name using flowkit
def get_flow_cytometry_from_gml_file(gml_path, flow_cytometry_file_path, gating_element_name):
    """
    This function is able to get the flow cytometry data from a gml file and a gating element name using flowkit.
    """
    # read the gml file
    ## create the session with the gml path
    print(gml_path)
    session = fk.Session(gating_strategy=gml_path, fcs_samples=[flow_cytometry_file_path])
    print(session)
    ## extract events from the gating
    sample_id = session.get_sample_ids()[0]
    session.analyze_samples(sample_id = sample_id)
    events = session.get_gate_events(sample_id = sample_id)
    events = session.get_gate_events(sample_id = sample_id, gate_name = gating_element_name)
     ## respond with the dataframe
    df = pd.DataFrame(events)
    df.columns = ['{}_{}'.format(pnn, pns) if pns else pnn for pnn, pns in df.columns]
     # Sommare le righe 'pnn' e 'pns'

    if len(df) > 10000:
        df = df.sample(n=10000, random_state = 42)
    df.reset_index(drop=True)
    return df
    

def process_transformation(transform_data, column_name):
            """
            Process transformation with more robust error handling
            """
            if not transform_data or not isinstance(transform_data, dict):
                return None

            transform_type = transform_data.get("type")
            params = transform_data.get("params", {})

            try:
                # Generate a unique transform_id
                transform_id = f"{column_name}_{transform_type}_transform"

                if transform_type == 'biexponential':
                    transformation = fk.transforms.WSPBiexTransform(
                        negative=params.get('negative', 0),
                        width=params.get('width', -10),
                        positive=params.get('positive', 4.41854),
                        max_value=params.get('max_value', 262144.000029)
                    )
                    return transform_id, transformation
                elif transform_type == 'log':
                    transformation  = fk.transforms.WSPLogTransform(
                        offset=params.get('offset', 1),
                        decades=params.get('decades', 4.5)
                    )
                    return transform_id, transformation
                else:
                    print(f"Unsupported transformation type: {transform_type}")
                    return None
            except Exception as e:
                print(f"Error creating transformation for {column_name}: {str(e)}")
                return None


def create_transformation(transform_data, column_name):
    if not transform_data or not isinstance(transform_data, dict):
        return None

    transform_type = transform_data.get("type")
    params = transform_data.get("params", {})

    if transform_type == 'biexponential':
        return fk.transforms.WSPBiexTransform(
            negative=params.get('negative', 0),
            width=params.get('width', -10),
            positive=params.get('positive', 4.41854),
            max_value=params.get('max_value', 262144.0)
        )
    elif transform_type == 'log':
        return fk.transforms.WSPLogTransform(
            offset=params.get('offset', 1),
            decades=params.get('decades', 4.5)
        )
    else:
        print(f"Unsupported transformation type: {transform_type}")
        return None

def apply_transformations(fcs_sample, x_transformation, y_transformation):
    """
    Apply transformations to a FlowKit sample
    
    Args:
    - fcs_sample: FlowKit Sample object
    - x_transformation: Transformation for x-axis
    - y_transformation: Transformation for y-axis
    
    Returns:
    - Transformed FlowKit Sample
    """
    try:
        # debugging
        print(fcs_sample)
        # Apply x-axis transformation if provided
        if x_transformation:
            print()
            fcs_sample.apply_transform(x_transformation, channels=[fcs_sample.channels[0].name])
        
        # Apply y-axis transformation if provided
        if y_transformation:
            fcs_sample.apply_transform(y_transformation, channels=[fcs_sample.channels[1].name])
        
        return fcs_sample  # Return the transformed sample directly
    
    except Exception as e:
        print(f"Error applying transformations: {str(e)}")
        raise


# Modify the GML file to include transformation parameters based on transformation type
def prepare_transformation_params(transformation):
    """
    Prepare transformation parameters based on transformation type.
    
    Args:
        transformation (dict): Transformation details dictionary
    
    Returns:
        dict: Prepared transformation parameters
    """
    # Default parameters
    default_params = {
        "offset": 1,
        "decades": 4.5
    }
    
    # If no transformation or no params, return default
    if not transformation or not transformation.get("params"):
        return default_params
    
    # Handle different transformation types
    transform_type = transformation.get("type", "log").lower()
    params = transformation.get("params", {})
    
    if transform_type == "log":
        return {
            "offset": params.get("offset", default_params["offset"]),
            "decades": params.get("decades", default_params["decades"])
        }
    elif transform_type == "logicle":
        # Logicle transformation might have different parameters
        return {
            "offset": params.get("offset", default_params["offset"]),
            "decades": params.get("decades", default_params["decades"]),
            # Add additional Logicle-specific parameters if needed
            "width": params.get("width"),
            "t": params.get("t")
        }
    elif transform_type == "asinh":
        # Inverse hyperbolic sine transformation
        return {
            "offset": params.get("offset", default_params["offset"]),
            "cofactor": params.get("cofactor", 5)
        }
    else:
        # Fallback to default log transformation
        return default_params

       
def add_transformations_to_gml(gml_path, transformations):
    """
    Add transformation parameters to an existing GML file at the top.

    Args:
        gml_path (str): Path to the input GML file.
        transformations (dict): Dictionary of transformation IDs and their parameters.
    """
    # Define the standard Gating-ML namespaces
    NAMESPACES = {
        'gating': 'http://www.isac-net.org/std/Gating-ML/v2.0/gating',
        'transforms': 'http://www.isac-net.org/std/Gating-ML/v2.0/transformations',
        'data-type': 'http://www.isac-net.org/std/Gating-ML/v2.0/datatypes'
    }

    # Register the namespaces to avoid prefix issues
    for prefix, uri in NAMESPACES.items():
        ET.register_namespace(prefix, uri)

    # Parse the existing GML file
    tree = ET.parse(gml_path)
    root = tree.getroot()

    # Create a new transformations section at the top
    transforms_section = ET.Element(f'{{{NAMESPACES["transforms"]}}}transformations')

    # Add transformations
    for transform_id, params in transformations.items():
        # Create transformation element
        transform_elem = ET.SubElement(transforms_section, f'{{{NAMESPACES["transforms"]}}}transformation')
        transform_elem.set(f'{{{NAMESPACES["transforms"]}}}id', transform_id)

        # Add log transformation details
        log_elem = ET.SubElement(transform_elem, f'{{{NAMESPACES["transforms"]}}}log')
        
        # Add offset
        offset_elem = ET.SubElement(log_elem, f'{{{NAMESPACES["transforms"]}}}offset')
        offset_elem.text = str(params.get('offset', 1))

        # Add decades
        decades_elem = ET.SubElement(log_elem, f'{{{NAMESPACES["transforms"]}}}decades')
        decades_elem.text = str(params.get('decades', 4.5))

    # Remove any existing transformations section
    existing_transforms = root.find(f'.//{{{NAMESPACES["transforms"]}}}transformations')
    if existing_transforms is not None:
        root.remove(existing_transforms)

    # Insert the new transformations section at the beginning of the root
    root.insert(0, transforms_section)

    # Write the modified XML
    # Use minidom for pretty printing
    rough_string = ET.tostring(root, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")

    # Remove extra blank lines
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])

    # Write to file
    with open(gml_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)

# inverse log transformation function

def inverse_log_transform(y, offset=1, decades=4.5):
    max_value = 262144  # Fixed constant

    # Compute inverse transformation
    x = 10 ** ((y * decades) / max_value)

    # Apply offset constraint
    return max(x, offset)

## inverse transformation for biexponential vertices
def inverse_biexponential_transform(value, negative=0, width=-10, positive=4.5, maxValue=262144):
    if value <= 0:
        return 0

    # Define transformation parameters
    decades = positive
    log_decades = math.log(decades)
    w = 0.5 if width < 0 else width
    t = maxValue

    # Compute constants
    b = log_decades / decades
    a = t / (math.exp(b * decades) - 1)

    # Apply inverse transformation
    x = (1 / b) * math.log((value / maxValue + a) / a) * t

    return x * maxValue
