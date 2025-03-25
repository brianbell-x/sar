"""
Script to create descriptive field mappings for SAR Form 6710-06.
Maps original PDF field names (e.g., item32, item35a) to highly descriptive names
following the pattern: p<part>_f<field_number><sub_item?>_<description>_<type>.
"""

import json
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_field_mappings() -> Dict[str, str]:
    """Create mapping of original PDF field names to descriptive names."""

    mappings = {
        # --- Part I: Reporting Financial Institution Information ---
        "item1":    "p1_f1_corrects_prior_report_checkbox",        # Field 1: Check if this corrects a prior report
        "item2":    "p1_f2_institution_legal_name_text",           # Field 2: Name of Financial Institution
        "item3":    "p1_f3_institution_ein_text",                  # Field 3: Employer Identification Number (EIN)
        "item4":    "p1_f4_institution_address_text",              # Field 4: Address of Financial Institution
        # Field 5: Primary Federal Regulator
        "item5a":   "p1_f5a_regulator_option_federal_reserve_checkbox",# 5a: Federal Reserve System (FRS)
        "item5b":   "p1_f5b_regulator_option_fdic_checkbox",           # 5b: Federal Deposit Insurance Corporation (FDIC)
        "item5c":   "p1_f5c_regulator_option_ncua_checkbox",           # 5c: National Credit Union Administration (NCUA)
        "item5d":   "p1_f5d_regulator_option_occ_checkbox",            # 5d: Office of the Comptroller of the Currency (OCC)
        "item5e":   "p1_f5e_regulator_option_ots_checkbox",            # 5e: Office of Thrift Supervision (OTS)
        "item6":    "p1_f6_institution_city_text",                 # Field 6: City of Financial Institution
        "item7":    "p1_f7_institution_state_char1_text",          # Field 7: State (Character 1)
        "item7-1":  "p1_f7_institution_state_char2_text",          # Field 7: State (Character 2)
        # Field 8: ZIP Code (Institution)
        "item8-1":  "p1_f8_institution_zip_digit1_text",           # 8: Digit 1 (5-digit ZIP)
        "item8-2":  "p1_f8_institution_zip_digit2_text",           # 8: Digit 2
        "item8-3":  "p1_f8_institution_zip_digit3_text",           # 8: Digit 3
        "item8-4":  "p1_f8_institution_zip_digit4_text",           # 8: Digit 4
        "item8-5":  "p1_f8_institution_zip_digit5_text",           # 8: Digit 5
        "item8-6":  "p1_f8_institution_zip_digit6_text",           # 8: Digit 6 (+4 extension)
        "item8-7":  "p1_f8_institution_zip_digit7_text",           # 8: Digit 7 (+4 extension)
        "item8-8":  "p1_f8_institution_zip_digit8_text",           # 8: Digit 8 (+4 extension)
        "item8-9":  "p1_f8_institution_zip_digit9_text",           # 8: Digit 9 (+4 extension)
        "item9":    "p1_f9_branch_address_text",                   # Field 9: Address of Branch Office(s) where activity occurred
        "item9-1":  "p1_f9_multiple_branches_involved_checkbox",   # Field 9: Check if multiple branches involved
        "item10":   "p1_f10_branch_city_text",                     # Field 10: Branch City
        "item11-1": "p1_f11_branch_state_char1_text",              # Field 11: Branch State (Character 1)
        "item11-2": "p1_f11_branch_state_char2_text",              # Field 11: Branch State (Character 2)
        # Field 12: Branch ZIP Code
        "item12-1": "p1_f12_branch_zip_digit1_text",               # 12: Digit 1 (5-digit ZIP)
        "item12-2": "p1_f12_branch_zip_digit2_text",               # 12: Digit 2
        "item12-3": "p1_f12_branch_zip_digit3_text",               # 12: Digit 3
        "item12-4": "p1_f12_branch_zip_digit4_text",               # 12: Digit 4
        "item12-5": "p1_f12_branch_zip_digit5_text",               # 12: Digit 5
        "item12-6": "p1_f12_branch_zip_digit6_text",               # 12: Digit 6 (+4 extension)
        "item12-7": "p1_f12_branch_zip_digit7_text",               # 12: Digit 7 (+4 extension)
        "item12-8": "p1_f12_branch_zip_digit8_text",               # 12: Digit 8 (+4 extension)
        "item12-9": "p1_f12_branch_zip_digit9_text",               # 12: Digit 9 (+4 extension)
        # Field 13: Date Institution Closed (if applicable)
        "item13-1": "p1_f13_institution_closed_date_month_text",   # 13: Month (MM)
        "item13-2": "p1_f13_institution_closed_date_day_text",     # 13: Day (DD)
        "item13-3": "p1_f13_institution_closed_date_year_text",    # 13: Year (YYYY)
        # Field 14: Account number(s) affected, if any
        "item14a":   "p1_f14a_account_1_number_text",              # 14a: Account Number 1
        "item14a-1": "p1_f14a_account_1_is_closed_yes_checkbox",   # 14a: Account 1 Closed? Yes
        "item14a-2": "p1_f14a_account_1_is_closed_no_checkbox",    # 14a: Account 1 Closed? No
        "item14b":   "p1_f14b_account_2_number_text",              # 14b: Account Number 2
        "item14b-1": "p1_f14b_account_2_is_closed_yes_checkbox",   # 14b: Account 2 Closed? Yes
        "item14b-2": "p1_f14b_account_2_is_closed_no_checkbox",    # 14b: Account 2 Closed? No
        "item14c":   "p1_f14c_account_3_number_text",              # 14c: Account Number 3
        "item14c-1": "p1_f14c_account_3_is_closed_yes_checkbox",   # 14c: Account 3 Closed? Yes
        "item14c-2": "p1_f14c_account_3_is_closed_no_checkbox",    # 14c: Account 3 Closed? No
        "item14d":   "p1_f14d_account_4_number_text",              # 14d: Account Number 4
        "item14d-1": "p1_f14d_account_4_is_closed_yes_checkbox",   # 14d: Account 4 Closed? Yes
        "item14d-2": "p1_f14d_account_4_is_closed_no_checkbox",    # 14d: Account 4 Closed? No

        # --- Part II: Suspect Information ---
        "itemPII":  "p2_fNA_suspect_info_unavailable_checkbox",    # Checkbox above Field 15: Check if Suspect Info Unavailable
        "item15":   "p2_f15_suspect_last_name_or_entity_name_text",# Field 15: Last Name or Entity Name
        "item16":   "p2_f16_suspect_first_name_text",              # Field 16: First Name
        "item17":   "p2_f17_suspect_middle_name_text",             # Field 17: Middle Name/Initial
        "item18":   "p2_f18_suspect_address_text",                 # Field 18: Address
        "item19":   "p2_f19_suspect_ssn_or_ein_or_itin_text",      # Field 19: SSN or EIN or ITIN
        "item20":   "p2_f20_suspect_city_text",                    # Field 20: City
        "item21a":  "p2_f21_suspect_state_char1_text",             # Field 21: State (Character 1)
        "item21b":  "p2_f21_suspect_state_char2_text",             # Field 21: State (Character 2)
        # Field 22: Suspect ZIP Code
        "item22-1": "p2_f22_suspect_zip_digit1_text",              # 22: Digit 1 (5-digit ZIP)
        "item22-2": "p2_f22_suspect_zip_digit2_text",              # 22: Digit 2
        "item22-3": "p2_f22_suspect_zip_digit3_text",              # 22: Digit 3
        "item22-4": "p2_f22_suspect_zip_digit4_text",              # 22: Digit 4
        "item22-5": "p2_f22_suspect_zip_digit5_text",              # 22: Digit 5
        "item22-6": "p2_f22_suspect_zip_digit6_text",              # 22: Digit 6 (+4 extension)
        "ITEM22-7": "p2_f22_suspect_zip_digit7_text",              # 22: Digit 7 (+4 extension) - Note inconsistent case in original PDF analysis
        "ITEM22-8": "p2_f22_suspect_zip_digit8_text",              # 22: Digit 8 (+4 extension) - Note inconsistent case
        "item22-9": "p2_f22_suspect_zip_digit9_text",              # 22: Digit 9 (+4 extension)
        "item23":   "p2_f23_suspect_country_text",                 # Field 23: Country
        # Field 24: Suspect Phone Number - Residence
        "item24-1": "p2_f24_suspect_phone_residence_area_code_text",# 24: Area Code (3 digits)
        "item24-2": "p2_f24_suspect_phone_residence_number_text",   # 24: Number (7 digits)
        # Field 25: Suspect Phone Number - Work
        "item25-1": "p2_f25_suspect_phone_work_area_code_text",     # 25: Area Code (3 digits)
        "item25-2": "p2_f25_suspect_phone_work_number_text",        # 25: Number (7 digits)
        "item26":   "p2_f26_suspect_occupation_or_business_type_text",# Field 26: Occupation or Type of Business
        # Field 27: Suspect Date of Birth
        "item27-1": "p2_f27_suspect_dob_month_text",               # 27: Month (MM) - Note: Original PDF analysis missed this, assuming mapping based on adjacent fields
        "item27-2": "p2_f27_suspect_dob_day_text",                 # 27: Day (DD)
        "item27-3": "p2_f27_suspect_dob_year_text",                # 27: Year (YYYY)
        # Field 28: Admission/Confession
        "item28a":  "p2_f28_admission_confession_option_yes_checkbox",# 28a: Yes
        "item28b":  "p2_f28_admission_confession_option_no_checkbox", # 28b: No
        # Field 29: Form(s) of Identification for Suspect
        "item29a":  "p2_f29a_id_type_option_drivers_license_checkbox",# 29a: Driver's License/State ID
        "item29b":  "p2_f29b_id_type_option_passport_checkbox",      # 29b: Passport
        "item29c":  "p2_f29c_id_type_option_alien_reg_checkbox",     # 29c: Alien Registration
        "item29d":  "p2_f29d_id_type_option_other_checkbox",         # 29d: Other
        "item29-1": "p2_f29_id_number_part1_text",            # 29: Number (part 1)
        "item29-2": "p2_f29_id_number_part2_text",            # 29: Number (part 2)
        "item29-3": "p2_f29_id_issuing_authority_text",       # 29: Issuing Authority (State/Country)
        # Field 30: Relationship to Financial Institution
        "item30a":  "p2_f30a_relationship_option_accountant_checkbox",# 30a: Accountant
        "item30b":  "p2_f30b_relationship_option_agent_checkbox",     # 30b: Agent
        "item30c":  "p2_f30c_relationship_option_appraiser_checkbox", # 30c: Appraiser
        "item30d":  "p2_f30d_relationship_option_attorney_checkbox",  # 30d: Attorney
        "item30e":  "p2_f30e_relationship_option_borrower_checkbox",  # 30e: Borrower
        "item30f":  "p2_f30f_relationship_option_broker_checkbox",    # 30f: Broker
        "item30g":  "p2_f30g_relationship_option_customer_checkbox",  # 30g: Customer
        "item30h":  "p2_f30h_relationship_option_director_checkbox",  # 30h: Director
        "item30i":  "p2_f30i_relationship_option_employee_checkbox",  # 30i: Employee
        "item30j":  "p2_f30j_relationship_option_officer_checkbox",   # 30j: Officer
        "item30k":  "p2_f30k_relationship_option_shareholder_checkbox",# 30k: Shareholder
        "item30l":  "p2_f30l_relationship_option_other_checkbox",     # 30l: Other
        "item30-1": "p2_f30l_relationship_option_other_description_text",# 30l: Other Relationship Description
        # Field 31: Is the relationship an insider relationship?
        "item31a":  "p2_f31_insider_relationship_option_yes_checkbox", # 31a: Yes
        "item31b":  "p2_f31_insider_relationship_option_no_checkbox",  # 31b: No
        # Field 31: If Yes (insider), specify current status:
        "item31c":  "p2_f31c_insider_status_option_employed_checkbox",# 31c: Still Employed
        "item31d":  "p2_f31d_insider_status_option_suspended_checkbox",# 31d: Suspended
        "item31e":  "p2_f31e_insider_status_option_terminated_checkbox",# 31e: Terminated
        "item31f":  "p2_f31f_insider_status_option_resigned_checkbox",# 31f: Resigned
        # Field 32: Date of Suspension, Termination, Resignation (if applicable)
        "item32-1": "p2_f32_insider_status_date_month_text",       # 32: Month (MM)
        "item32-2": "p2_f32_insider_status_date_day_text",         # 32: Day (DD)
        "item32-3": "p2_f32_insider_status_date_year_text",        # 32: Year (YYYY)

        # --- Part III: Suspicious Activity Information ---
        # Field 33: Date or date range of suspicious activity
        "item33-1": "p3_f33_activity_date_from_month_text",        # 33: From Month (MM)
        "item33-2": "p3_f33_activity_date_from_day_text",          # 33: From Day (DD)
        "item33-3": "p3_f33_activity_date_from_year_text",         # 33: From Year (YYYY)
        "item33-4": "p3_f33_activity_date_to_month_text",          # 33: To Month (MM)
        "item33-5": "p3_f33_activity_date_to_day_text",            # 33: To Day (DD)
        "item33-6": "p3_f33_activity_date_to_year_text",           # 33: To Year (YYYY)
        # Field 34: Total dollar amount involved in known or suspicious activity
        "item34-1": "p3_f34_total_amount_digit1_text",             # 34: Digit 1 (Least significant)
        "item34-2": "p3_f34_total_amount_digit2_text",             # 34: Digit 2
        "item34-3": "p3_f34_total_amount_digit3_text",             # 34: Digit 3
        "item34-4": "p3_f34_total_amount_digit4_text",             # 34: Digit 4
        "item34-5": "p3_f34_total_amount_digit5_text",             # 34: Digit 5
        "item34-6": "p3_f34_total_amount_digit6_text",             # 34: Digit 6
        "item34-7": "p3_f34_total_amount_digit7_text",             # 34: Digit 7
        "item34-8": "p3_f34_total_amount_digit8_text",             # 34: Digit 8
        "item34-9": "p3_f34_total_amount_digit9_text",             # 34: Digit 9
        "item34-10":"p3_f34_total_amount_digit10_text",            # 34: Digit 10
        "item34-11":"p3_f34_total_amount_digit11_text",            # 34: Digit 11 (Most significant)
        # Field 35: Summary characterization of suspicious activity
        "item35a":  "p3_f35a_activity_type_bsa_structuring_checkbox",    # 35a: Bank Secrecy Act/Structuring
        "item35b":  "p3_f35b_activity_type_bribery_gratuity_checkbox",   # 35b: Bribery/Gratuity
        "item35c":  "p3_f35c_activity_type_check_fraud_checkbox",        # 35c: Check Fraud
        "item35d":  "p3_f35d_activity_type_check_kiting_checkbox",       # 35d: Check Kiting
        "item35e":  "p3_f35e_activity_type_commercial_loan_fraud_checkbox",# 35e: Commercial Loan Fraud
        "item35f":  "p3_f35f_activity_type_computer_intrusion_checkbox", # 35f: Computer Intrusion
        "item35g":  "p3_f35g_activity_type_consumer_loan_fraud_checkbox",# 35g: Consumer Loan Fraud
        "item35h":  "p3_f35h_activity_type_counterfeit_check_checkbox",  # 35h: Counterfeit Check
        "item35i":  "p3_f35i_activity_type_counterfeit_card_checkbox",   # 35i: Counterfeit Credit/Debit Card
        "item35j":  "p3_f35j_activity_type_counterfeit_instrument_checkbox",# 35j: Counterfeit Instrument (other)
        "item35k":  "p3_f35k_activity_type_credit_card_fraud_checkbox",  # 35k: Credit Card Fraud
        "item35l":  "p3_f35l_activity_type_debit_card_fraud_checkbox",   # 35l: Debit Card Fraud
        "item35m":  "p3_f35m_activity_type_defalcation_embezzlement_checkbox",# 35m: Defalcation/Embezzlement
        "item35n":  "p3_f35n_activity_type_false_statement_checkbox",    # 35n: False Statement
        "item35o":  "p3_f35o_activity_type_misuse_of_position_checkbox", # 35o: Misuse of Position or Self Dealing
        "item35p":  "p3_f35p_activity_type_mortgage_loan_fraud_checkbox",# 35p: Mortgage Loan Fraud
        "item35q":  "p3_f35q_activity_type_mysterious_disappearance_checkbox",# 35q: Mysterious Disappearance
        "item35r":  "p3_f35r_activity_type_wire_transfer_fraud_checkbox",# 35r: Wire Transfer Fraud
        "item35s":  "p3_f35s_activity_type_other_checkbox",              # 35s: Other
        "item35s-1":"p3_f35s_activity_type_other_description_text",      # 35s: Other Activity Description
        "item35t":  "p3_f35t_activity_type_terrorist_financing_checkbox",# 35t: Terrorist Financing
        "item35u":  "p3_f35u_activity_type_identity_theft_checkbox",     # 35u: Identity Theft
        # Field 36: Amount of loss prior to recovery
        "item36-1": "p3_f36_loss_amount_digit1_text",            # 36: Digit 1 (Least significant)
        "item36-2": "p3_f36_loss_amount_digit2_text",            # 36: Digit 2
        "item36-3": "p3_f36_loss_amount_digit3_text",            # 36: Digit 3
        "item36-4": "p3_f36_loss_amount_digit4_text",            # 36: Digit 4
        "item36-5": "p3_f36_loss_amount_digit5_text",            # 36: Digit 5
        "item36-6": "p3_f36_loss_amount_digit6_text",            # 36: Digit 6
        "item36-7": "p3_f36_loss_amount_digit7_text",            # 36: Digit 7
        "item36-8": "p3_f36_loss_amount_digit8_text",            # 36: Digit 8 (Most significant)
        # Field 37: Dollar amount of recovery
        # "item37-1" is missing in the original analysis, assuming it's digit 1
        "item37-1": "p3_f37_recovery_amount_digit1_text",        # 37: Digit 1 (Least significant) - ASSUMED MAPPING
        "item37-2": "p3_f37_recovery_amount_digit2_text",        # 37: Digit 2
        "37-3":     "p3_f37_recovery_amount_digit3_text",        # 37: Digit 3 - Note different format in original analysis
        "item37-4": "p3_f37_recovery_amount_digit4_text",        # 37: Digit 4
        "item37-5": "p3_f37_recovery_amount_digit5_text",        # 37: Digit 5
        "item37-6": "p3_f37_recovery_amount_digit6_text",        # 37: Digit 6
        "item37-7": "p3_f37_recovery_amount_digit7_text",        # 37: Digit 7
        "item37-8": "p3_f37_recovery_amount_digit8_text",        # 37: Digit 8
        "item37-9": "p3_f37_recovery_amount_digit9_text",        # 37: Digit 9 (Most significant)
        # Field 38: Material Impact
        "item38a":  "p3_f38_material_impact_option_yes_checkbox",# 38a: Yes
        "item38b":  "p3_f38_material_impact_option_no_checkbox", # 38b: No
        # Field 39: Bonding Company Notified
        "item39a":  "p3_f39_bonding_company_notified_option_yes_checkbox",# 39a: Yes
        "item39b":  "p3_f39_bonding_company_notified_option_no_checkbox", # 39b: No
        # Field 40: Law Enforcement Agency Advised
        "item40a":  "p3_f40a_agency_notified_dea_checkbox",              # 40a: DEA
        "item40b":  "p3_f40b_agency_notified_fbi_checkbox",              # 40b: FBI
        "item40c":  "p3_f40c_agency_notified_irs_checkbox",              # 40c: IRS
        "item40d":  "p3_f40d_agency_notified_postal_inspection_checkbox",# 40d: Postal Inspection
        "item40e":  "p3_f40e_agency_notified_secret_service_checkbox",   # 40e: Secret Service
        "item40f":  "p3_f40f_agency_notified_us_customs_checkbox",       # 40f: U.S. Customs
        "item40g":  "p3_f40g_agency_notified_other_federal_checkbox",    # 40g: Other Federal
        "item40h":  "p3_f40h_agency_notified_state_checkbox",            # 40h: State
        "item40i":  "p3_f40i_agency_notified_local_checkbox",            # 40i: Local
        "item40j":  "p3_f40j_agency_name_provided_checkbox",             # 40j: Check if Agency Name provided below
        "item40j-1":"p3_f40j_agency_name_text",                          # 40j: Agency Name (if g, h, or i checked)
        # Field 41-44: Law Enforcement Contact Information
        "item41":   "p3_f41_law_enforcement_contact_1_name_text",        # Field 41: Contact Name 1
        "item42-1": "p3_f42_law_enforcement_contact_1_phone_area_code_text",# Field 42: Phone 1 Area Code
        "item42-2": "p3_f42_law_enforcement_contact_1_phone_number_text", # Field 42: Phone 1 Number
        "item43":   "p3_f43_law_enforcement_contact_2_name_text",        # Field 43: Contact Name 2
        "item44-1": "p3_f44_law_enforcement_contact_2_phone_area_code_text",# Field 44: Phone 2 Area Code
        "item44-2": "p3_f44_law_enforcement_contact_2_phone_number_text", # Field 44: Phone 2 Number

        # --- Part IV: Contact for Assistance ---
        "item45":   "p4_f45_assistance_contact_last_name_text",      # Field 45: Last Name
        "item46":   "p4_f46_assistance_contact_first_name_text",     # Field 46: First Name
        "item47":   "p4_f47_assistance_contact_middle_name_text",    # Field 47: Middle Name/Initial
        "item48":   "p4_f48_assistance_contact_title_text",          # Field 48: Title
        # Field 49: Contact Phone Number
        "item49-1": "p4_f49_assistance_contact_phone_area_code_text",# 49: Area Code
        "item49-2": "p4_f49_assistance_contact_phone_number_text",   # 49: Number
        # Field 50: Date Prepared
        "item50-1": "p4_f50_date_prepared_month_text",            # 50: Month (MM)
        "item50-2": "p4_f50_date_prepared_day_text",              # 50: Day (DD)
        "item50-3": "p4_f50_date_prepared_year_text",             # 50: Year (YYYY)
        "item51":   "p4_f51_filing_agency_name_if_not_institution_text", # Field 51: Agency name of filer

        # --- Metadata/Other ---
        "FormName": "form_name_metadata_text", # Form metadata field often present in PDF templates
        # "item51" seems to be used for the narrative on page 3 in the original analysis,
        # but narrative is conceptually Part V. We'll map it here for PDF filling purposes
        # but the LLM prompt should use p5_fNA_narrative_text conceptually.
        # "item51": "p5_fNA_narrative_text" # Conceptual mapping for LLM

    }

    # Add narrative field separately for clarity in LLM prompt generation,
    # even though it might physically occupy the space of 'item51' in the PDF structure.
    # This mapping is primarily for the LLM's JSON output structure.
    # mappings["item51"] = "p5_fNA_narrative_text" # Assign narrative conceptually

    return mappings

def update_field_analysis(input_path: str, output_path: str) -> None:
    """
    Update field analysis JSON with descriptive names based on the new mapping.

    Args:
        input_path: Path to original field analysis JSON (with original PDF field names).
        output_path: Path to save updated field analysis JSON (with new descriptive names).
    """
    try:
        # Load original field analysis
        with open(input_path) as f:
            field_info = json.load(f)

        # Get mappings from original PDF name -> new descriptive name
        mappings = create_field_mappings()

        # Create new field info using descriptive names as keys
        new_field_info = {}
        unmapped_original_names = []

        for original_name, info in field_info.items():
            if original_name in mappings:
                new_name = mappings[original_name]
                new_field_info[new_name] = info
                # Store the original PDF name within the info dict for reference/debugging
                new_field_info[new_name]["original_pdf_name"] = original_name
            else:
                # Keep unmapped fields using their original names, but log them
                logger.warning(f"No mapping defined for original PDF field: '{original_name}'")
                new_field_info[original_name] = info
                unmapped_original_names.append(original_name)

        # Save updated field analysis (keys are now descriptive names)
        with open(output_path, 'w') as f:
            json.dump(new_field_info, f, indent=2, sort_keys=True) # Sort keys for consistency

        logger.info(f"Updated field analysis saved to: {output_path}")

        # Print summary of unmapped fields
        if unmapped_original_names:
            logger.warning("\nOriginal PDF fields NOT mapped to descriptive names:")
            for name in sorted(unmapped_original_names):
                logger.warning(f"  - {name}")
        else:
            logger.info("\nAll fields from input JSON were successfully mapped.")

    except FileNotFoundError:
        logger.error(f"Error: Input file not found at '{input_path}'")
        raise
    except json.JSONDecodeError:
        logger.error(f"Error: Could not decode JSON from '{input_path}'")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during field analysis update: {str(e)}")
        raise

if __name__ == "__main__":
    # Define input and output paths
    original_analysis_path = "resources/field_analysis.json"
    descriptive_analysis_output_path = "resources/field_analysis_descriptive.json"

    original_filled_analysis_path = "resources/field_analysis_filled.json"
    descriptive_filled_analysis_output_path = "resources/field_analysis_filled_descriptive.json"

    logger.info(f"Updating field analysis: '{original_analysis_path}' -> '{descriptive_analysis_output_path}'")
    update_field_analysis(
        original_analysis_path,
        descriptive_analysis_output_path
    )

    logger.info(f"\nUpdating filled field analysis: '{original_filled_analysis_path}' -> '{descriptive_filled_analysis_output_path}'")
    update_field_analysis(
        original_filled_analysis_path,
        descriptive_filled_analysis_output_path
    )

    logger.info("\nField mapping script finished.")