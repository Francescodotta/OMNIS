import requests
import pandas as pd

def get_gene_name_uniprot(accession):
    """Get gene name from UniProt using REST API"""
    url = f"https://rest.uniprot.org/uniprotkb/{accession}"
    params = {
        'format': 'json',
        'fields': 'gene_names,gene_primary'
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'genes' in data and data['genes']:
            print(f"Found gene name for {accession}: {data['genes'][0]['geneName']['value']}")
            return data['genes'][0]['geneName']['value']
    return None

if __name__ == "__main__":
    # get the csv file and get the gene names for all the accession numbers in the csv file 
    df = pd.read_csv('QuantifiedProteins.tsv', sep='\t')
    df['Gene Name'] = df['Protein Groups'].apply(get_gene_name_uniprot)
    print(df[['Protein Groups', 'Gene Name']].head(10))  # Display first 10 rows for verification
    df.to_csv('QuantifiedProteins_with_gene_names.tsv', sep='\t', index=False)
    print("Gene names added to the DataFrame and saved to 'QuantifiedProteins_with_gene_names.tsv'.")