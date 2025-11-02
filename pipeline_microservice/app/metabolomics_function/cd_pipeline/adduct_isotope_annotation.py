import pyopenms as oms
import os
import subprocess
import tempfile


def annotate_adducts_isotopes(input_featurexml, output_featurexml, polarity="negative", user_adducts=None, user_charge=None):
    """
    Annotate adducts and isotopses in a feature map using pyOpenMS MetaboliteFeatureDeconvolution
    This function loads a feature map from an input FeatureXML file, performs adduct and isotpoe annotation using the MetaboliteFeatureDeconvolution algorithm from pyOpenMS, and saves the annotated feature map to an output FeatureXML file. The annotation process groups features based on potential adducts, charges and retention time in differences.
    
    Parameters:
    -----------
    input_featurexml : str
        Path to the input FeatureXML file containing the feature map to be annotated.

    output_featurexml : str
        Path where the annotated FeatureXML file will be saved.

    polarity : str, optional
        Ionization mode. Either "positive" or "negative". Default is "negative".
        This determines the default adduct list and charge range.

    user_adducts : list of str, optional
        Custom list of potential adducts. Each adduct is specified as a string in the format
        "element:charge:probability[:rt_shift]". If None, default adducts for the polarity are used.
        Examples:
        - Positive mode: ["H:+:0.6", "Na:+:0.4", "H-2O-1:0:0.2"]
        - Negative mode: ["H-1:-:1", "CH2O2:0:0.5"]

    user_charge : dict, optional
        Custom charge parameters. Should contain keys: "charge_min", "charge_max", "charge_span_max".
        If None, default values for the polarity are used.
        Examples:
        - Positive mode: {"charge_min": 1, "charge_max": 3, "charge_span_max": 3}
        - Negative mode: {"charge_min": -3, "charge_max": -1, "charge_span_max": 3}

    Returns:
    --------
    str
        Path to the output FeatureXML file containing the annotated feature map.

    Raises:
    -------
    FileNotFoundError
        If the input FeatureXML file does not exist.

    ValueError
        If polarity is not "positive" or "negative", or if parameters are invalid.

    RuntimeError
        If the MetaboliteFeatureDeconvolution computation fails.

    Notes:
    ------
    - The function uses pyOpenMS MetaboliteFeatureDeconvolution for adduct and isotope annotation.
    - Default parameters are set based on common metabolomics workflows but can be customized.
    - Retention time differences are set to 3.0 seconds by default.
    - The output feature map includes adduct information in the feature metadata.

    Examples:
    ---------
    >>> # Annotate with default negative mode parameters
    >>> annotate_adducts_isotopes("input.featureXML", "output.featureXML")

    >>> # Annotate with custom adducts for positive mode
    >>> custom_adducts = ["H:+:0.7", "Na:+:0.3"]
    >>> annotate_adducts_isotopes("input.featureXML", "output.featureXML", 
    ...                            polarity="positive", user_adducts=custom_adducts)
    """
    if not os.path.exists(input_featurexml):
        raise FileNotFoundError(f"Input file {input_featurexml} does not exist")
    
    if polarity not in ['positive', 'negative']:
        raise ValueError("Polarity must be 'positive' or 'negative'")
    
    # Load input feature map
    feature_map = oms.FeatureMap()
    oms.FeatureXMLFile().load(input_featurexml, feature_map)
    
    # Initialize feature deconvolution
    mfd = oms.MetaboliteFeatureDeconvolution()
    
    # Get default parameters
    params = mfd.getDefaults()
    
    # Set adduct parameters based on polarity and user input
    if user_adducts is not None:
        params.setValue("potential_adducts", user_adducts)
    else:
        if polarity == 'positive':
            params.setValue("potential_adducts", ["H:+:0.6", "Na:+:0.4", "H-2O-1:0:0.2"])
        else:
            params.setValue("potential_adducts", ["H-1:-:1", "CH202:0:0.5"])
            
    # Set charge parameters based on polarity and user input
    if user_charge is not None:
        params.setValue("charge_min", user_charge.get("charge_min", 1 if polarity == "positive" else -3))
        params.setValue("charge_max", user_charge.get("charge_max", 3 if polarity == "positive" else -1))
        params.setValue("charge_span_max", user_charge.get("charge_span_max", 3))
    else:
        if polarity == "positive":
            params.setValue("charge_min", 1, "Minimal possible charge")
            params.setValue("charge_max", 3, "Maximal possible charge")
            params.setValue("charge_span_max", 3)
        else:  # negative
            params.setValue("charge_min", -3, "Minimal possible charge")
            params.setValue("charge_max", -1, "Maximal possible charge")
            params.setValue("charge_span_max", 3)
            
    # Set retention time parameters
    params.setValue("retention_max_diff", 3.0)
    params.setValue("retention_max_diff_local", 3.0)
    
    # Set updated parameters
    mfd.setParameters(params)
    
    # prepare result objects
    feature_map_MFD = oms.FeatureMap()
    groups = oms.ConsensusMap()
    edges = oms.ConsensusMap()
    
    # Compute the adduct annotation
    try:
        mfd.compute(feature_map, feature_map_MFD, groups, edges)
    except Exception as e:
        raise RuntimeError(f"MetaboliteFeatureDeconvolution computation failed: {str(e)}")
    
    # save annotated feature map
    oms.FeatureXMLFile().store(output_featurexml, feature_map_MFD)
    print(f"Adduct/isotope annotation completed. Saved to {output_featurexml}")     
    return output_featurexml           
        