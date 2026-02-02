"""
Enhanced Polymer Chromatography Condition Extractor
Builds on your existing code to extract detailed mobile phase and column conditions
"""

import pdfplumber
import matplotlib.pyplot as plt
import re
from collections import defaultdict
import json


polymer_names = [
    'Jordi', 'Nucleosil', 'Discovery', 'Zorbax', 'Tosoh', 
    'Phenomenex', 'Agilent', 'Supelco', 'Kromasil', 'YMC',
    'Waters', 'Spherisorb', 'Inertsil', 'Kinetex', 'Chiralpak',
    'Styragel', 'PLgel', 'Diol'  
]


common_solvents = [
    'THF', 'tetrahydrofuran', 'acetonitrile', 'ACN', 'methanol', 'MeOH',
    'water', 'H2O', 'chloroform', 'CHCl3', 'toluene', 'hexane',
    'dichloromethane', 'DCM', 'ethanol', 'EtOH', 'isopropanol', 'IPA',
    'dimethylformamide', 'DMF', 'acetone', 'heptane', 'ethyl acetate',
    'dimethoxyethane'
]

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text() + '\n'
    return text

def identify_polymers(text, polymer_names):
    """Identify mentions of polymers in the extracted text."""
    polymer_dict = {name: [] for name in polymer_names}
    
    lines = text.split('\n')
    for line in lines:
        for polymer in polymer_names:
            if polymer.lower() in line.lower():
                polymer_dict[polymer].append(line)
    
    return polymer_dict

def extract_chromatography_conditions(text):
    """
    Extract detailed chromatography conditions.
    Enhanced to include additives, gradients, and column info.
    """
    conditions = []
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
       
        keywords = ['column', 'mobile phase', 'eluent', 'flow rate', 
                   'temperature', 'particle diameter', 'pore size', 
                   'acetone', 'methanol', 'water', 'gradient']
        
        if any(keyword in line_lower for keyword in keywords):
            
            context_start = max(0, i-3)
            context_end = min(len(lines), i+4)
            context = ' '.join(lines[context_start:context_end])
            
            cond = {
                'line': line.strip(),
                'column_brand': None,
                'column_type': None,
                'dimensions': None,
                'particle_size': None,
                'pore_size': None,
                'mobile_phase_solvents': [],
                'solvent_ratio': None,
                'solvent_additives': [],
                'gradient_info': None,
                'is_gradient': False,
                'flow_rate': None,
                'temperature': None
            }
            
            for brand in polymer_names:
                if brand.lower() in context.lower():
                    cond['column_brand'] = brand
                    break
            
            
            types = ['DVB', 'divinylbenzene', 'C18', 'C8', 'C6', 'PEG', 'polyethylene glycol',
                    'Diol', 'silica', 'RP', 'reversed phase', 'normal phase', 'NP',
                    'amino', 'CN', 'cyano', 'phenyl']
            for t in types:
                if t.lower() in context.lower():
                    cond['column_type'] = t
                    break
            
            
            dim_match = re.search(r'(\d+\.?\d*)\s*[×x!]\s*(\d+\.?\d*)\s*mm', context, re.IGNORECASE)
            if dim_match:
                cond['dimensions'] = f"{dim_match.group(1)}×{dim_match.group(2)} mm"
            
            
            particle_match = re.search(r'(?:particle\s+(?:diameter|size)[:\s]*)?(\d+\.?\d*)\s*(μm|µm|um)', context, re.IGNORECASE)
            if particle_match:
                cond['particle_size'] = f"{particle_match.group(1)} μm"
            
            
            pore_match = re.search(r'(?:pore\s+size[:\s]*)?(\d+\.?\d*)\s*[AÅ]', context, re.IGNORECASE)
            if pore_match:
                cond['pore_size'] = f"{pore_match.group(1)} Å"
            
            
            if 'gradient' in context.lower():
                cond['is_gradient'] = True
               
                gradient_patterns = [
                    r'gradient[:\s]+(\d+)-(\d+)%\s+over\s+(\d+)\s*min',
                    r'gradient[:\s]+from\s+(\d+)%?\s+to\s+(\d+)%',
                    r'(\d+)-(\d+)%\s+gradient'
                ]
                for pattern in gradient_patterns:
                    grad_match = re.search(pattern, context, re.IGNORECASE)
                    if grad_match:
                        if len(grad_match.groups()) == 3:
                            cond['gradient_info'] = f"{grad_match.group(1)}-{grad_match.group(2)}% over {grad_match.group(3)} min"
                        else:
                            cond['gradient_info'] = f"{grad_match.group(1)}-{grad_match.group(2)}%"
                        break
                
                
                if not cond['gradient_info']:
                    cond['gradient_info'] = "gradient elution (details in text)"
            
            
            mp_pattern = r'(\w+)\s+(\w+)\s+(\d+):(\d+)\s*\(([wv]/[wv])\)'
            mp_match = re.search(mp_pattern, context, re.IGNORECASE)
            
            if mp_match:
                solv1, solv2 = mp_match.group(1), mp_match.group(2)
                ratio1, ratio2 = mp_match.group(3), mp_match.group(4)
                ratio_type = mp_match.group(5)
                
                cond['mobile_phase_solvents'] = [solv1, solv2]
                cond['solvent_ratio'] = f"{ratio1}:{ratio2} ({ratio_type})"
            else:
                
                ratio_match = re.search(r'(\d+):(\d+)\s*\(([wv]/[wv])\)', context)
                if ratio_match:
                    cond['solvent_ratio'] = f"{ratio_match.group(1)}:{ratio_match.group(2)} ({ratio_match.group(3)})"
                    # Find solvents nearby
                    for solv in common_solvents:
                        if solv.lower() in context.lower() and solv not in cond['mobile_phase_solvents']:
                            cond['mobile_phase_solvents'].append(solv)
            
            
            additive_patterns = [
                r'(\d+\.?\d*)\s*%\s+([A-Za-z]+)',  
                r'(\d+\.?\d*)\s*(mM|M)\s+([A-Za-z\s]+)',  
                r'with\s+(\d+\.?\d*%?\s*[A-Za-z\s]+)',  
                r'containing\s+(\d+\.?\d*%?\s*[A-Za-z\s]+)'  
            ]
            
            for pattern in additive_patterns:
                add_matches = re.findall(pattern, context, re.IGNORECASE)
                for match in add_matches:
                    if isinstance(match, tuple):
                        additive = ' '.join(str(x) for x in match).strip()
                    else:
                        additive = match.strip()
                    
                    
                    if additive and len(additive) > 2 and additive not in cond['solvent_additives']:
                        cond['solvent_additives'].append(additive)
            
            
            flow_match = re.search(r'(?:flow[\s-]?rate[:\s]*)?(\d+\.?\d*)\s*(mL|ml|μL|µL)/min', context, re.IGNORECASE)
            if flow_match:
                cond['flow_rate'] = f"{flow_match.group(1)} {flow_match.group(2)}/min"
            
            
            temp_match = re.search(r'(?:temperature[:\s]*)?(\d+\.?\d*)\s*[°8]\s*C', context, re.IGNORECASE)
            if temp_match:
                cond['temperature'] = f"{temp_match.group(1)}°C"
            
            
            if any([cond['column_brand'], cond['mobile_phase_solvents'], 
                   cond['flow_rate'], cond['temperature'], cond['is_gradient']]):
                conditions.append(cond)
    
    
    seen = set()
    unique = []
    for c in conditions:
        sig = (c['column_brand'], c['solvent_ratio'], c['flow_rate'], c['is_gradient'])
        if sig not in seen:
            seen.add(sig)
            unique.append(c)
    
    return unique

def extract_polymer_column_associations(text):
    """
    Extract which polymers (samples) are analyzed on which columns.
    This looks for patterns like "Polymer X was analyzed on Column Y"
    """
    associations = []
    lines = text.split('\n')
    
    
    polymer_samples = [
        'PEG', 'PPG', 'Pluronic', 'Synperonic', 'poloxamer', 'Imbentin',
        'EO-PO-EO', 'PO-EO-PO', 'polyethylene glycol', 'polypropylene glycol',
        'triblock', 'diblock', 'block copolymer'
    ]
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
       
        analysis_keywords = ['analyzed', 'separated', 'eluted', 'chromatogram', 
                            'measured', 'obtained on', 'using', 'performed on']
        
        if any(keyword in line_lower for keyword in analysis_keywords):
          
            context_start = max(0, i-2)
            context_end = min(len(lines), i+3)
            context = ' '.join(lines[context_start:context_end])
            
            
            found_polymers = []
            for polymer in polymer_samples:
                if polymer.lower() in context.lower():
                    found_polymers.append(polymer)
            
           
            found_columns = []
            for column in polymer_names:
                if column.lower() in context.lower():
                    found_columns.append(column)
            
            
            if found_polymers and found_columns:
                for poly in found_polymers:
                    for col in found_columns:
                        associations.append({
                            'polymer': poly,
                            'column': col,
                            'context': line.strip()
                        })
    
    
    seen = set()
    unique = []
    for assoc in associations:
        sig = (assoc['polymer'], assoc['column'])
        if sig not in seen:
            seen.add(sig)
            unique.append(assoc)
    
    return unique

def plot_polymer_frequency(polymer_dict):
    """Plot a bar graph of the frequency of polymer mentions."""
    names = list(polymer_dict.keys())
    counts = [len(lines) for lines in polymer_dict.values()]

    plt.figure(figsize=(10, 6))
    plt.bar(names, counts, color='skyblue')
    plt.xlabel('Polymers')
    plt.ylabel('Frequency')
    plt.title('Frequency of Polymer Mentions')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def print_detailed_conditions(conditions):
    """Print extracted conditions in a nice format."""
    print("\n" + "="*100)
    print("DETAILED CHROMATOGRAPHY CONDITIONS EXTRACTED")
    print("="*100)
    
    for i, cond in enumerate(conditions, 1):
        print(f"\n[Condition #{i}]")
        print("-"*100)
        
        
        if cond['column_brand']:
            col_str = f"  Column: {cond['column_brand']}"
            if cond['column_type']:
                col_str += f" ({cond['column_type']})"
            print(col_str)
            
            if cond['dimensions']:
                print(f"      -> Dimensions: {cond['dimensions']}")
            if cond['particle_size']:
                print(f"      -> Particle size: {cond['particle_size']}")
            if cond['pore_size']:
                print(f"      -> Pore size: {cond['pore_size']}")
        
        
        if cond['mobile_phase_solvents'] or cond['is_gradient']:
            print(f"  Mobile phase:")
            
            if cond['is_gradient']:
                print(f"      -> Type: Gradient")
                if cond['gradient_info']:
                    print(f"      -> Gradient: {cond['gradient_info']}")
            else:
                print(f"      -> Type: Isocratic")
            
            if cond['mobile_phase_solvents']:
                print(f"      -> Solvents: {', '.join(cond['mobile_phase_solvents'])}")
            
            if cond['solvent_ratio']:
                print(f"      -> Ratio: {cond['solvent_ratio']}")
            
            if cond['solvent_additives']:
                print(f"      -> Additives: {', '.join(cond['solvent_additives'])}")
        
       
        if cond['flow_rate']:
            print(f"  Flow rate: {cond['flow_rate']}")
        
        if cond['temperature']:
            print(f"  Temperature: {cond['temperature']}")
        
        
        print(f"  Source: \"{cond['line']}\"")

def create_summary_table(conditions):
    """Create a summary table of all conditions."""
    summary = {
        'columns': defaultdict(int),
        'mobile_phases': defaultdict(int),
        'flow_rates': set(),
        'temperatures': set()
    }
    
    for cond in conditions:
        if cond['column_brand']:
            col_key = cond['column_brand']
            if cond['column_type']:
                col_key += f" {cond['column_type']}"
            summary['columns'][col_key] += 1
        
        if cond['mobile_phase_solvents'] and cond['solvent_ratio']:
            mp_key = f"{'/'.join(cond['mobile_phase_solvents'])} {cond['solvent_ratio']}"
            summary['mobile_phases'][mp_key] += 1
        
        if cond['flow_rate']:
            summary['flow_rates'].add(cond['flow_rate'])
        
        if cond['temperature']:
            summary['temperatures'].add(cond['temperature'])
    
    return summary

def main(pdf_path):
    """
    Main function to extract and analyze polymer chromatography conditions.
    
    Extracts:
    - Column specifications (brand, type, dimensions, particle size, pore size)
    - Mobile phase details (solvents, ratios, additives, gradient info)
    - Operating conditions (flow rate, temperature)
    - Polymer-column associations
    """
    
    print("="*100)
    print("ENHANCED POLYMER CHROMATOGRAPHY ANALYZER")
    print("="*100)
    
    
    print("\nExtracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    print("Text extraction complete.")
    
    
    print("\nIdentifying column brands...")
    polymer_dict = identify_polymers(text, polymer_names)
    brand_count = sum(1 for lines in polymer_dict.values() if lines)
    print(f"Found {brand_count} column brand(s) mentioned.")
    
    
    print("\nExtracting chromatography conditions...")
    conditions = extract_chromatography_conditions(text)
    print(f"Extracted {len(conditions)} detailed condition(s).")
    
   
    print("\nExtracting polymer-column associations...")
    associations = extract_polymer_column_associations(text)
    print(f"Found {len(associations)} polymer-column association(s).")
    
    
    print("\n" + "="*100)
    print("RESULTS")
    print("="*100)
    
    
    print("\n" + "="*100)
    print("COLUMN BRAND MENTIONS")
    print("="*100)
    found_brands = {polymer: lines for polymer, lines in polymer_dict.items() if lines}
    if found_brands:
        for polymer, lines in found_brands.items():
            print(f"  {polymer}: {len(lines)} mention(s)")
    else:
        print("  No column brands detected.")
    
   
    if associations:
        print("\n" + "="*100)
        print("POLYMER-COLUMN ASSOCIATIONS")
        print("="*100)
        
        
        by_column = defaultdict(list)
        for assoc in associations:
            by_column[assoc['column']].append(assoc['polymer'])
        
        for column in sorted(by_column.keys()):
            polymers = list(set(by_column[column]))
            print(f"\n  {column} Column:")
            for poly in polymers:
                print(f"      -> {poly}")
        
        print("\n  Detailed Associations:")
        for i, assoc in enumerate(associations, 1):
            print(f"    {i}. {assoc['polymer']} on {assoc['column']}")
            print(f"       Context: \"{assoc['context']}\"")
    
    
    print_detailed_conditions(conditions)
    
    
    print("\n" + "="*100)
    print("Generating frequency plot...")
    plot_polymer_frequency(polymer_dict)
    
    
    json_output = {
        "metadata": {
            "source_file": pdf_path,
            "total_conditions_found": len(conditions),
            "total_associations_found": len(associations),
            "column_brands_detected": list(found_brands.keys())
        },
        "chromatography_data": []
    }
    
   
    for i, cond in enumerate(conditions, 1):
        entry = {
            "condition_id": i,
            "stationary_phase_details": {
                "column_brand": cond.get('column_brand'),
                "column_type": cond.get('column_type'),
                "material_modification": cond.get('column_type'),
                "column_dimensions": cond.get('dimensions'),
                "particle_diameter": cond.get('particle_size'),
                "pore_size": cond.get('pore_size')
            },
            "solvent_details": {
                "solvents": cond.get('mobile_phase_solvents', []),
                "ratio": cond.get('solvent_ratio'),
                "additives": cond.get('solvent_additives', []),
                "is_gradient": cond.get('is_gradient', False),
                "gradient_info": cond.get('gradient_info')
            },
            "technical_details": {
                "flow_rate": cond.get('flow_rate'),
                "temperature": cond.get('temperature')
            },
            "source_information": {
                "original_line": cond.get('line')
            }
        }
        json_output["chromatography_data"].append(entry)
    
   
    if associations:
        json_output["polymer_column_associations"] = [
            {
                "polymer": assoc['polymer'],
                "column": assoc['column'],
                "context": assoc['context']
            }
            for assoc in associations
        ]
    
    
    json_output["column_mention_statistics"] = {
        column: len(lines) 
        for column, lines in polymer_dict.items() 
        if lines
    }
    
    
    output_json = pdf_path.replace('.pdf', '_chromatography_data.json')
    try:
        with open(output_json, 'w') as f:
            json.dump(json_output, f, indent=2)
        print(f"\nAll data saved to unified JSON: {output_json}")
    except Exception as e:
        print(f"\nWarning: Could not save JSON file: {e}")
    
    print("\n" + "="*100)
    print("ANALYSIS COMPLETE")
    print("="*100)
    
    return {
        'polymer_mentions': polymer_dict,
        'conditions': conditions,
        'associations': associations,
        'json_data': json_output
    }

if __name__ == "__main__":
    
    pdf_path = '/Users/mishakavdia/polymer.project-1/[251] Trathnigg2005.pdf'
    results = main(pdf_path)