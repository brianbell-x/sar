"""
PDF Filler for SAR Form 6710-06 based on exact field analysis.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Optional
import pdfrw

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_field_info(json_path: str) -> Dict:
    """Load field information from analysis JSON."""
    with open(json_path) as f:
        return json.load(f)

def fill_checkbox(annotation: pdfrw.objects.pdfdict.PdfDict, value: bool, field_info: Dict) -> None:
    """
    Fill a checkbox field using field-specific state information.
    
    Args:
        annotation: PDF form field annotation
        value: Boolean indicating if checkbox should be checked
        field_info: Field information from analysis JSON containing states
    """
    try:
        # Create PdfName objects for states
        check_state = pdfrw.PdfName('Yes')
        off_state = pdfrw.PdfName('Off')
        
        # Create PdfName objects for dictionary keys
        AP = pdfrw.PdfName('AP')
        N = pdfrw.PdfName('N')
        D = pdfrw.PdfName('D')
        
        # Get or create appearance dictionary
        if AP not in annotation:
            annotation[AP] = pdfrw.PdfDict()
            
        # Preserve existing appearance dictionaries if they exist
        n_dict = annotation[AP][N] if N in annotation[AP] else pdfrw.PdfDict()
        d_dict = annotation[AP][D] if D in annotation[AP] else pdfrw.PdfDict()
        
        # Ensure both states exist in both normal and down dictionaries
        if check_state not in n_dict:
            n_dict[check_state] = annotation[AP][N][check_state] if N in annotation[AP] and check_state in annotation[AP][N] else pdfrw.PdfDict()
        if off_state not in n_dict:
            n_dict[off_state] = annotation[AP][N][off_state] if N in annotation[AP] and off_state in annotation[AP][N] else pdfrw.PdfDict()
            
        if check_state not in d_dict:
            d_dict[check_state] = annotation[AP][D][check_state] if D in annotation[AP] and check_state in annotation[AP][D] else pdfrw.PdfDict()
        if off_state not in d_dict:
            d_dict[off_state] = annotation[AP][D][off_state] if D in annotation[AP] and off_state in annotation[AP][D] else pdfrw.PdfDict()
        
        # Update appearance dictionary
        annotation[AP][N] = n_dict
        annotation[AP][D] = d_dict
        
        # Set value and appearance state
        state = check_state if value else off_state
        annotation.update(
            pdfrw.PdfDict(
                V=state,
                AS=state,
                Ff=pdfrw.PdfObject('0')  # Standard checkbox flags
            )
        )
        
        logger.debug(f"Set checkbox {field_info['name']} to {check_state if value else off_state}")
        
    except Exception as e:
        logger.error(f"Failed to set checkbox {field_info['name']}: {str(e)}")
        raise

def fill_text(annotation: pdfrw.objects.pdfdict.PdfDict, value: str, max_length: Optional[int] = None) -> None:
    """Fill a text field with optional max length constraint."""
    if max_length:
        value = str(value)[:max_length]
    annotation.update(pdfrw.PdfDict(V=str(value)))

def fill_sar_pdf(data: Dict, template_path: str, output_path: str, field_info_path: str) -> None:
    """
    Fill SAR PDF form using exact field information.
    
    Args:
        data: Dictionary containing test data for all fields
        template_path: Path to blank PDF template
        output_path: Path for filled PDF
        field_info_path: Path to field analysis JSON
    """
    try:
        # Load field information
        field_info = load_field_info(field_info_path)
        
        # Load template
        template_pdf = pdfrw.PdfReader(template_path)
        
        # Process each page
        for page in template_pdf.pages:
            if not page.Annots:
                continue
                
            for annotation in page.Annots:
                if annotation.Subtype == "/Widget":
                    field_name = str(annotation["/T"]).strip("()")
                    if not field_name or field_name == "None":
                        continue
                    
                    # Find the descriptive field name that maps to this original field name
                    descriptive_name = None
                    for desc_name, info in field_info.items():
                        if info.get("original_name") == field_name:
                            descriptive_name = desc_name
                            break
                    
                    if not descriptive_name:
                        # Only log warning for non-None fields that should have mappings
                        if field_name != "None":
                            logger.warning(f"No descriptive name found for field: {field_name}")
                        continue
                        
                    if descriptive_name not in data:
                        # Use default value if present
                        if "default_value" in field_info[descriptive_name]:
                            fill_text(annotation, field_info[descriptive_name]["default_value"])
                        continue
                        
                    value = data[descriptive_name]
                    
                    # Handle field based on type
                    if field_info[descriptive_name].get("type") == "/Btn":
                        fill_checkbox(annotation, value, field_info[descriptive_name])
                    elif field_info[descriptive_name].get("type") == "/Tx":
                        fill_text(annotation, value, int(field_info[descriptive_name]["max_length"]) if "max_length" in field_info[descriptive_name] else None)
        
        # Write filled PDF
        pdfrw.PdfWriter().write(output_path, template_pdf)
        logger.info(f"Successfully wrote filled PDF to: {output_path}")
        
    except Exception as e:
        logger.error(f"Error filling PDF: {str(e)}")
        raise

def create_test_data() -> Dict:
    """Create test data for all fields."""
    return {
        # Form metadata
        "form_name_text": "6710-06",
        
        # Part I fields
        "p1_corrects_prior_report_checkbox": True,
        "p1_institution_name_text": "First National Bank of Testing",
        "p1_institution_ein_text": "123456789",
        "p1_institution_address_text": "789 Financial Plaza, Suite 1000",
        
        # Primary Federal Regulator
        "p1_regulator_federal_reserve_checkbox": True,
        "p1_regulator_fdic_checkbox": False,
        "p1_regulator_ncua_checkbox": False,
        "p1_regulator_occ_checkbox": False,
        "p1_regulator_ots_checkbox": False,
        
        "p1_institution_city_text": "Chicago",
        "p1_institution_state_1_text": "I",
        "p1_institution_state_2_text": "L",
        
        # Institution zip code
        "p1_institution_zip_1_text": "6",
        "p1_institution_zip_2_text": "0",
        "p1_institution_zip_3_text": "6",
        "p1_institution_zip_4_text": "0",
        "p1_institution_zip_5_text": "1",
        "p1_institution_zip_6_text": "0",
        "p1_institution_zip_7_text": "0",
        "p1_institution_zip_8_text": "0",
        "p1_institution_zip_9_text": "0",
        
        "p1_branch_address_text": "456 Branch Street",
        "p1_multiple_branches_checkbox": True,
        "p1_branch_city_text": "Springfield",
        "p1_branch_state_1_text": "I",
        "p1_branch_state_2_text": "L",
        
        # Branch zip code
        "p1_branch_zip_1_text": "6",
        "p1_branch_zip_2_text": "2",
        "p1_branch_zip_3_text": "7",
        "p1_branch_zip_4_text": "0",
        "p1_branch_zip_5_text": "1",
        "p1_branch_zip_6_text": "0",
        "p1_branch_zip_7_text": "0",
        "p1_branch_zip_8_text": "0",
        "p1_branch_zip_9_text": "0",
        
        # Institution closed date
        "p1_institution_closed_month_text": "03",
        "p1_institution_closed_day_text": "15",
        "p1_institution_closed_year_text": "2025",
        
        # Account numbers and status
        "p1_account_number_1_text": "1234567890",
        "p1_account_1_closed_yes_checkbox": True,
        "p1_account_1_closed_no_checkbox": True,
        "p1_account_number_2_text": "0987654321",
        "p1_account_2_closed_yes_checkbox": True,
        "p1_account_2_closed_no_checkbox": True,
        "p1_account_number_3_text": "5555555555",
        "p1_account_3_closed_yes_checkbox": True,
        "p1_account_3_closed_no_checkbox": True,
        "p1_account_number_4_text": "7777777777",
        "p1_account_4_closed_yes_checkbox": True,
        "p1_account_4_closed_no_checkbox": True,
        
        # Part II - Suspect Information
        "p2_suspect_info_unavailable_checkbox": True,
        "p2_suspect_last_name_text": "Smith Corporation",
        "p2_suspect_first_name_text": "John",
        "p2_suspect_middle_name_text": "Robert",
        "p2_suspect_address_text": "123 Suspect Lane",
        "p2_suspect_ssn_ein_text": "123456789",
        "p2_suspect_city_text": "Los Angeles",
        "p2_suspect_state_1_text": "C",
        "p2_suspect_state_2_text": "A",
        
        # Suspect zip code
        "p2_suspect_zip_1_text": "9",
        "p2_suspect_zip_2_text": "0",
        "p2_suspect_zip_3_text": "0",
        "p2_suspect_zip_4_text": "0",
        "p2_suspect_zip_5_text": "1",
        "p2_suspect_zip_6_text": "0",
        "p2_suspect_zip_7_text": "0",
        "p2_suspect_zip_8_text": "0",
        "p2_suspect_zip_9_text": "0",
        
        "p2_suspect_country_text": "United States",
        "p2_suspect_phone_home_area_text": "312",
        "p2_suspect_phone_home_number_text": "5550123",
        "p2_suspect_phone_work_area_text": "312",
        "p2_suspect_phone_work_number_text": "5554567",
        "p2_suspect_occupation_text": "Technology Consulting",
        "p2_suspect_dob_day_text": "21",
        "p2_suspect_dob_year_text": "1975",
        
        # Suspect ID information
        "p2_suspect_id_number_1_text": "DL123456789",
        "p2_suspect_id_number_2_text": "PP123456789",
        "p2_suspect_id_issuer_text": "SSN123456789",
        
        "p2_suspect_relationship_other_text": "State: CA, Expiration: 2025",
        
        # Employment status
        "p2_suspect_still_employed_checkbox": True,
        "p2_suspect_suspended_checkbox": True,
        "p2_suspect_terminated_checkbox": True,
        "p2_suspect_resigned_checkbox": True,
        
        # Termination date
        "p2_suspect_termination_month_text": "02",
        "p2_suspect_termination_day_text": "28",
        "p2_suspect_termination_year_text": "2025",
        
        # Part III - Suspicious Activity Information
        # Activity date range
        "p3_activity_from_month_text": "01",
        "p3_activity_from_day_text": "01",
        "p3_activity_from_year_text": "2025",
        "p3_activity_to_month_text": "03",
        "p3_activity_to_day_text": "15",
        "p3_activity_to_year_text": "2025",
        
        # Total amount ($1,000,000)
        "p3_total_amount_1_text": "1",
        "p3_total_amount_2_text": "0",
        "p3_total_amount_3_text": "0",
        "p3_total_amount_4_text": "0",
        "p3_total_amount_5_text": "0",
        "p3_total_amount_6_text": "0",
        "p3_total_amount_7_text": "0",
        "p3_total_amount_8_text": "0",
        "p3_total_amount_9_text": "0",
        "p3_total_amount_10_text": "0",
        "p3_total_amount_11_text": "0",
        
        # Activity types
        "p3_activity_bsa_structuring_checkbox": True,
        "p3_activity_bribery_checkbox": True,
        "p3_activity_check_fraud_checkbox": True,
        "p3_activity_check_kiting_checkbox": True,
        "p3_activity_commercial_loan_fraud_checkbox": True,
        "p3_activity_computer_intrusion_checkbox": True,
        "p3_activity_consumer_loan_fraud_checkbox": True,
        "p3_activity_counterfeit_check_checkbox": True,
        "p3_activity_counterfeit_card_checkbox": True,
        "p3_activity_counterfeit_instrument_checkbox": True,
        "p3_activity_credit_card_fraud_checkbox": True,
        "p3_activity_debit_card_fraud_checkbox": True,
        "p3_activity_defalcation_checkbox": True,
        "p3_activity_false_statement_checkbox": True,
        "p3_activity_misuse_position_checkbox": True,
        "p3_activity_mortgage_loan_fraud_checkbox": True,
        "p3_activity_mysterious_disappearance_checkbox": True,
        "p3_activity_wire_transfer_fraud_checkbox": True,
        "p3_activity_other_checkbox": True,
        "p3_activity_other_text": "Cryptocurrency-related fraud",
        "p3_activity_terrorist_financing_checkbox": True,
        "p3_activity_identity_theft_checkbox": True,
        
        # Amount of loss ($750,000)
        "p3_loss_amount_1_text": "7",
        "p3_loss_amount_2_text": "5",
        "p3_loss_amount_3_text": "0",
        "p3_loss_amount_4_text": "0",
        "p3_loss_amount_5_text": "0",
        "p3_loss_amount_6_text": "0",
        "p3_loss_amount_7_text": "0",
        "p3_loss_amount_8_text": "0",
        
        # Amount recovered ($250,000)
        "p3_recovery_amount_2_text": "2",
        "p3_recovery_amount_3_text": "5",
        "p3_recovery_amount_4_text": "0",
        "p3_recovery_amount_5_text": "0",
        "p3_recovery_amount_6_text": "0",
        "p3_recovery_amount_7_text": "0",
        "p3_recovery_amount_8_text": "0",
        "p3_recovery_amount_9_text": "0",
        
        # Law enforcement notifications
        "p3_notified_dea_checkbox": True,
        "p3_notified_fbi_checkbox": True,
        "p3_notified_irs_checkbox": True,
        "p3_notified_postal_checkbox": True,
        "p3_notified_secret_service_checkbox": True,
        "p3_notified_customs_checkbox": True,
        "p3_notified_other_federal_checkbox": True,
        "p3_notified_state_checkbox": True,
        "p3_notified_local_checkbox": True,
        "p3_notified_agency_name_provided_checkbox": True,
        "p3_notified_agency_name_text": "Illinois Financial Crimes Task Force",
        
        # Law enforcement contacts
        "p3_contact_name_1_text": "Agent Sarah Johnson",
        "p3_contact_1_phone_area_text": "202",
        "p3_contact_1_phone_number_text": "5550123",
        "p3_contact_name_2_text": "Detective Michael Brown",
        "p3_contact_2_phone_area_text": "312",
        "p3_contact_2_phone_number_text": "5559876",
        
        # Part IV - Contact for Assistance
        "p4_contact_last_name_text": "Anderson",
        "p4_contact_first_name_text": "Emily",
        "p4_contact_middle_name_text": "Jane",
        "p4_contact_title_text": "Compliance Officer",
        "p4_contact_phone_area_text": "312",
        "p4_contact_phone_number_text": "5558888",
        "p4_date_prepared_month_text": "03",
        "p4_date_prepared_day_text": "24",
        "p4_date_prepared_year_text": "2025",
        "p4_agency_text": "Financial Compliance Services LLC"
    }

if __name__ == "__main__":
    # Create test data that fills every field
    test_data = create_test_data()
    
    # Fill the PDF using descriptive field names
    fill_sar_pdf(
        test_data,
        "resources/6710-06.pdf",
        "resources/6710-06_filled_test.pdf",
        "resources/field_analysis_descriptive.json"
    )
