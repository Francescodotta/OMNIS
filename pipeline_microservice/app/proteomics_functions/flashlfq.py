import os 
import subprocess   
from dotenv import load_dotenv
import sys
import pandas as pd
import re
from Bio import SeqIO

load_dotenv()

def verify_input_files(input_pin_file, mzml_file):
    """Verify input files exist and are readable"""
    if not os.path.exists(input_pin_file):
        raise FileNotFoundError(f"PIN file not found: {input_pin_file}")
    if not os.path.exists(mzml_file):
        raise FileNotFoundError(f"mzML file not found: {mzml_file}")
    
    # Check file sizes
    if os.path.getsize(input_pin_file) == 0:
        raise ValueError(f"PIN file is empty: {input_pin_file}")
    if os.path.getsize(mzml_file) == 0:
        raise ValueError(f"mzML file is empty: {mzml_file}")

def parse_fasta_for_gene_names(fasta_file):
    """
    Parse FASTA file to extract gene names for each protein accession.
    
    Parameters:
    - fasta_file (str): Path to the FASTA file
    
    Returns:
    - dict: Dictionary mapping protein accessions to gene names
    """
    gene_map = {}
    
    if not os.path.exists(fasta_file):
        raise FileNotFoundError(f"FASTA file not found: {fasta_file}")
    
    print(f"Parsing FASTA file: {fasta_file}")
    
    with open(fasta_file, "r") as file:
        for record in SeqIO.parse(file, "fasta"):
            # Extract accession from the record ID
            accession = record.id
            
            # Extract gene name from the description
            description = record.description
            gene_name = extract_gene_name_from_description(description)
            
            if gene_name:
                gene_map[accession] = gene_name
            else:
                # If no gene name found, use the accession as fallback
                gene_map[accession] = accession
    
    print(f"Extracted gene names for {len(gene_map)} proteins from FASTA")
    return gene_map

def extract_gene_name_from_description(description):
    """
    Extract gene name from FASTA description line.
    
    Parameters:
    - description (str): FASTA description line
    
    Returns:
    - str: Gene name if found, None otherwise
    """
    # Pattern for UniProt format: >sp|P12345|GENENAME_HUMAN Description GN=GENENAME
    gn_pattern = r'GN=(\w+)'
    match = re.search(gn_pattern, description)
    if match:
        return match.group(1)
    
    # Pattern for simple format: >ACCESSION GENENAME Description
    simple_pattern = r'>\w+\s+(\w+)'
    match = re.search(simple_pattern, description)
    if match:
        return match.group(1)
    
    # Pattern for pipe-separated format: >sp|ACCESSION|GENENAME_ORGANISM
    pipe_pattern = r'>\w+\|[\w\d]+\|(\w+)_'
    match = re.search(pipe_pattern, description)
    if match:
        return match.group(1)
    
    return None

def filter_and_annotate_quantified_proteins(quantified_proteins_file, fasta_file, output_file=None):
    """
    Filter quantified proteins to remove zero intensities and add gene names from FASTA.
    
    Parameters:
    - quantified_proteins_file (str): Path to the QuantifiedProteins.tsv file
    - fasta_file (str): Path to the FASTA file
    - output_file (str): Path for the output file (optional)
    
    Returns:
    - str: Path to the filtered and annotated output file
    """
    # Read the quantified proteins file
    df = pd.read_csv(quantified_proteins_file, sep='\t')
    
    print(f"Original dataset shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Find intensity columns (columns that contain intensity values)
    intensity_columns = [col for col in df.columns if 'Intensity' in col or col.startswith('Intensity')]
    
    if not intensity_columns:
        # If no explicit intensity columns, assume all numeric columns except first few metadata columns
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        # Exclude common metadata columns
        metadata_cols = ['Protein Groups', 'Gene Name', 'Organism']
        intensity_columns = [col for col in numeric_columns if col not in metadata_cols]
    
    print(f"Intensity columns found: {intensity_columns}")
    
    # Filter out rows where all intensity values are zero
    if intensity_columns:
        # Create a mask for rows where at least one intensity column is non-zero
        non_zero_mask = (df[intensity_columns] != 0).any(axis=1)
        df_filtered = df[non_zero_mask].copy()
    else:
        # If no intensity columns found, filter based on the last column (assuming it's intensity)
        last_col = df.columns[-1]
        df_filtered = df[df[last_col] != 0].copy()
    
    print(f"After filtering zero intensities: {df_filtered.shape}")
    
    # Parse FASTA file to get gene names
    gene_map = parse_fasta_for_gene_names(fasta_file)
    
    # Add gene names to the dataframe
    def get_gene_name(protein_groups):
        if pd.isna(protein_groups) or protein_groups == '':
            return ''
        
        # Split by semicolon if multiple proteins
        proteins = str(protein_groups).split(';')
        gene_names = []
        
        for protein in proteins:
            protein = protein.strip()
            
            # Try direct lookup first
            if protein in gene_map:
                gene_names.append(gene_map[protein])
                continue
            
            # Try to extract accession from UniProt format
            accession = extract_accession_from_protein_id(protein)
            if accession and accession in gene_map:
                gene_names.append(gene_map[accession])
                continue
            
            # If not found, use the original protein ID
            gene_names.append(protein)
        
        return ';'.join(gene_names)
    
    # Apply gene name mapping
    df_filtered['Gene Name'] = df_filtered['Protein Groups'].apply(get_gene_name)
    
    # Reorder columns to put Gene Name after Protein Groups
    cols = df_filtered.columns.tolist()
    if 'Gene Name' in cols:
        cols.remove('Gene Name')
        protein_groups_idx = cols.index('Protein Groups') if 'Protein Groups' in cols else 0
        cols.insert(protein_groups_idx + 1, 'Gene Name')
        df_filtered = df_filtered[cols]
    
    # Save the filtered and annotated file
    if output_file is None:
        base_name = os.path.splitext(quantified_proteins_file)[0]
        output_file = f"{base_name}_filtered_annotated.tsv"
    
    df_filtered.to_csv(output_file, sep='\t', index=False)
    
    print(f"Filtered and annotated data saved to: {output_file}")
    print(f"Final dataset shape: {df_filtered.shape}")
    print(f"Non-zero proteins: {len(df_filtered)}")
    
    return output_file

def extract_accession_from_protein_id(protein_id):
    """
    Extract accession from various protein ID formats.
    
    Parameters:
    - protein_id (str): Protein identifier
    
    Returns:
    - str: Extracted accession or original ID if no pattern matches
    """
    # UniProt format: sp|P12345|PROTEIN_HUMAN
    uniprot_pattern = r'(?:sp|tr|swiss-prot)\|([A-Z0-9]+)\|'
    match = re.search(uniprot_pattern, protein_id)
    if match:
        return match.group(1)
    
    # Simple accession format
    accession_pattern = r'^([A-Z0-9]+)$'
    match = re.search(accession_pattern, protein_id)
    if match:
        return match.group(1)
    
    # Return original if no pattern matches
    return protein_id

def run_flashlfq(input_pin_file, mzml_file, output_dir):
    """
    Run FlashLFQ from the command line on the given PIN file.
    
    Parameters:
    - input_pin_file (str): Path to the FlashLFQ input (.pin) or (.tsv) file.
    - mzml_file (str): Path to the mzML file.
    - output_dir (str): Output directory for FlashLFQ results.
    
    Returns:
    - dict: Paths to the output files
    """
    # Verify input files
    verify_input_files(input_pin_file, mzml_file)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    flashlfq_path = os.path.join(os.getenv('TOOLS_BASE_PATH'), "FlashLFQ/CMD/bin/Release/net8.0/CMD.dll")
    if not os.path.exists(flashlfq_path):
        raise FileNotFoundError(f"FlashLFQ not found at: {flashlfq_path}")
    
    command = [
        "dotnet",
        flashlfq_path,
        "--idt", input_pin_file,
        "--rep", os.path.dirname(mzml_file),
        "--out", output_dir,
        '--sha',
        "--chg",
    ]
    
    print(f"Running FlashLFQ: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        print("FlashLFQ Output:")
        print(result.stdout)
        
        # Check for expected output files
        expected_files = [
            "QuantifiedPeaks.tsv",
            "QuantifiedPeptides.tsv",
            "QuantifiedProteins.tsv"
        ]
        
        output_files = {}
        missing_files = []
        
        for file in expected_files:
            file_path = os.path.join(output_dir, file)
            if os.path.exists(file_path):
                output_files[file] = file_path
            else:
                missing_files.append(file)
        
        if missing_files:
            print("\nWarning: Expected output files not found:")
            for file in missing_files:
                print(f"- {file}")
            print("\nFlashLFQ stderr output:")
            print(result.stderr)
            raise RuntimeError("FlashLFQ did not generate all expected output files")
            
        return output_files
                
    except subprocess.CalledProcessError as e:
        print(f"FlashLFQ failed with exit code {e.returncode}")
        print("Error output:")
        print(e.stderr)
        raise

if __name__ == "__main__":
    try:
        # Example usage for FlashLFQ
        input_pin_file = "/media/datastorage/it_cast/omnis_microservice_db/test_db/flashlfq_input.tsv"
        mzml_file = os.path.join("/media/datastorage/it_cast/omnis_microservice_db/test_db", "20250228_04_01.mzML")
        output_dir = os.path.join("/media/datastorage/it_cast/omnis_microservice_db/test_db/", "flashlfq_results")
        
        # Run FlashLFQ
        output_files = run_flashlfq(input_pin_file, mzml_file, output_dir)
        print("\nSuccessfully generated output files:")
        for file_name, file_path in output_files.items():
            print(f"- {file_name}: {file_path}")
        
        # Filter and annotate the QuantifiedProteins.tsv file
        if "QuantifiedProteins.tsv" in output_files:
            fasta_file = "/media/datastorage/it_cast/omnis_microservice_db/test_db/fasta/combined_target_decoy_database.fasta"  # Update this path as needed
            filtered_file = filter_and_annotate_quantified_proteins(
                output_files["QuantifiedProteins.tsv"], 
                fasta_file
            )
            print(f"\nFiltered and annotated file created: {filtered_file}")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)