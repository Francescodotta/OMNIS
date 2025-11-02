import polars as pl
import xml.etree.ElementTree as ET
import pyopenms as oms

def parse_hmdb_to_dataframe_streaming(xml_path):
    ns = {'hmdb': 'http://www.hmdb.ca'}
    data = []
    context = ET.iterparse(xml_path, events=("end",))
    for event, elem in context:
        if elem.tag.endswith("metabolite"):
            accession = elem.findtext('hmdb:accession', default='', namespaces=ns)
            name = elem.findtext('hmdb:name', default='', namespaces=ns)
            mass = elem.findtext('hmdb:monisotopic_molecular_weight', default='', namespaces=ns)
            try:
                mass = float(mass)
            except (ValueError, TypeError):
                elem.clear()
                continue
            data.append({'accession': accession, 'name': name, 'mass': mass})
            elem.clear()  # Free memory
    df = pl.DataFrame(data)
    df = df.sort("mass")
    return df

def load_kegg_compounds_csv(csv_path):
    # Assumes columns: KEGG_ID, Name, Formula, Exact_Mass
    df = pl.read_csv(csv_path)
    df = df.with_columns(pl.col("Exact_Mass").cast(pl.Float64))
    df = df.sort("Exact_Mass")
    return df


def search_hmdb_by_mz(df, mz, ppm=5):
    delta = mz * ppm * 1e-6
    hits = df.filter((pl.col("mass") >= mz - delta) & (pl.col("mass") <= mz + delta))
    return hits


def search_kegg_by_mz(df, mz, ppm=5, top_n=10):
    delta = mz * ppm * 1e-6
    hits = df.filter((pl.col("Exact_Mass") >= mz - delta) & (pl.col("Exact_Mass") <= mz + delta))
    hits = hits.with_columns((pl.col("Exact_Mass") - mz).abs().alias("mass_diff"))
    hits = hits.sort("mass_diff")
    return hits.head(top_n)



def consensus_to_feature_dicts(consensusxml, hmdb_df, kegg_df, ppm=5, kegg_ppm=5, kegg_top_n=10):
    consensus_map = oms.ConsensusMap()
    oms.ConsensusXMLFile().load(consensusxml, consensus_map)
    feature_dicts = []

    for feature in consensus_map:
        mz = feature.getMZ()
        rt = feature.getRT()
        intensity = feature.getIntensity()

        # collect all underlying precursor ions, charges, and per-sample intensities
        precursor_ions = []
        precursor_charges = []
        per_sample_intensity = {}
        for handle in feature.getFeatureList():
            precursor_ions.append(round(handle.getMZ(), 4))
            precursor_charges.append(handle.getCharge())
            map_idx = handle.getMapIndex()
            per_sample_intensity[map_idx] = handle.getIntensity()


        # HMDB search
        hmdb_hits = search_hmdb_by_mz(hmdb_df, mz, ppm=ppm)
        hmdb_matches = hmdb_hits.to_dicts()
        # KEGG search
        kegg_hits = search_kegg_by_mz(kegg_df, mz, ppm=kegg_ppm, top_n=kegg_top_n)
        kegg_matches = kegg_hits.to_dicts()
        # Find common annotations by name (case-insensitive)
        hmdb_names = set(m['name'].strip().lower() for m in hmdb_matches if m.get('name'))
        kegg_names = set(m['Name'].strip().lower() for m in kegg_matches if m.get('Name'))
        common_names = hmdb_names & kegg_names
        common_annotations = []
        for name in common_names:
            hmdb_ann = [m for m in hmdb_matches if m.get('name', '').strip().lower() == name]
            kegg_ann = [m for m in kegg_matches if m.get('Name', '').strip().lower() == name]
            for h in hmdb_ann:
                for k in kegg_ann:
                    common_annotations.append({'hmdb': h, 'kegg': k})
        # Gather source file indices (input maps)
        input_maps = set()
        for handle in feature.getFeatureList():
            input_maps.add(handle.getMapIndex())
        feature_dicts.append({
            "mz": round(mz, 4),
            "rt": round(rt/60, 4),  # Convert seconds to minutes
            "hmdb_matches": hmdb_matches,
            "kegg_matches": kegg_matches,
            "common_annotations": common_annotations,
            'peak_area': intensity,
            'precursor_ions': precursor_ions,
            'precursor_charges': precursor_charges,
            "input_maps": list(input_maps),
            "per_sample_intensity": per_sample_intensity
        })

    print(f"Processed {len(feature_dicts)} features from consensus XML.")
    print(f'kegg compounds: {len(kegg_df)},  {kegg_df.head(5)} \n\n')
    return feature_dicts

if __name__ == "__main__":
    xml_path = '/media/datastorage/it_cast/omnis_microservice_db/tools/hmdb_metabolites.xml'
    kegg_csv_path = '/media/datastorage/it_cast/omnis_microservice_db/tools/kegg_compounds.csv'
    hmdb_df = parse_hmdb_to_dataframe_streaming(xml_path)
    kegg_df = load_kegg_compounds_csv(kegg_csv_path)
    feature_dicts = consensus_to_feature_dicts("final.consensusXML", hmdb_df, kegg_df, ppm=50, kegg_ppm=50, kegg_top_n=10)
    print(feature_dicts[:5])
    for i, feat in enumerate(feature_dicts[:5]):
        print(f"Feature {i+1}: m/z={feat['mz']:.5f}, RT={feat['rt']:.2f}")
        print("  HMDB matches:")
        for match in feat["hmdb_matches"]:
            print(f"    {match}")
        print("  Top 10 KEGG matches:")
        for match in feat["kegg_matches"]:
            print(f"    {match}")
        print("  Common annotations (HMDB+KEGG):")
        for match in feat["common_annotations"]:
            print(f"    {match}")
        print()
