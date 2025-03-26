"""
Script to update field names in the PDF to be more descriptive and human-readable.
"""

import json
import pdfrw
import logging
import re
import shutil
from typing import Dict, Optional
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_descriptive_field_names() -> Dict[str, str]:
    """Create mapping of original PDF field names to descriptive names."""
    return {
        # Part I: Reporting Financial Institution Information
        "item1": "corrects_prior_report",
        "item2": "financial_institution_name",
        "item3": "financial_institution_ein",
        "item4": "financial_institution_address",
        "item5a": "regulator_federal_reserve",
        "item5b": "regulator_fdic",
        "item5c": "regulator_ncua",
        "item5d": "regulator_occ",
        "item5e": "regulator_ots",
        "item6": "financial_institution_city",
        "item7": "financial_institution_state_char1",
        "item7-1": "financial_institution_state_char2",
        "item8-1": "financial_institution_zip_1",
        "item8-2": "financial_institution_zip_2",
        "item8-3": "financial_institution_zip_3",
        "item8-4": "financial_institution_zip_4",
        "item8-5": "financial_institution_zip_5",
        "item8-6": "financial_institution_zip_plus4_1",
        "item8-7": "financial_institution_zip_plus4_2",
        "item8-8": "financial_institution_zip_plus4_3",
        "item8-9": "financial_institution_zip_plus4_4",
        "item9": "branch_address",
        "item9-1": "multiple_branches_involved",
        "item10": "branch_city",
        "item11-1": "branch_state_char1",
        "item11-2": "branch_state_char2",
        "item12-1": "branch_zip_1",
        "item12-2": "branch_zip_2",
        "item12-3": "branch_zip_3",
        "item12-4": "branch_zip_4",
        "item12-5": "branch_zip_5",
        "item12-6": "branch_zip_plus4_1",
        "item12-7": "branch_zip_plus4_2",
        "item12-8": "branch_zip_plus4_3",
        "item12-9": "branch_zip_plus4_4",
        "item13-1": "institution_closed_date_month",
        "item13-2": "institution_closed_date_day",
        "item13-3": "institution_closed_date_year",
        "item14a": "affected_account_1_number",
        "item14a-1": "affected_account_1_closed_yes",
        "item14a-2": "affected_account_1_closed_no",
        "item14b": "affected_account_2_number",
        "item14b-1": "affected_account_2_closed_yes",
        "item14b-2": "affected_account_2_closed_no",
        "item14c": "affected_account_3_number",
        "item14c-1": "affected_account_3_closed_yes",
        "item14c-2": "affected_account_3_closed_no",
        "item14d": "affected_account_4_number",
        "item14d-1": "affected_account_4_closed_yes",
        "item14d-2": "affected_account_4_closed_no",

        # Part II: Suspect Information
        "itemPII": "suspect_info_unavailable",
        "item15": "suspect_last_name_or_entity",
        "item16": "suspect_first_name",
        "item17": "suspect_middle_name",
        "item18": "suspect_address",
        "item19": "suspect_ssn_ein_tin",
        "item20": "suspect_city",
        "item21a": "suspect_state_char1",
        "item21b": "suspect_state_char2",
        "item22-1": "suspect_zip_1",
        "item22-2": "suspect_zip_2",
        "item22-3": "suspect_zip_3",
        "item22-4": "suspect_zip_4",
        "item22-5": "suspect_zip_5",
        "item22-6": "suspect_zip_plus4_1",
        "ITEM22-7": "suspect_zip_plus4_2",
        "ITEM22-8": "suspect_zip_plus4_3",
        "item22-9": "suspect_zip_plus4_4",
        "item23": "suspect_country",
        "item24-1": "suspect_phone_residence_area_code",
        "item24-2": "suspect_phone_residence_number",
        "item25-1": "suspect_phone_work_area_code",
        "item25-2": "suspect_phone_work_number",
        "item26": "suspect_occupation_or_business",
        "item27-1": "suspect_dob_month",
        "item27-2": "suspect_dob_day",
        "item27-3": "suspect_dob_year",
        "item28a": "suspect_admission_yes",
        "item28b": "suspect_admission_no",
        "item29a": "suspect_id_drivers_license",
        "item29b": "suspect_id_passport",
        "item29c": "suspect_id_alien_registration",
        "item29d": "suspect_id_other",
        "item29-1": "suspect_id_number_part1",
        "item29-2": "suspect_id_number_part2",
        "item29-3": "suspect_id_issuing_authority",
        "item30a": "relationship_accountant",
        "item30b": "relationship_agent",
        "item30c": "relationship_appraiser",
        "item30d": "relationship_attorney",
        "item30e": "relationship_borrower",
        "item30f": "relationship_broker",
        "item30g": "relationship_customer",
        "item30h": "relationship_director",
        "item30i": "relationship_employee",
        "item30j": "relationship_officer",
        "item30k": "relationship_shareholder",
        "item30l": "relationship_other",
        "item30-1": "relationship_other_description",
        "item31a": "insider_relationship_yes",
        "item31b": "insider_relationship_no",
        "item31c": "insider_status_still_employed",
        "item31d": "insider_status_suspended",
        "item31e": "insider_status_terminated",
        "item31f": "insider_status_resigned",
        "item32-1": "insider_status_date_month",
        "item32-2": "insider_status_date_day",
        "item32-3": "insider_status_date_year",

        # Part III: Suspicious Activity Information
        "item33-1": "activity_date_from_month",
        "item33-2": "activity_date_from_day",
        "item33-3": "activity_date_from_year",
        "item33-4": "activity_date_to_month",
        "item33-5": "activity_date_to_day",
        "item33-6": "activity_date_to_year",
        "item34-1": "total_amount_digit1",
        "item34-2": "total_amount_digit2",
        "item34-3": "total_amount_digit3",
        "item34-4": "total_amount_digit4",
        "item34-5": "total_amount_digit5",
        "item34-6": "total_amount_digit6",
        "item34-7": "total_amount_digit7",
        "item34-8": "total_amount_digit8",
        "item34-9": "total_amount_digit9",
        "item34-10": "total_amount_digit10",
        "item34-11": "total_amount_digit11",
        "item35a": "activity_bsa_structuring_money_laundering",
        "item35b": "activity_bribery_gratuity",
        "item35c": "activity_check_fraud",
        "item35d": "activity_check_kiting",
        "item35e": "activity_commercial_loan_fraud",
        "item35f": "activity_computer_intrusion",
        "item35g": "activity_consumer_loan_fraud",
        "item35h": "activity_counterfeit_check",
        "item35i": "activity_counterfeit_credit_debit_card",
        "item35j": "activity_counterfeit_instrument_other",
        "item35k": "activity_credit_card_fraud",
        "item35l": "activity_debit_card_fraud",
        "item35m": "activity_defalcation_embezzlement",
        "item35n": "activity_false_statement",
        "item35o": "activity_misuse_position_self_dealing",
        "item35p": "activity_mortgage_loan_fraud",
        "item35q": "activity_mysterious_disappearance",
        "item35r": "activity_wire_transfer_fraud",
        "item35s": "activity_other",
        "item35s-1": "activity_other_description",
        "item35t": "activity_terrorist_financing",
        "item35u": "activity_identity_theft",
        "item36-1": "loss_amount_digit1",
        "item36-2": "loss_amount_digit2",
        "item36-3": "loss_amount_digit3",
        "item36-4": "loss_amount_digit4",
        "item36-5": "loss_amount_digit5",
        "item36-6": "loss_amount_digit6",
        "item36-7": "loss_amount_digit7",
        "item36-8": "loss_amount_digit8",
        "item37-1": "recovery_amount_digit1",
        "item37-2": "recovery_amount_digit2",
        "37-3": "recovery_amount_digit3",
        "item37-4": "recovery_amount_digit4",
        "item37-5": "recovery_amount_digit5",
        "item37-6": "recovery_amount_digit6",
        "item37-7": "recovery_amount_digit7",
        "item37-8": "recovery_amount_digit8",
        "item37-9": "recovery_amount_digit9",
        "item38a": "material_impact_yes",
        "item38b": "material_impact_no",
        "item39a": "bonding_company_notified_yes",
        "item39b": "bonding_company_notified_no",
        "item40a": "notified_dea",
        "item40b": "notified_fbi",
        "item40c": "notified_irs",
        "item40d": "notified_postal_inspection",
        "item40e": "notified_secret_service",
        "item40f": "notified_us_customs",
        "item40g": "notified_other_federal",
        "item40h": "notified_state",
        "item40i": "notified_local",
        "item40j": "agency_name_provided",
        "item40j-1": "law_enforcement_agency_name",
        "item41": "law_enforcement_contact_1_name",
        "item42-1": "law_enforcement_contact_1_phone_area",
        "item42-2": "law_enforcement_contact_1_phone_number",
        "item43": "law_enforcement_contact_2_name",
        "item44-1": "law_enforcement_contact_2_phone_area",
        "item44-2": "law_enforcement_contact_2_phone_number",

        # Part IV: Contact for Assistance
        "item45": "contact_last_name",
        "item46": "contact_first_name",
        "item47": "contact_middle_name",
        "item48": "contact_title",
        "item49-1": "contact_phone_area_code",
        "item49-2": "contact_phone_number",
        "item50-1": "date_prepared_month",
        "item50-2": "date_prepared_day",
        "item50-3": "date_prepared_year",
        "item51": "filing_agency_name",

        # Form metadata
        "FormName": "form_name",
        "Body": "body_section",
        "Header": "header_section",
        "Help": "help_section",
        "Open": "open_section",
        "POC": "poc_section",
        "Refresh": "refresh_section",
        "Save": "save_section"
    }

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

def update_pdf_field_names(pdf_path: str, output_path: str, field_mappings: Dict[str, str]) -> None:
    """Update field names in the PDF with descriptive names."""
    # Create backup of original PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{pdf_path}.{timestamp}.backup"
    shutil.copy2(pdf_path, backup_path)
    logger.info(f"Created backup of original PDF at: {backup_path}")
    
    # Read the PDF
    pdf = pdfrw.PdfReader(pdf_path)
    
    # Track unmapped fields
    unmapped_fields = set()
    
    # Update field names
    for page in pdf.pages:
        if not page.Annots:
            continue
            
        for annotation in page.Annots:
            if annotation.Subtype == "/Widget":
                field_name = str(annotation["/T"]).strip("()")
                if not field_name:
                    continue
                
                # Get base name for radio buttons (e.g. "item5" from "item5.0")
                base_name = re.match(r'([^.]+)', field_name).group(1)
                
                if base_name in field_mappings:
                    new_name = field_mappings[base_name]
                    # For radio buttons, preserve the original suffix
                    suffix_match = re.search(r'(\.\d+)$', field_name)
                    if suffix_match:
                        new_name += suffix_match.group(1)
                    
                    # Update the field name
                    annotation[pdfrw.objects.pdfname.PdfName('T')] = pdfrw.objects.pdfstring.PdfString.encode(new_name)
                    logger.debug(f"Renamed field '{field_name}' to '{new_name}'")
                else:
                    unmapped_fields.add(base_name)
                    logger.warning(f"No mapping found for field: {base_name}")
    
    # Save the modified PDF
    pdfrw.PdfWriter().write(output_path, pdf)
    logger.info(f"Saved modified PDF with updated field names to: {output_path}")
    
    # Report unmapped fields
    if unmapped_fields:
        logger.warning("\nFields without mappings:")
        for field in sorted(unmapped_fields):
            logger.warning(f"  - {field}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Analyze and update PDF form field names")
    parser.add_argument("--analyze-only", action="store_true", help="Only analyze fields without updating names")
    parser.add_argument("--input", default="resources/6710-06.pdf", help="Input PDF path")
    parser.add_argument("--output", help="Output PDF path (for renaming)")
    args = parser.parse_args()
    
    # Analyze fields
    fields = analyze_pdf_fields(args.input)
    
    # Save analysis to JSON
    analysis_path = "resources/field_analysis_updated.json"
    with open(analysis_path, "w") as f:
        json.dump(fields, f, indent=2)
    logger.info(f"Analysis saved to: {analysis_path}")
    
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
    
    # Update field names if requested
    if not args.analyze_only:
        if not args.output:
            args.output = args.input.replace(".pdf", "_renamed.pdf")
        
        field_mappings = create_descriptive_field_names()
        update_pdf_field_names(args.input, args.output, field_mappings)

if __name__ == "__main__":
    main()
