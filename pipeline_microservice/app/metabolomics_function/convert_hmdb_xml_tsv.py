import sys
import gzip
import csv
import xml.etree.ElementTree as ET

def strip_tag(t): 
    return t.split('}')[-1] if '}' in t else t

def find_child_text(elem, names):
    for c in elem:
        if strip_tag(c.tag) in names:
            if c.text and c.text.strip():
                return c.text.strip()
        # dive one level (structures -> smiles)
        for g in c:
            if strip_tag(g.tag) in names and g.text and g.text.strip():
                return g.text.strip()
    return ''

def process(hmdb_in, mapping_out, struct_out):
    opener = gzip.open if hmdb_in.endswith('.gz') else open
    with opener(hmdb_in, 'rt', encoding='utf-8') as fh, \
         open(mapping_out, 'w', newline='', encoding='utf-8') as mfh, \
         open(struct_out, 'w', newline='', encoding='utf-8') as sfh:

        map_writer = csv.writer(mfh, delimiter='\t')
        struct_writer = csv.writer(sfh, delimiter='\t')
        map_writer.writerow(['mass', 'formula', 'identifier'])
        struct_writer.writerow(['identifier', 'name', 'SMILES', 'INCHI'])

        # streaming parse for <metabolite> elements using root clear pattern (works with xml.etree)
        context = ET.iterparse(fh, events=('start','end'))
        root = None
        for event, elem in context:
            if root is None and event == 'start':
                root = elem  # store root element to clear later
            if event == 'end' and strip_tag(elem.tag) == 'metabolite':
                acc = find_child_text(elem, ('accession','id')) or ''
                name = find_child_text(elem, ('name',)) or ''
                formula = find_child_text(elem, ('chemical_formula','formula')) or ''
                exact_mass = find_child_text(elem, ('exact_mass','average_molecular_weight')) or ''
                mass_val = exact_mass if exact_mass.replace('.','',1).lstrip('-').isdigit() else '0'

                smiles = ''
                inchi = ''
                for child in elem:
                    t = strip_tag(child.tag)
                    if t in ('smiles','smile','structure') and child.text and child.text.strip():
                        if not smiles:
                            smiles = child.text.strip()
                    for g in child:
                        gt = strip_tag(g.tag)
                        if gt.lower() == 'smiles' and g.text and g.text.strip():
                            smiles = g.text.strip()
                        if gt.lower() == 'inchi' and g.text and g.text.strip():
                            inchi = g.text.strip()
                if not inchi:
                    inchi = find_child_text(elem, ('inchi','inchikey'))

                map_writer.writerow([mass_val, formula, acc])
                struct_writer.writerow([acc, name, smiles, inchi])

                # free memory: clear processed element and its ancestors via root.clear()
                elem.clear()
                if root is not None:
                    root.clear()

if __name__ == '__main__':
    hmdb_path = "/media/datastorage/it_cast/omnis_microservice_db/tools/hmdb_metabolites.xml"
    mapping_out = "/media/datastorage/it_cast/omnis_microservice_db/tools/hmdb_metabolites_mapping.tsv"
    structure_out = "/media/datastorage/it_cast/omnis_microservice_db/tools/hmdb_metabolites_structure.tsv"
    process(hmdb_path, mapping_out, structure_out)