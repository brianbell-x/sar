"""
Script to update field names in the PDF analysis JSON.
"""

import json
import pdfrw
import logging
import re

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def analyze_pdf_fields(pdf_path: str) -> dict:
    """Analyze PDF fields and return their names."""
    pdf = pdfrw.PdfReader(pdf_path)
    fields = {}
    radio_groups = {}
    
    # First pass - collect all button fields and their parents
    button_fields = {}
    for page_idx, page in enumerate(pdf.pages, 1):
        if not page.Annots:
            continue
            
        for annotation in page.Annots:
            if annotation.Subtype == "/Widget":
                field_name = str(annotation["/T"]).strip("()")
                if not field_name:
                    continue
                    
                field_type = str(annotation["/FT"])
                if field_type == "/Btn":
                    # Get parent field name
                    parent_name = None
                    if "/Parent" in annotation:
                        parent = annotation["/Parent"]
                        if "/T" in parent:
                            parent_name = str(parent["/T"]).strip("()")
                            logger.debug(f"Found button with parent: {parent_name}")
                    
                    # Extract base name (e.g. "item5" from "item5.0")
                    base_name = re.match(r'([^.]+)', field_name).group(1)
                    if base_name not in button_fields:
                        button_fields[base_name] = []
                    button_fields[base_name].append({
                        'name': field_name,
                        'page': page_idx,
                        'annotation': annotation,
                        'parent_name': parent_name
                    })
    
    # Second pass - analyze button fields to detect radio groups
    for base_name, buttons in button_fields.items():
        # Check if any button has a parent field
        has_parent = any(button['parent_name'] for button in buttons)
        if has_parent:
            logger.debug(f"Found radio group: {base_name}")
            radio_groups[base_name] = {
                "name": base_name,
                "type": "/Btn",
                "page": buttons[0]['page'],
                "options": []
            }
            
            for button in buttons:
                annotation = button['annotation']
                if "/AP" in annotation and "/N" in annotation["/AP"]:
                    n_dict = annotation["/AP"]["/N"]
                    states = [str(k) for k in n_dict.keys() if k != "/Off"]
                    if states:
                        for state in states:
                            if state not in radio_groups[base_name]["options"]:
                                radio_groups[base_name]["options"].append(state)
                                logger.debug(f"Added option {state} to radio group {base_name}")
        else:  # Single button = checkbox
            button = buttons[0]
            field_name = button['name']
            annotation = button['annotation']
            
            fields[field_name] = {
                "name": field_name,
                "type": "/Btn",
                "page": button['page']
            }
            
            # Get checkbox states
            ap = annotation["/AP"]
            if ap:
                logger.debug(f"Processing button field: {field_name}")
                logger.debug(f"AP dictionary: {ap}")
                if "/N" in ap:
                    n_dict = ap["/N"]
                    states = [str(k) for k in n_dict.keys()]
                    fields[field_name]["states"] = states
                    logger.debug(f"States from N dict: {states}")
                
                if "/D" in ap:
                    d_dict = ap["/D"]
                    down_states = [str(k) for k in d_dict.keys()]
                    fields[field_name]["down_states"] = down_states
                    logger.debug(f"Down states: {down_states}")
                    
            # Get appearance state
            if "/AS" in annotation:
                fields[field_name]["appearance_state"] = str(annotation["/AS"])
                logger.debug(f"Appearance state: {annotation['/AS']}")
                
            # Get value
            if "/V" in annotation:
                fields[field_name]["value"] = str(annotation["/V"])
                logger.debug(f"Value: {annotation['/V']}")
                
            # Get flags
            if "/Ff" in annotation:
                flags = int(str(annotation["/Ff"]))
                fields[field_name]["flags"] = flags
                logger.debug(f"Flags: {flags}")
    
    # Add non-button fields
    for page_idx, page in enumerate(pdf.pages, 1):
        if not page.Annots:
            continue
            
        for annotation in page.Annots:
            if annotation.Subtype == "/Widget":
                field_name = str(annotation["/T"]).strip("()")
                if not field_name:
                    continue
                    
                field_type = str(annotation["/FT"])
                if field_type != "/Btn":
                    fields[field_name] = {
                        "name": field_name,
                        "type": field_type,
                        "page": page_idx
                    }
                    
                    if field_type == "/Tx":
                        # Get max length if present
                        if "/MaxLen" in annotation:
                            fields[field_name]["max_length"] = str(annotation["/MaxLen"])
                        
                        # Get default value if present
                        if "/DV" in annotation:
                            fields[field_name]["default_value"] = str(annotation["/DV"])
                            
                        # Get current value if present
                        if "/V" in annotation:
                            fields[field_name]["current_value"] = str(annotation["/V"])
                            
                        # Get flags if present
                        if "/Ff" in annotation:
                            fields[field_name]["flags"] = str(annotation["/Ff"])
    
    # Add radio groups to fields
    fields.update(radio_groups)
    return fields

def main():
    # Analyze original PDF
    fields = analyze_pdf_fields("resources/6710-06.pdf")
    
    # Save analysis to JSON
    with open("resources/field_analysis_updated.json", "w") as f:
        json.dump(fields, f, indent=2)
        
    print("Analysis complete. Results saved to: resources/field_analysis_updated.json")
    
    # Print checkbox fields and radio groups
    print("\nCheckbox fields and radio groups:")
    for name, info in fields.items():
        if info.get("type") == "/Btn":
            print(f"\n{name}:")
            if "options" in info:
                print(f"  Radio group with options: {info['options']}")
            else:
                print(f"  States: {info.get('states', [])}")
                print(f"  Down states: {info.get('down_states', [])}")
                print(f"  Appearance state: {info.get('appearance_state')}")
                print(f"  Value: {info.get('value')}")
                print(f"  Flags: {info.get('flags')}")

if __name__ == "__main__":
    main()
