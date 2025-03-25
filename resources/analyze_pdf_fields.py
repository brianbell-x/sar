"""
Advanced PDF Form Field Analyzer
Analyzes PDF form fields to extract detailed information about their structure,
properties, and states, with special focus on checkbox fields.
"""

import json
import logging
from typing import Dict, Any, List
import pdfrw

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def analyze_field_properties(field: pdfrw.objects.pdfdict.PdfDict) -> Dict[str, Any]:
    """
    Analyze all properties of a form field.
    
    Args:
        field: PDF form field annotation
        
    Returns:
        Dictionary containing all relevant field properties
    """
    properties = {}
    
    # Basic field properties
    properties["name"] = str(field["/T"]).strip("()")
    properties["type"] = str(field["/FT"]) if "/FT" in field else None
    properties["flags"] = str(field["/Ff"]) if "/Ff" in field else None
    properties["page"] = getattr(field, "page_number", None)
    
    # Get field value if present
    if "/V" in field:
        properties["current_value"] = str(field["/V"])
    
    # Get appearance state if present
    if "/AS" in field:
        properties["appearance_state"] = str(field["/AS"])
    
    # Get default value if present
    if "/DV" in field:
        properties["default_value"] = str(field["/DV"])
    
    # Special handling for text fields
    if properties["type"] == "/Tx":
        if "/MaxLen" in field:
            properties["max_length"] = str(field["/MaxLen"])
    
    # Special handling for checkboxes and radio buttons
    if properties["type"] == "/Btn":
        # Get appearance dictionary
        if "/AP" in field:
            ap_dict = field["/AP"]
            properties["appearance_options"] = {}
            
            # Normal appearance
            if "/N" in ap_dict:
                normal_states = list(ap_dict["/N"].keys())
                if normal_states:
                    properties["states"] = [str(state) for state in normal_states]
            
            # Down appearance (when clicked)
            if "/D" in ap_dict:
                down_states = list(ap_dict["/D"].keys())
                if down_states:
                    properties["down_states"] = [str(state) for state in down_states]
        
        # Check for radio button group
        if "/Parent" in field:
            properties["is_radio_button"] = True
            if "/Opt" in field["/Parent"]:
                properties["radio_options"] = [
                    str(opt) for opt in field["/Parent"]["/Opt"]
                ]
    
    return properties

def get_field_name(annotation: pdfrw.objects.pdfdict.PdfDict) -> str:
    """
    Get the field name, handling special cases for checkbox groups.
    
    Args:
        annotation: PDF form field annotation
        
    Returns:
        Field name with proper suffix for checkbox groups
    """
    # Check for parent field
    parent = annotation.get("/Parent")
    if parent and "/T" in parent:
        base_name = str(parent["/T"]).strip("()")
    else:
        base_name = str(annotation["/T"]).strip("()")
    
    # Handle special cases for checkbox groups
    if base_name in ["item5", "item28", "item29", "item30", "item31", "item38", "item39"]:
        # Get the index within the parent's kids array
        if parent and "/Kids" in parent:
            try:
                idx = parent["/Kids"].index(annotation)
                # Map index to letter suffix
                suffix = chr(ord('a') + idx)
                return f"{base_name}{suffix}"
            except ValueError:
                pass
    
    return base_name

def analyze_pdf_fields(pdf_path: str, output_path: str) -> None:
    """
    Analyze form fields in a PDF and save detailed information to JSON.
    
    Args:
        pdf_path: Path to the PDF file
        output_path: Path to save the analysis JSON
    """
    try:
        # Load PDF
        pdf = pdfrw.PdfReader(pdf_path)
        field_info = {}
        
        # Process each page
        for page_num, page in enumerate(pdf.pages, 1):
            if not page.Annots:
                continue
            
            for annotation in page.Annots:
                if annotation.Subtype == "/Widget":
                    # Get field name with proper handling for checkbox groups
                    field_name = get_field_name(annotation)
                    
                    # Skip empty field names
                    if not field_name:
                        continue
                    
                    # Analyze field
                    field_data = analyze_field_properties(annotation)
                    # Add page number after analysis
                    field_data["page"] = page_num
                    
                    if field_name:
                        field_info[field_name] = field_data
                        logger.debug(f"Analyzed field: {field_name}")
                        
                        # Extra logging for checkbox fields
                        if field_data.get("type") == "/Btn":
                            logger.debug(f"Checkbox details for {field_name}:")
                            logger.debug(f"  States: {field_data.get('states', [])}")
                            logger.debug(f"  Current value: {field_data.get('current_value')}")
                            logger.debug(f"  Appearance state: {field_data.get('appearance_state')}")
        
        # Save analysis to JSON
        with open(output_path, 'w') as f:
            json.dump(field_info, f, indent=2, sort_keys=True)
            
        logger.info(f"Analysis complete. Found {len(field_info)} fields.")
        logger.info(f"Results saved to: {output_path}")
        
        # Print summary of checkbox fields
        checkbox_fields = {
            name: data for name, data in field_info.items() 
            if data.get("type") == "/Btn"
        }
        if checkbox_fields:
            logger.info("\nCheckbox Fields Summary:")
            for name, data in checkbox_fields.items():
                logger.info(f"\nField: {name}")
                logger.info(f"  Page: {data.get('page')}")
                logger.info(f"  States: {data.get('states', [])}")
                logger.info(f"  Current Value: {data.get('current_value')}")
                logger.info(f"  Appearance State: {data.get('appearance_state')}")
                if "down_states" in data:
                    logger.info(f"  Down States: {data['down_states']}")
                if "is_radio_button" in data:
                    logger.info(f"  Radio Options: {data.get('radio_options', [])}")
        
    except Exception as e:
        logger.error(f"Error analyzing PDF: {str(e)}")
        raise

if __name__ == "__main__":
    # Analyze both the template and filled PDF
    analyze_pdf_fields(
        "resources/6710-06.pdf",
        "resources/field_analysis.json"
    )
    
    print("\nAnalyzing filled PDF:")
    analyze_pdf_fields(
        "resources/6710-06_filled_test.pdf",
        "resources/field_analysis_filled.json"
    )
