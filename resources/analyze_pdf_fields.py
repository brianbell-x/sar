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
logging.basicConfig(level=logging.INFO)
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
    for key in field.keys():
        try:
            # Decode if necessary (Names, Strings might be bytes)
            # pdfrw often handles this, but explicit decoding might be needed sometimes
            value = field[key]
            prop_name = key.decode('utf-8') if isinstance(key, bytes) else str(key)
            
            # Basic representation for logging/debugging
            # For complex types like nested dicts/arrays, you might want deeper inspection
            if isinstance(value, pdfrw.objects.pdfdict.PdfDict):
                properties[prop_name] = f"Dict with keys: {list(value.keys())}"
            elif isinstance(value, pdfrw.objects.pdfarray.PdfArray):
                 properties[prop_name] = f"Array: {value}" # pdfrw makes arrays list-like
            elif isinstance(value, pdfrw.objects.pdfname.BasePdfName):
                 properties[prop_name] = str(value) # Get the name string e.g. '/Yes'
            elif isinstance(value, pdfrw.objects.pdfstring.PdfString):
                 properties[prop_name] = value.decode() # Decode PDF string
            else:
                 properties[prop_name] = repr(value) # General representation

        except Exception as e:
            logger.warning(f"Could not process key {key}: {e}")
            properties[str(key)] = f"<Error processing: {e}>"

    # Add the specific ones you already had for clarity, possibly overwriting
    # the generic ones if needed for specific formatting
    if "/T" in field:
        properties["/T (Name)"] = str(field["/T"]).strip("()")
    if "/FT" in field:
        properties["/FT (Type)"] = str(field["/FT"])
    if "/Ff" in field:
        properties["/Ff (Flags)"] = int(field["/Ff"]) # Keep as int for bitwise checks
    if "/V" in field:
         # Specific handling for Value as it's often important
         v_val = field["/V"]
         if isinstance(v_val, pdfrw.objects.pdfname.BasePdfName):
             properties["/V (Value)"] = str(v_val)
         elif isinstance(v_val, pdfrw.objects.pdfstring.PdfString):
             properties["/V (Value)"] = v_val.decode()
         else:
              properties["/V (Value)"] = repr(v_val)
    if "/AS" in field:
        properties["/AS (Appearance State)"] = str(field["/AS"])

    properties["page_number"] = getattr(field, "page_number", None) # Library specific

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
        
        # Save analysis to JSON
        with open(output_path, 'w') as f:
            json.dump(field_info, f, indent=2, sort_keys=True)
            
        logger.info(f"Analysis complete. Found {len(field_info)} fields.")
        logger.info(f"Results saved to: {output_path}")
        
        # Brief summary of checkbox fields
        checkbox_fields = {
            name: data for name, data in field_info.items() 
            if data.get("/FT (Type)") == "/Btn"
        }
        if checkbox_fields:
            logger.info(f"\nFound {len(checkbox_fields)} checkbox/radio button fields")
        
    except Exception as e:
        logger.error(f"Error analyzing PDF: {str(e)}")
        raise

if __name__ == "__main__":
    # Analyze both the template and filled PDF
    analyze_pdf_fields(
        "resources/6710-06_renamed.pdf",
        "resources/field_analysis.json"
    )
