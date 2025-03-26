"""
PDF Filler for SAR Form 6710-06 using a template with DESCRIPTIVE field names.
Assumes the PDF template has already been processed by update_field_names.py.
"""

import logging
from typing import Dict, Any, Optional
import pdfrw

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define standard checkbox states used by pdfrw
CHECKBOX_CHECK_STATE = pdfrw.PdfName('Yes') # Common state for checked
CHECKBOX_OFF_STATE = pdfrw.PdfName('Off') # Common state for unchecked

def fill_checkbox(annotation: pdfrw.PdfDict, value: bool) -> None:
    """
    Fill a checkbox field. Assumes standard '/Yes' and '/Off' states.
    Updates the Value (/V) and Appearance State (/AS).

    Args:
        annotation: PDF form field annotation (widget).
        value: Boolean indicating if checkbox should be checked (True) or unchecked (False).
    """
    try:
        state_to_set = CHECKBOX_CHECK_STATE if value else CHECKBOX_OFF_STATE
        current_name = annotation.get('/T') # For logging

        # Check if the annotation already has Appearance States defined
        ap_dict = annotation.get('/AP')
        if not ap_dict or not isinstance(ap_dict, pdfrw.PdfDict):
            # If no appearance dictionary exists, we can't reliably set visual state.
            # We can still try setting the value, but it might not render correctly.
            logger.warning(f"Checkbox '{current_name}' lacks Appearance Dictionary (/AP). Setting value only.")
            annotation.update({
                pdfrw.PdfName('V'): state_to_set
            })
            return

        # Ensure the target state exists in the Normal (/N) appearance dictionary.
        # PDFs often require this for the state to be valid.
        normal_appearances = ap_dict.get('/N')
        if not normal_appearances or not isinstance(normal_appearances, pdfrw.PdfDict):
             logger.warning(f"Checkbox '{current_name}' lacks Normal Appearance Dictionary (/N). Setting value only.")
             annotation.update({
                pdfrw.PdfName('V'): state_to_set
             })
             return

        # Check if the required state ('Yes' or 'Off') is defined within /N
        # Some PDFs might use different names (e.g., '/On'). This basic filler assumes '/Yes'.
        if CHECKBOX_CHECK_STATE not in normal_appearances:
             logger.warning(f"Checkbox '{current_name}' /AP/N does not contain state '{CHECKBOX_CHECK_STATE}'. Check PDF structure.")
        if CHECKBOX_OFF_STATE not in normal_appearances:
             logger.warning(f"Checkbox '{current_name}' /AP/N does not contain state '{CHECKBOX_OFF_STATE}'. Check PDF structure.")


        # Update Value (/V) and Appearance State (/AS)
        annotation.update({
            pdfrw.PdfName('V'): state_to_set,
            pdfrw.PdfName('AS'): state_to_set
        })
        # Optional: Force appearance update flag if needed, but usually /AS is sufficient
        # annotation[pdfrw.PdfName('Ff')] = pdfrw.PdfObject('0') # Reset flags if necessary

        logger.debug(f"Set checkbox '{current_name}' to state: {state_to_set}")

    except Exception as e:
        current_name = annotation.get('/T', 'UNKNOWN_FIELD')
        logger.error(f"Failed to set checkbox '{current_name}': {e}", exc_info=True)
        # Decide if you want to re-raise or just log


def fill_text(annotation: pdfrw.PdfDict, value: Any, max_length: Optional[int] = None) -> None:
    """
    Fill a text field (/Tx) with optional max length constraint.
    Converts value to string.

    Args:
        annotation: PDF form field annotation (widget).
        value: The value to fill (will be converted to string).
        max_length: Optional maximum length for the field.
    """
    try:
        str_value = str(value) if value is not None else ''
        if max_length is not None and max_length > 0:
            str_value = str_value[:max_length]

        annotation.update({
            pdfrw.PdfName('V'): pdfrw.PdfString.encode(str_value)
        })
        # Optional: Update Appearance Stream (/AP) if needed for complex fields,
        # but pdfrw often handles simple text field appearances automatically.
        # annotation.update({ pdfrw.PdfName('AP'): '' }) # Force refresh? Risky.

    except Exception as e:
        current_name = annotation.get('/T', 'UNKNOWN_FIELD')
        logger.error(f"Failed to set text field '{current_name}': {e}", exc_info=True)


def fill_sar_pdf(data: Dict[str, Any], template_path: str, output_path: str) -> None:
    """
    Fills a SAR PDF form using a template with *descriptive* field names.

    Args:
        data: Dictionary where keys are the descriptive field names (matching the PDF)
              and values are the data to fill.
        template_path: Path to the modified PDF template (e.g., 6710-06_descriptive.pdf).
        output_path: Path where the filled PDF will be saved.
    """
    try:
        logger.info(f"Loading descriptive template PDF: {template_path}")
        template_pdf = pdfrw.PdfReader(template_path)
        template_pdf.Info.Creator = pdfrw.PdfString.encode("SAR AI PDF Filler") # Optional: Set creator metadata

        processed_fields = set()

        for page_num, page in enumerate(template_pdf.pages, 1):
            if not page.Annots:
                continue

            logger.debug(f"Processing Page {page_num}...")
            for annotation in page.Annots:
                if annotation.Subtype != '/Widget' or '/T' not in annotation:
                    continue

                try:
                    # Field name is expected to be the descriptive name now
                    field_name_obj = annotation['/T']
                    if isinstance(field_name_obj, pdfrw.PdfString):
                         field_name = field_name_obj.decode('utf-8', errors='ignore')
                    else:
                         field_name = str(field_name_obj).strip("()") # Should ideally be PdfString after renaming

                    if not field_name or field_name == "None":
                        continue

                    processed_fields.add(field_name)

                    # Check if data exists for this field
                    if field_name in data:
                        value = data[field_name]
                        field_type = str(annotation.get('/FT', '')) # Get field type

                        if field_type == '/Btn': # Checkbox or Radio Button
                            # Assuming boolean values for checkboxes from Agent 5 output
                            if isinstance(value, bool):
                                 fill_checkbox(annotation, value)
                            else:
                                 logger.warning(f"Expected boolean value for button '{field_name}', got {type(value)}. Skipping.")
                        elif field_type == '/Tx': # Text Field
                            max_len = int(annotation.get('/MaxLen', 0)) if '/MaxLen' in annotation else None
                            fill_text(annotation, value, max_len)
                        elif field_type == '/Ch': # Choice Field (Dropdown/List)
                             # Requires specific handling based on /Opt values if needed
                             logger.info(f"Choice field '{field_name}' found. Basic text fill attempted. Review if dropdown selection is needed.")
                             fill_text(annotation, value) # Treat as text for now
                        else:
                             logger.warning(f"Unsupported field type '{field_type}' for field '{field_name}'. Skipping.")

                    else:
                        # Log fields in the PDF that weren't provided in the data
                        logger.debug(f"No data provided for PDF field: '{field_name}'")
                        # Handle default values if needed, e.g., clear field?
                        # annotation.update({ pdfrw.PdfName('V'): pdfrw.PdfString('') })


                except Exception as e:
                    field_name = annotation.get('/T', 'UNKNOWN_FIELD')
                    logger.error(f"Error processing field '{field_name}' on page {page_num}: {e}", exc_info=True)


        # Log fields in the data that were not found in the PDF
        data_keys = set(data.keys())
        unprocessed_data = data_keys - processed_fields
        if unprocessed_data:
            logger.warning(f"Data provided for fields not found or processed in PDF: {sorted(list(unprocessed_data))}")

        # Mark fields as needing appearance update
        template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))

        logger.info(f"Writing filled PDF to: {output_path}")
        pdfrw.PdfWriter().write(output_path, template_pdf)
        logger.info(f"Successfully wrote filled PDF: {output_path}")

    except FileNotFoundError:
         logger.error(f"Template PDF not found at '{template_path}'. Ensure it exists and the path is correct.")
         raise
    except Exception as e:
        logger.error(f"General error filling PDF: {e}", exc_info=True)
        raise

# Keep the test data generation and __main__ block for standalone testing
# but ensure it uses the descriptive field names now.

def create_test_data_descriptive() -> Dict:
    """Create test data using DESCRIPTIVE field names."""
    # This requires updating the keys from create_test_data to match FIELD_MAPPING values
    return {
        # Part I fields (using descriptive names)
        "corrects_prior_report": True,
        "financial_institution_name": "First National Bank of Testing",
        "financial_institution_ein": "123456789",
        "financial_institution_address": "789 Financial Plaza, Suite 1000",
        "regulator_federal_reserve": True,
        "regulator_fdic": False,
        "regulator_ncua": False,
        "regulator_occ": False,
        "regulator_ots": False,
        "financial_institution_city": "Chicago",
        "financial_institution_state_char1": "I",
        "financial_institution_state_char2": "L",
        "financial_institution_zip_1": "6",
        "financial_institution_zip_2": "0",
        "financial_institution_zip_3": "6",
        "financial_institution_zip_4": "0",
        "financial_institution_zip_5": "1",
        "financial_institution_zip_plus4_1": "1", # Example +4
        "financial_institution_zip_plus4_2": "2",
        "financial_institution_zip_plus4_3": "3",
        "financial_institution_zip_plus4_4": "4",
        "branch_address": "456 Branch Street",
        "multiple_branches_involved": False,
        "branch_city": "Springfield",
        "branch_state_char1": "I",
        "branch_state_char2": "L",
        "branch_zip_1": "6",
        "branch_zip_2": "2",
        "branch_zip_3": "7",
        "branch_zip_4": "0",
        "branch_zip_5": "1",
        "branch_zip_plus4_1": "", # Leave empty if not applicable
        "branch_zip_plus4_2": "",
        "branch_zip_plus4_3": "",
        "branch_zip_plus4_4": "",
        "institution_closed_date_month": "", # Leave empty if not closed
        "institution_closed_date_day": "",
        "institution_closed_date_year": "",
        "affected_account_1_number": "ACC1234567890",
        "affected_account_1_closed_yes": False,
        "affected_account_1_closed_no": True, # Explicitly set 'No' if needed by form logic
        "affected_account_2_number": "ACC0987654321",
        "affected_account_2_closed_yes": True,
        "affected_account_2_closed_no": False, # Explicitly set 'No' if needed

        # Part II - Suspect Information
        "suspect_info_unavailable": False,
        "suspect_last_name_or_entity": "Doe",
        "suspect_first_name": "John",
        "suspect_middle_name": "X",
        "suspect_address": "123 Anonymity Lane",
        "suspect_ssn_ein_tin": "987654321", # Should be SSN/EIN/ITIN
        "suspect_city": "Metropolis",
        "suspect_state_char1": "N",
        "suspect_state_char2": "Y",
        "suspect_zip_1": "1",
        "suspect_zip_2": "0",
        "suspect_zip_3": "0",
        "suspect_zip_4": "0",
        "suspect_zip_5": "1",
        "suspect_zip_plus4_1": "5",
        "suspect_zip_plus4_2": "6",
        "suspect_zip_plus4_3": "7",
        "suspect_zip_plus4_4": "8",
        "suspect_country": "USA",
        "suspect_phone_residence_area_code": "212",
        "suspect_phone_residence_number": "5550100",
        "suspect_phone_work_area_code": "212",
        "suspect_phone_work_number": "5550200",
        "suspect_occupation_or_business": "Consultant",
        "suspect_dob_month": "01",
        "suspect_dob_day": "15",
        "suspect_dob_year": "1980",
        "suspect_admission_yes": False,
        "suspect_admission_no": True,
        "suspect_id_drivers_license": True,
        "suspect_id_passport": False,
        "suspect_id_alien_registration": False,
        "suspect_id_other": False,
        "suspect_id_number_part1": "D12345678", # Example ID number parts
        "suspect_id_number_part2": "",
        "suspect_id_issuing_authority": "NY", # State/Country
        "relationship_customer": True,
        "relationship_accountant": False, # Mark others explicitly false if needed
        # ... add all other relationship checkboxes as False ...
        "relationship_other": False,
        "relationship_other_description": "",
        "insider_relationship_yes": False,
        "insider_relationship_no": True,
        # ... leave insider status fields blank if not applicable ...

        # Part III - Suspicious Activity Information
        "activity_date_from_month": "01",
        "activity_date_from_day": "01",
        "activity_date_from_year": "2024",
        "activity_date_to_month": "03",
        "activity_date_to_day": "31",
        "activity_date_to_year": "2024",
        "total_amount_digit11": "1", # Example: 1,234,567.00 -> 123456700
        "total_amount_digit10": "2",
        "total_amount_digit9": "3",
        "total_amount_digit8": "4",
        "total_amount_digit7": "5",
        "total_amount_digit6": "6",
        "total_amount_digit5": "7",
        "total_amount_digit4": "0", # Cents
        "total_amount_digit3": "0", # Cents
        "total_amount_digit2": "", # Leading zeros often omitted or handled by PDF
        "total_amount_digit1": "",
        "activity_bsa_structuring_money_laundering": True,
        "activity_wire_transfer_fraud": True,
        "activity_other": True,
        "activity_other_description": "Unusual pattern of international wires",
        # ... set other activity checkboxes to False ...
        "loss_amount_digit8": "0", # Example loss $5000.00 -> 500000
        "loss_amount_digit7": "5",
        "loss_amount_digit6": "0",
        "loss_amount_digit5": "0",
        "loss_amount_digit4": "0",
        "loss_amount_digit3": "0", # Cents
        "loss_amount_digit2": "0", # Cents
        "loss_amount_digit1": "",
        "recovery_amount_digit9": "", # Example recovery $100.00 -> 10000
        "recovery_amount_digit8": "",
        "recovery_amount_digit7": "",
        "recovery_amount_digit6": "1",
        "recovery_amount_digit5": "0",
        "recovery_amount_digit4": "0",
        "recovery_amount_digit3": "0", # Cents
        "recovery_amount_digit2": "0", # Cents
        # recovery_amount_digit1 is missing from mapping, check PDF/mapping script
        "material_impact_yes": False,
        "material_impact_no": True,
        "bonding_company_notified_yes": False,
        "bonding_company_notified_no": True,
        "notified_fbi": True,
        "notified_dea": False, # etc...
        "agency_name_provided": True,
        "law_enforcement_agency_name": "FBI - New York Field Office",
        "law_enforcement_contact_1_name": "Agent Smith",
        "law_enforcement_contact_1_phone_area": "212",
        "law_enforcement_contact_1_phone_number": "5551000",

        # Part IV - Contact for Assistance
        "contact_last_name": "Compliance",
        "contact_first_name": "Officer",
        "contact_middle_name": "",
        "contact_title": "AML Compliance Lead",
        "contact_phone_area_code": "312",
        "contact_phone_number": "5552000",
        "date_prepared_month": "04",
        "date_prepared_day": "15",
        "date_prepared_year": "2024",
        "filing_agency_name": "First National Bank of Testing",

        # Part V - Narrative Text (using the mapped descriptive name)
        "narrative_text": ("Narrative Example: WHO: John Doe (Customer ACC1234567890). "
                         "WHAT: Received multiple international wire transfers from high-risk jurisdictions "
                         "followed by immediate withdrawal attempts via ATM and cashier's checks inconsistent with "
                         "customer profile. Amounts structured just below reporting thresholds. "
                         "WHEN: Jan 1 2024 - Mar 31 2024. "
                         "WHERE: Transfers originated from Country X, Y; Withdrawals attempted at Main Branch and ATM Network Z. "
                         "WHY: Pattern suggests potential money laundering or layering activity. No legitimate business purpose provided upon inquiry. "
                         "HOW: International SWIFT transfers; attempted withdrawals via cashier's check and ATM."),

        # Other potential fields (buttons, display text) - usually not filled via data
        # "form_name_display": "6710-06", # Probably read-only
    }


if __name__ == "__main__":
    # --- Standalone Test ---
    # 1. Ensure you have run `update_field_names.py` first to create the descriptive PDF.
    #    Example: python resources/update_field_names.py --input resources/6710-06.pdf --output resources/6710-06_descriptive.pdf
    # 2. Make sure the output path for the filled PDF exists or can be created.

    descriptive_template = "resources/6710-06_descriptive.pdf" # Path to the PDF generated by update_field_names.py
    test_output_path = "output/sar_filled_descriptive_test.pdf" # Output path for this test

    import os
    if not os.path.exists(descriptive_template):
        print(f"ERROR: Descriptive template PDF not found at '{descriptive_template}'.")
        print("Please run 'python resources/update_field_names.py --input resources/6710-06.pdf --output resources/6710-06_descriptive.pdf' first.")
    else:
        print("Creating test data with descriptive names...")
        test_data = create_test_data_descriptive()

        # Ensure output directory exists
        os.makedirs(os.path.dirname(test_output_path), exist_ok=True)

        print(f"Filling PDF template '{descriptive_template}'...")
        try:
            fill_sar_pdf(
                data=test_data,
                template_path=descriptive_template,
                output_path=test_output_path
            )
            print(f"\nTest successful! Filled PDF saved to: {test_output_path}")
        except Exception as e:
            print(f"\nTest failed during PDF filling: {e}")
            logging.exception("PDF filling error:")