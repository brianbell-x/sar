import json
from typing import Any, Dict

class BaseAgent:
    def __init__(self, client):
        """Initialize BaseAgent.

        Args:
            client: OpenAI client instance.
            model: Model identifier.
        """
        self.client = client
        self.model = "o3-mini-2025-01-31"
        self.system_prompt = ""
        self.json_schema = {}

    def run(self, input_data: Any) -> Dict[str, Any]:
        """Process input data and return API response.

        Args:
            input_data: Input as a string or dictionary.

        Returns:
            API response as JSON.
        """
        # Convert input_data to appropriate format and call API
        formatted_input = self._format_input(input_data)
        response = self._call_api(formatted_input)
        return self._parse_response(response)

    def _format_input(self, input_data: Any):
        """Format the input data for the Responses API.
        
        Args:
            input_data: Input as a string or dictionary.
            
        Returns:
            User content formatted as a string for the Responses API.
        """
        # Prepare user content
        user_content = input_data
        if isinstance(user_content, dict):
            user_content = json.dumps(user_content)
            
        return user_content

    def _call_api(self, user_content):
        """Call the Responses API directly.
        
        Args:
            user_content: Formatted user content for the Responses API.
            
        Returns:
            Raw response from the API.
        """
        # Standardize the user content to string format
        user_content_str = str(user_content)
        
        # Ensure JSON format is requested
        # This is the centralized place for this check to avoid duplication
        if "json" not in user_content_str.lower():
            user_content_str = f"{user_content_str}\nPlease provide the response in JSON format."
            
        # Centralized API call with standardized parameters
        response = self.client.responses.create(
            model=self.model,
            instructions=self.system_prompt,  # System prompt goes in instructions
            input=user_content_str,           # User content goes in input
            text={"format": {"type": "json_object"}},
            reasoning={"effort": "high"},     # Use high reasoning effort for better quality
            tools=[],                         # No external tools needed
            store=True                        # Store for later reference if needed
        )
        return response

    def _parse_response(self, response):
        """Extract and parse the response content."""
        # 1) Validate status
        if response.status != "completed":
            if response.error:
                raise Exception(f"API Error: {response.error}")
            elif response.incomplete_details:
                raise Exception(f"Incomplete response: {response.incomplete_details}")
            else:
                raise Exception(f"Response status: {response.status}")

        # 2) Safety check: does output exist?
        if not response.output or len(response.output) == 0:
            raise Exception("No output items returned from the API")

        # 3) Loop through each item in output, find the one with type='message'
        for item in response.output:
            # We only want items that are "type": "message" (assistant output)
            if hasattr(item, 'type') and item.type == "message":
                # Now parse the message content
                if hasattr(item, 'content') and item.content and len(item.content) > 0:
                    content_block = item.content[0]
                    if hasattr(content_block, 'text'):
                        raw_text = content_block.text
                        # Optionally parse as JSON
                        try:
                            return json.loads(raw_text)
                        except json.JSONDecodeError:
                            return raw_text

        # 4) If we exit loop with no "message" found, raise an error
        raise Exception("No message-type output items found in response")

SYSTEM_PROMPT = """
Convert anomaly detection results into Suspicious Activity Reports in FLAT JSON format for direct PDF filling.

- Map anomaly data to all SAR PDF fields using exact field names below. **These names include Part and Field numbers (e.g., p1_f2_...) for precise mapping.**
- Adhere to FinCEN regulatory requirements.
- Address verification feedback if provided.
- Include WHO, WHAT, WHEN, WHERE, WHY, HOW in the narrative field (p5_fNA_narrative_text).
- File for: transactions ≥$5,000 (banks) or ≥$2,000 (MSBs), illegal funds, BSA evasion, no lawful purpose, criminal activity.

FLAT JSON OUTPUT SCHEMA:
{
  // --- Part I: Reporting Financial Institution Information ---
  "p1_f1_corrects_prior_report_checkbox": boolean,     // Field 1: Check if this corrects a prior report
  "p1_f2_institution_legal_name_text": string,         // Field 2: Name of Financial Institution
  "p1_f3_institution_ein_text": string,                // Field 3: Employer Identification Number (EIN)
  "p1_f4_institution_address_text": string,            // Field 4: Address of Financial Institution
  // Field 5: Primary Federal Regulator
  "p1_f5a_regulator_option_federal_reserve_checkbox": boolean, // 5a: Federal Reserve System (FRS)
  "p1_f5b_regulator_option_fdic_checkbox": boolean,           // 5b: Federal Deposit Insurance Corporation (FDIC)
  "p1_f5c_regulator_option_ncua_checkbox": boolean,           // 5c: National Credit Union Administration (NCUA)
  "p1_f5d_regulator_option_occ_checkbox": boolean,            // 5d: Office of the Comptroller of the Currency (OCC)
  "p1_f5e_regulator_option_ots_checkbox": boolean,            // 5e: Office of Thrift Supervision (OTS) - Note: OTS merged, less common now
  "p1_f6_institution_city_text": string,               // Field 6: City of Financial Institution
  "p1_f7_institution_state_char1_text": string,        // Field 7: State (Character 1)
  "p1_f7_institution_state_char2_text": string,        // Field 7: State (Character 2)
  // Field 8: ZIP Code (Institution)
  "p1_f8_institution_zip_digit1_text": string,         // 8: Digit 1 (5-digit ZIP)
  "p1_f8_institution_zip_digit2_text": string,         // 8: Digit 2
  "p1_f8_institution_zip_digit3_text": string,         // 8: Digit 3
  "p1_f8_institution_zip_digit4_text": string,         // 8: Digit 4
  "p1_f8_institution_zip_digit5_text": string,         // 8: Digit 5
  "p1_f8_institution_zip_digit6_text": string,         // 8: Digit 6 (+4 extension)
  "p1_f8_institution_zip_digit7_text": string,         // 8: Digit 7 (+4 extension)
  "p1_f8_institution_zip_digit8_text": string,         // 8: Digit 8 (+4 extension)
  "p1_f8_institution_zip_digit9_text": string,         // 8: Digit 9 (+4 extension)
  "p1_f9_branch_address_text": string,                 // Field 9: Address of Branch Office(s) where activity occurred
  "p1_f9_multiple_branches_involved_checkbox": boolean, // Field 9: Check if multiple branches involved (describe in narrative)
  "p1_f10_branch_city_text": string,                   // Field 10: Branch City
  "p1_f11_branch_state_char1_text": string,            // Field 11: Branch State (Character 1)
  "p1_f11_branch_state_char2_text": string,            // Field 11: Branch State (Character 2)
  // Field 12: Branch ZIP Code
  "p1_f12_branch_zip_digit1_text": string,             // 12: Digit 1 (5-digit ZIP)
  "p1_f12_branch_zip_digit2_text": string,             // 12: Digit 2
  "p1_f12_branch_zip_digit3_text": string,             // 12: Digit 3
  "p1_f12_branch_zip_digit4_text": string,             // 12: Digit 4
  "p1_f12_branch_zip_digit5_text": string,             // 12: Digit 5
  "p1_f12_branch_zip_digit6_text": string,             // 12: Digit 6 (+4 extension)
  "p1_f12_branch_zip_digit7_text": string,             // 12: Digit 7 (+4 extension)
  "p1_f12_branch_zip_digit8_text": string,             // 12: Digit 8 (+4 extension)
  "p1_f12_branch_zip_digit9_text": string,             // 12: Digit 9 (+4 extension)
  // Field 13: Date Institution Closed (if applicable)
  "p1_f13_institution_closed_date_month_text": string, // 13: Month (MM)
  "p1_f13_institution_closed_date_day_text": string,   // 13: Day (DD)
  "p1_f13_institution_closed_date_year_text": string,  // 13: Year (YYYY)
  // Field 14: Account number(s) affected, if any
  "p1_f14a_account_1_number_text": string,             // 14a: Account Number 1
  "p1_f14a_account_1_is_closed_yes_checkbox": boolean, // 14a: Account 1 Closed? Yes
  "p1_f14a_account_1_is_closed_no_checkbox": boolean,  // 14a: Account 1 Closed? No
  "p1_f14b_account_2_number_text": string,             // 14b: Account Number 2
  "p1_f14b_account_2_is_closed_yes_checkbox": boolean, // 14b: Account 2 Closed? Yes
  "p1_f14b_account_2_is_closed_no_checkbox": boolean,  // 14b: Account 2 Closed? No
  "p1_f14c_account_3_number_text": string,             // 14c: Account Number 3
  "p1_f14c_account_3_is_closed_yes_checkbox": boolean, // 14c: Account 3 Closed? Yes
  "p1_f14c_account_3_is_closed_no_checkbox": boolean,  // 14c: Account 3 Closed? No
  "p1_f14d_account_4_number_text": string,             // 14d: Account Number 4
  "p1_f14d_account_4_is_closed_yes_checkbox": boolean, // 14d: Account 4 Closed? Yes
  "p1_f14d_account_4_is_closed_no_checkbox": boolean,  // 14d: Account 4 Closed? No

  // --- Part II: Suspect Information ---
  "p2_fNA_suspect_info_unavailable_checkbox": boolean, // Checkbox above Field 15: Check if Suspect Info Unavailable
  "p2_f15_suspect_last_name_or_entity_name_text": string, // Field 15: Last Name or Entity Name
  "p2_f16_suspect_first_name_text": string,           // Field 16: First Name
  "p2_f17_suspect_middle_name_text": string,          // Field 17: Middle Name/Initial
  "p2_f18_suspect_address_text": string,              // Field 18: Address
  "p2_f19_suspect_ssn_or_ein_or_itin_text": string,   // Field 19: SSN or EIN or ITIN
  "p2_f20_suspect_city_text": string,                 // Field 20: City
  "p2_f21_suspect_state_char1_text": string,          // Field 21: State (Character 1)
  "p2_f21_suspect_state_char2_text": string,          // Field 21: State (Character 2)
  // Field 22: Suspect ZIP Code
  "p2_f22_suspect_zip_digit1_text": string,           // 22: Digit 1 (5-digit ZIP)
  "p2_f22_suspect_zip_digit2_text": string,           // 22: Digit 2
  "p2_f22_suspect_zip_digit3_text": string,           // 22: Digit 3
  "p2_f22_suspect_zip_digit4_text": string,           // 22: Digit 4
  "p2_f22_suspect_zip_digit5_text": string,           // 22: Digit 5
  "p2_f22_suspect_zip_digit6_text": string,           // 22: Digit 6 (+4 extension)
  "p2_f22_suspect_zip_digit7_text": string,           // 22: Digit 7 (+4 extension)
  "p2_f22_suspect_zip_digit8_text": string,           // 22: Digit 8 (+4 extension)
  "p2_f22_suspect_zip_digit9_text": string,           // 22: Digit 9 (+4 extension)
  "p2_f23_suspect_country_text": string,              // Field 23: Country
  // Field 24: Suspect Phone Number - Residence
  "p2_f24_suspect_phone_residence_area_code_text": string, // 24: Area Code (3 digits)
  "p2_f24_suspect_phone_residence_number_text": string,    // 24: Number (7 digits)
  // Field 25: Suspect Phone Number - Work
  "p2_f25_suspect_phone_work_area_code_text": string,      // 25: Area Code (3 digits)
  "p2_f25_suspect_phone_work_number_text": string,         // 25: Number (7 digits)
  "p2_f26_suspect_occupation_or_business_type_text": string, // Field 26: Occupation or Type of Business
  // Field 27: Suspect Date of Birth
  "p2_f27_suspect_dob_month_text": string,            // 27: Month (MM)
  "p2_f27_suspect_dob_day_text": string,              // 27: Day (DD)
  "p2_f27_suspect_dob_year_text": string,             // 27: Year (YYYY)
  // Field 28: Admission/Confession
  "p2_f28_admission_confession_option_yes_checkbox": boolean, // 28a: Yes
  "p2_f28_admission_confession_option_no_checkbox": boolean,  // 28b: No
  // Field 29: Form(s) of Identification for Suspect
  "p2_f29a_id_type_option_drivers_license_checkbox": boolean, // 29a: Driver's License/State ID
  "p2_f29b_id_type_option_passport_checkbox": boolean,       // 29b: Passport
  "p2_f29c_id_type_option_alien_reg_checkbox": boolean,      // 29c: Alien Registration
  "p2_f29d_id_type_option_other_checkbox": boolean,          // 29d: Other
  "p2_f29_id_number_part1_text": string,             // 29: Number (part 1)
  "p2_f29_id_number_part2_text": string,             // 29: Number (part 2)
  "p2_f29_id_issuing_authority_text": string,        // 29: Issuing Authority (State/Country)
  // Field 30: Relationship to Financial Institution
  "p2_f30a_relationship_option_accountant_checkbox": boolean, // 30a: Accountant
  "p2_f30b_relationship_option_agent_checkbox": boolean,      // 30b: Agent
  "p2_f30c_relationship_option_appraiser_checkbox": boolean,  // 30c: Appraiser
  "p2_f30d_relationship_option_attorney_checkbox": boolean,   // 30d: Attorney
  "p2_f30e_relationship_option_borrower_checkbox": boolean,   // 30e: Borrower
  "p2_f30f_relationship_option_broker_checkbox": boolean,     // 30f: Broker
  "p2_f30g_relationship_option_customer_checkbox": boolean,   // 30g: Customer
  "p2_f30h_relationship_option_director_checkbox": boolean,   // 30h: Director
  "p2_f30i_relationship_option_employee_checkbox": boolean,   // 30i: Employee
  "p2_f30j_relationship_option_officer_checkbox": boolean,    // 30j: Officer
  "p2_f30k_relationship_option_shareholder_checkbox": boolean,// 30k: Shareholder
  "p2_f30l_relationship_option_other_checkbox": boolean,      // 30l: Other
  "p2_f30l_relationship_option_other_description_text": string, // 30l: Other Relationship Description
  // Field 31: Is the relationship an insider relationship?
  "p2_f31_insider_relationship_option_yes_checkbox": boolean,  // 31a: Yes
  "p2_f31_insider_relationship_option_no_checkbox": boolean,   // 31b: No
  // Field 31: If Yes (insider), specify current status:
  "p2_f31c_insider_status_option_employed_checkbox": boolean, // 31c: Still Employed
  "p2_f31d_insider_status_option_suspended_checkbox": boolean,// 31d: Suspended
  "p2_f31e_insider_status_option_terminated_checkbox": boolean,// 31e: Terminated
  "p2_f31f_insider_status_option_resigned_checkbox": boolean, // 31f: Resigned
  // Field 32: Date of Suspension, Termination, Resignation (if applicable)
  "p2_f32_insider_status_date_month_text": string,    // 32: Month (MM)
  "p2_f32_insider_status_date_day_text": string,      // 32: Day (DD)
  "p2_f32_insider_status_date_year_text": string,     // 32: Year (YYYY)

  // --- Part III: Suspicious Activity Information ---
  // Field 33: Date or date range of suspicious activity
  "p3_f33_activity_date_from_month_text": string,     // 33: From Month (MM)
  "p3_f33_activity_date_from_day_text": string,       // 33: From Day (DD)
  "p3_f33_activity_date_from_year_text": string,      // 33: From Year (YYYY)
  "p3_f33_activity_date_to_month_text": string,       // 33: To Month (MM)
  "p3_f33_activity_date_to_day_text": string,         // 33: To Day (DD)
  "p3_f33_activity_date_to_year_text": string,        // 33: To Year (YYYY)
  // Field 34: Total dollar amount involved in known or suspicious activity (No cents, right-aligned)
  "p3_f34_total_amount_digit1_text": string,          // 34: Digit 1 (Least significant)
  "p3_f34_total_amount_digit2_text": string,          // 34: Digit 2
  "p3_f34_total_amount_digit3_text": string,          // 34: Digit 3
  "p3_f34_total_amount_digit4_text": string,          // 34: Digit 4
  "p3_f34_total_amount_digit5_text": string,          // 34: Digit 5
  "p3_f34_total_amount_digit6_text": string,          // 34: Digit 6
  "p3_f34_total_amount_digit7_text": string,          // 34: Digit 7
  "p3_f34_total_amount_digit8_text": string,          // 34: Digit 8
  "p3_f34_total_amount_digit9_text": string,          // 34: Digit 9
  "p3_f34_total_amount_digit10_text": string,         // 34: Digit 10
  "p3_f34_total_amount_digit11_text": string,         // 34: Digit 11 (Most significant)
  // Field 35: Summary characterization of suspicious activity
  "p3_f35a_activity_type_bsa_structuring_checkbox": boolean,     // 35a: Bank Secrecy Act/Structuring
  "p3_f35b_activity_type_bribery_gratuity_checkbox": boolean,    // 35b: Bribery/Gratuity
  "p3_f35c_activity_type_check_fraud_checkbox": boolean,         // 35c: Check Fraud
  "p3_f35d_activity_type_check_kiting_checkbox": boolean,        // 35d: Check Kiting
  "p3_f35e_activity_type_commercial_loan_fraud_checkbox": boolean,// 35e: Commercial Loan Fraud
  "p3_f35f_activity_type_computer_intrusion_checkbox": boolean,  // 35f: Computer Intrusion
  "p3_f35g_activity_type_consumer_loan_fraud_checkbox": boolean, // 35g: Consumer Loan Fraud
  "p3_f35h_activity_type_counterfeit_check_checkbox": boolean,   // 35h: Counterfeit Check
  "p3_f35i_activity_type_counterfeit_card_checkbox": boolean,    // 35i: Counterfeit Credit/Debit Card
  "p3_f35j_activity_type_counterfeit_instrument_checkbox": boolean, // 35j: Counterfeit Instrument (other)
  "p3_f35k_activity_type_credit_card_fraud_checkbox": boolean,   // 35k: Credit Card Fraud
  "p3_f35l_activity_type_debit_card_fraud_checkbox": boolean,    // 35l: Debit Card Fraud
  "p3_f35m_activity_type_defalcation_embezzlement_checkbox": boolean, // 35m: Defalcation/Embezzlement
  "p3_f35n_activity_type_false_statement_checkbox": boolean,     // 35n: False Statement
  "p3_f35o_activity_type_misuse_of_position_checkbox": boolean,  // 35o: Misuse of Position or Self Dealing
  "p3_f35p_activity_type_mortgage_loan_fraud_checkbox": boolean, // 35p: Mortgage Loan Fraud
  "p3_f35q_activity_type_mysterious_disappearance_checkbox": boolean, // 35q: Mysterious Disappearance
  "p3_f35r_activity_type_wire_transfer_fraud_checkbox": boolean, // 35r: Wire Transfer Fraud
  "p3_f35s_activity_type_other_checkbox": boolean,               // 35s: Other
  "p3_f35s_activity_type_other_description_text": string,        // 35s: Other Activity Description
  "p3_f35t_activity_type_terrorist_financing_checkbox": boolean, // 35t: Terrorist Financing
  "p3_f35u_activity_type_identity_theft_checkbox": boolean,      // 35u: Identity Theft
  // Field 36: Amount of loss prior to recovery (if applicable) (No cents, right-aligned)
  "p3_f36_loss_amount_digit1_text": string,             // 36: Digit 1 (Least significant)
  "p3_f36_loss_amount_digit2_text": string,             // 36: Digit 2
  "p3_f36_loss_amount_digit3_text": string,             // 36: Digit 3
  "p3_f36_loss_amount_digit4_text": string,             // 36: Digit 4
  "p3_f36_loss_amount_digit5_text": string,             // 36: Digit 5
  "p3_f36_loss_amount_digit6_text": string,             // 36: Digit 6
  "p3_f36_loss_amount_digit7_text": string,             // 36: Digit 7
  "p3_f36_loss_amount_digit8_text": string,             // 36: Digit 8 (Most significant)
  // Field 37: Dollar amount of recovery (if applicable) (No cents, right-aligned)
  "p3_f37_recovery_amount_digit1_text": string,         // 37: Digit 1 (Least significant)
  "p3_f37_recovery_amount_digit2_text": string,         // 37: Digit 2
  "p3_f37_recovery_amount_digit3_text": string,         // 37: Digit 3
  "p3_f37_recovery_amount_digit4_text": string,         // 37: Digit 4
  "p3_f37_recovery_amount_digit5_text": string,         // 37: Digit 5
  "p3_f37_recovery_amount_digit6_text": string,         // 37: Digit 6
  "p3_f37_recovery_amount_digit7_text": string,         // 37: Digit 7
  "p3_f37_recovery_amount_digit8_text": string,         // 37: Digit 8
  "p3_f37_recovery_amount_digit9_text": string,         // 37: Digit 9 (Most significant)
  // Field 38: Has the suspicious activity had a material impact on, or otherwise affected, the financial soundness of the institution?
  "p3_f38_material_impact_option_yes_checkbox": boolean, // 38a: Yes
  "p3_f38_material_impact_option_no_checkbox": boolean,  // 38b: No
  // Field 39: Has the institution's bonding company been notified?
  "p3_f39_bonding_company_notified_option_yes_checkbox": boolean, // 39a: Yes
  "p3_f39_bonding_company_notified_option_no_checkbox": boolean,  // 39b: No
  // Field 40: Has any law enforcement agency already been advised by telephone, written communication, or otherwise?
  "p3_f40a_agency_notified_dea_checkbox": boolean,           // 40a: DEA
  "p3_f40b_agency_notified_fbi_checkbox": boolean,           // 40b: FBI
  "p3_f40c_agency_notified_irs_checkbox": boolean,           // 40c: IRS
  "p3_f40d_agency_notified_postal_inspection_checkbox": boolean,// 40d: Postal Inspection
  "p3_f40e_agency_notified_secret_service_checkbox": boolean, // 40e: Secret Service
  "p3_f40f_agency_notified_us_customs_checkbox": boolean,     // 40f: U.S. Customs
  "p3_f40g_agency_notified_other_federal_checkbox": boolean,  // 40g: Other Federal
  "p3_f40h_agency_notified_state_checkbox": boolean,          // 40h: State
  "p3_f40i_agency_notified_local_checkbox": boolean,          // 40i: Local
  "p3_f40j_agency_name_provided_checkbox": boolean,           // 40j: Check if Agency Name provided below
  "p3_f40j_agency_name_text": string,                         // 40j: Agency Name (if g, h, or i checked)
  // Field 41-44: Law Enforcement Contact Information (if applicable)
  "p3_f41_law_enforcement_contact_1_name_text": string,       // Field 41: Contact Name 1
  "p3_f42_law_enforcement_contact_1_phone_area_code_text": string, // Field 42: Phone 1 Area Code
  "p3_f42_law_enforcement_contact_1_phone_number_text": string,  // Field 42: Phone 1 Number
  "p3_f43_law_enforcement_contact_2_name_text": string,       // Field 43: Contact Name 2
  "p3_f44_law_enforcement_contact_2_phone_area_code_text": string, // Field 44: Phone 2 Area Code
  "p3_f44_law_enforcement_contact_2_phone_number_text": string,  // Field 44: Phone 2 Number

  // --- Part IV: Contact for Assistance ---
  "p4_f45_assistance_contact_last_name_text": string,     // Field 45: Last Name
  "p4_f46_assistance_contact_first_name_text": string,    // Field 46: First Name
  "p4_f47_assistance_contact_middle_name_text": string,   // Field 47: Middle Name/Initial
  "p4_f48_assistance_contact_title_text": string,         // Field 48: Title
  // Field 49: Contact Phone Number
  "p4_f49_assistance_contact_phone_area_code_text": string, // 49: Area Code
  "p4_f49_assistance_contact_phone_number_text": string,    // 49: Number
  // Field 50: Date Prepared
  "p4_f50_date_prepared_month_text": string,           // 50: Month (MM)
  "p4_f50_date_prepared_day_text": string,             // 50: Day (DD)
  "p4_f50_date_prepared_year_text": string,            // 50: Year (YYYY)
  "p4_f51_filing_agency_name_if_not_institution_text": string, // Field 51: Agency name of filer (if not financial institution)

  // --- Part V: Suspicious Activity Narrative --- (Conceptual Field, not explicitly numbered on form page)
  "p5_fNA_narrative_text": string                      // Narrative Text: Describe WHO, WHAT, WHEN, WHERE, WHY, HOW
}

**Important:** The `field_mapping.py` script must be updated to map the original PDF field names (like 'item35a') to these new descriptive names (like 'p3_f35a_activity_type_bsa_structuring_checkbox').

Please generate the final output as a JSON object (no additional text).
"""

class SARGenerationAgent(BaseAgent):
    """Agent for generating Suspicious Activity Reports from anomaly detection data."""

    def __init__(self, client):
        """Initialize the SAR generation agent.

        Args:
            client: API client for model access
        """
        super().__init__(client)
        self.system_prompt = SYSTEM_PROMPT

    def run(self, input_data):
        """Generate a Suspicious Activity Report from anomaly detection data.

        Args:
            input_data: Either anomaly detection data alone or a dictionary containing
                       anomaly detection data and verification feedback

        Returns:
            A complete SAR report in JSON format using the descriptive field names.
        """
        # If input is a dictionary with verification feedback, extract and process
        if isinstance(input_data, dict) and "verification_feedback" in input_data:
            # Create a custom message including both anomaly data and feedback
            anomaly_data = input_data.get("anomaly_detection", {})
            verification_feedback = input_data.get("verification_feedback", {})

            # Prepare a structured input for the model
            combined_input = {
                "anomaly_detection": anomaly_data,
                "verification_feedback": verification_feedback,
                "instruction": "Please revise the SAR report based on the verification feedback, using the provided descriptive field names."
            }

            return super().run(combined_input)

        # Regular case - just anomaly detection data
        return super().run(input_data)
