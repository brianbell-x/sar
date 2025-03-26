import json
from typing import Any, Dict

# System Prompt remains the same
SYSTEM_PROMPT = """
Convert anomaly detection results into Suspicious Activity Reports in FLAT JSON format for direct PDF filling.

- Map anomaly data to all SAR PDF fields using exact field names below.
- Adhere to FinCEN regulatory requirements.
- Address verification feedback if provided.
- Include WHO, WHAT, WHEN, WHERE, WHY, HOW in the narrative field.
- File for: transactions ≥$5,000 (banks) or ≥$2,000 (MSBs), illegal funds, BSA evasion, no lawful purpose, criminal activity.

FLAT JSON OUTPUT SCHEMA:
{
  // --- Part I: Reporting Financial Institution Information ---
  "corrects_prior_report": boolean,                    // Field 1: Check if this corrects a prior report
  "financial_institution_name": string,                // Field 2: Name of Financial Institution
  "financial_institution_ein": string,                 // Field 3: Employer Identification Number (EIN)
  "financial_institution_address": string,             // Field 4: Address of Financial Institution
  // Field 5: Primary Federal Regulator
  "regulator_federal_reserve": boolean,                // 5a: Federal Reserve System (FRS)
  "regulator_fdic": boolean,                          // 5b: Federal Deposit Insurance Corporation (FDIC)
  "regulator_ncua": boolean,                          // 5c: National Credit Union Administration (NCUA)
  "regulator_occ": boolean,                           // 5d: Office of the Comptroller of the Currency (OCC)
  "regulator_ots": boolean,                           // 5e: Office of Thrift Supervision (OTS)
  "financial_institution_city": string,                // Field 6: City of Financial Institution
  "financial_institution_state_char1": string,         // Field 7: State (Character 1)
  "financial_institution_state_char2": string,         // Field 7: State (Character 2)
  // Field 8: ZIP Code (Institution)
  "financial_institution_zip_1": string,               // 8: Digit 1 (5-digit ZIP)
  "financial_institution_zip_2": string,               // 8: Digit 2
  "financial_institution_zip_3": string,               // 8: Digit 3
  "financial_institution_zip_4": string,               // 8: Digit 4
  "financial_institution_zip_5": string,               // 8: Digit 5
  "financial_institution_zip_plus4_1": string,         // 8: Digit 6 (+4 extension)
  "financial_institution_zip_plus4_2": string,         // 8: Digit 7 (+4 extension)
  "financial_institution_zip_plus4_3": string,         // 8: Digit 8 (+4 extension)
  "financial_institution_zip_plus4_4": string,         // 8: Digit 9 (+4 extension)
  "branch_address": string,                           // Field 9: Address of Branch Office(s) where activity occurred
  "multiple_branches_involved": boolean,               // Field 9: Check if multiple branches involved
  "branch_city": string,                              // Field 10: Branch City
  "branch_state_char1": string,                       // Field 11: Branch State (Character 1)
  "branch_state_char2": string,                       // Field 11: Branch State (Character 2)
  // Field 12: Branch ZIP Code
  "branch_zip_1": string,                             // 12: Digit 1 (5-digit ZIP)
  "branch_zip_2": string,                             // 12: Digit 2
  "branch_zip_3": string,                             // 12: Digit 3
  "branch_zip_4": string,                             // 12: Digit 4
  "branch_zip_5": string,                             // 12: Digit 5
  "branch_zip_plus4_1": string,                       // 12: Digit 6 (+4 extension)
  "branch_zip_plus4_2": string,                       // 12: Digit 7 (+4 extension)
  "branch_zip_plus4_3": string,                       // 12: Digit 8 (+4 extension)
  "branch_zip_plus4_4": string,                       // 12: Digit 9 (+4 extension)
  // Field 13: Date Institution Closed (if applicable)
  "institution_closed_date_month": string,            // 13: Month (MM)
  "institution_closed_date_day": string,              // 13: Day (DD)
  "institution_closed_date_year": string,             // 13: Year (YYYY)
  // Field 14: Account number(s) affected, if any
  "affected_account_1_number": string,                // 14a: Account Number 1
  "affected_account_1_closed_yes": boolean,           // 14a: Account 1 Closed? Yes
  "affected_account_1_closed_no": boolean,            // 14a: Account 1 Closed? No
  "affected_account_2_number": string,                // 14b: Account Number 2
  "affected_account_2_closed_yes": boolean,           // 14b: Account 2 Closed? Yes
  "affected_account_2_closed_no": boolean,            // 14b: Account 2 Closed? No
  "affected_account_3_number": string,                // 14c: Account Number 3
  "affected_account_3_closed_yes": boolean,           // 14c: Account 3 Closed? Yes
  "affected_account_3_closed_no": boolean,            // 14c: Account 3 Closed? No
  "affected_account_4_number": string,                // 14d: Account Number 4
  "affected_account_4_closed_yes": boolean,           // 14d: Account 4 Closed? Yes
  "affected_account_4_closed_no": boolean,            // 14d: Account 4 Closed? No

  // --- Part II: Suspect Information ---
  "suspect_info_unavailable": boolean,                // Checkbox above Field 15: Check if Suspect Info Unavailable
  "suspect_last_name_or_entity": string,              // Field 15: Last Name or Entity Name
  "suspect_first_name": string,                       // Field 16: First Name
  "suspect_middle_name": string,                      // Field 17: Middle Name/Initial
  "suspect_address": string,                          // Field 18: Address
  "suspect_ssn_ein_tin": string,                      // Field 19: SSN or EIN or ITIN
  "suspect_city": string,                             // Field 20: City
  "suspect_state_char1": string,                      // Field 21: State (Character 1)
  "suspect_state_char2": string,                      // Field 21: State (Character 2)
  // Field 22: Suspect ZIP Code
  "suspect_zip_1": string,                            // 22: Digit 1 (5-digit ZIP)
  "suspect_zip_2": string,                            // 22: Digit 2
  "suspect_zip_3": string,                            // 22: Digit 3
  "suspect_zip_4": string,                            // 22: Digit 4
  "suspect_zip_5": string,                            // 22: Digit 5
  "suspect_zip_plus4_1": string,                      // 22: Digit 6 (+4 extension)
  "suspect_zip_plus4_2": string,                      // 22: Digit 7 (+4 extension)
  "suspect_zip_plus4_3": string,                      // 22: Digit 8 (+4 extension)
  "suspect_zip_plus4_4": string,                      // 22: Digit 9 (+4 extension)
  "suspect_country": string,                          // Field 23: Country
  // Field 24: Suspect Phone Number - Residence
  "suspect_phone_residence_area_code": string,        // 24: Area Code (3 digits)
  "suspect_phone_residence_number": string,           // 24: Number (7 digits)
  // Field 25: Suspect Phone Number - Work
  "suspect_phone_work_area_code": string,             // 25: Area Code (3 digits)
  "suspect_phone_work_number": string,                // 25: Number (7 digits)
  "suspect_occupation_or_business": string,           // Field 26: Occupation or Type of Business
  // Field 27: Suspect Date of Birth
  "suspect_dob_month": string,                        // 27: Month (MM)
  "suspect_dob_day": string,                          // 27: Day (DD)
  "suspect_dob_year": string,                         // 27: Year (YYYY)
  // Field 28: Admission/Confession
  "suspect_admission_yes": boolean,                   // 28a: Yes
  "suspect_admission_no": boolean,                    // 28b: No
  // Field 29: Form(s) of Identification for Suspect
  "suspect_id_drivers_license": boolean,              // 29a: Driver's License/State ID
  "suspect_id_passport": boolean,                     // 29b: Passport
  "suspect_id_alien_registration": boolean,           // 29c: Alien Registration
  "suspect_id_other": boolean,                        // 29d: Other
  "suspect_id_number_part1": string,                  // 29: Number (part 1)
  "suspect_id_number_part2": string,                  // 29: Number (part 2)
  "suspect_id_issuing_authority": string,             // 29: Issuing Authority (State/Country)
  // Field 30: Relationship to Financial Institution
  "relationship_accountant": boolean,                 // 30a: Accountant
  "relationship_agent": boolean,                      // 30b: Agent
  "relationship_appraiser": boolean,                  // 30c: Appraiser
  "relationship_attorney": boolean,                   // 30d: Attorney
  "relationship_borrower": boolean,                   // 30e: Borrower
  "relationship_broker": boolean,                     // 30f: Broker
  "relationship_customer": boolean,                   // 30g: Customer
  "relationship_director": boolean,                   // 30h: Director
  "relationship_employee": boolean,                   // 30i: Employee
  "relationship_officer": boolean,                    // 30j: Officer
  "relationship_shareholder": boolean,                // 30k: Shareholder
  "relationship_other": boolean,                      // 30l: Other
  "relationship_other_description": string,           // 30l: Other Relationship Description
  // Field 31: Is the relationship an insider relationship?
  "insider_relationship_yes": boolean,                // 31a: Yes
  "insider_relationship_no": boolean,                 // 31b: No
  // Field 31: If Yes (insider), specify current status:
  "insider_status_still_employed": boolean,           // 31c: Still Employed
  "insider_status_suspended": boolean,                // 31d: Suspended
  "insider_status_terminated": boolean,               // 31e: Terminated
  "insider_status_resigned": boolean,                 // 31f: Resigned
  // Field 32: Date of Suspension, Termination, Resignation (if applicable)
  "insider_status_date_month": string,                // 32: Month (MM)
  "insider_status_date_day": string,                  // 32: Day (DD)
  "insider_status_date_year": string,                 // 32: Year (YYYY)

  // --- Part III: Suspicious Activity Information ---
  // Field 33: Date or date range of suspicious activity
  "activity_date_from_month": string,                 // 33: From Month (MM)
  "activity_date_from_day": string,                   // 33: From Day (DD)
  "activity_date_from_year": string,                  // 33: From Year (YYYY)
  "activity_date_to_month": string,                   // 33: To Month (MM)
  "activity_date_to_day": string,                     // 33: To Day (DD)
  "activity_date_to_year": string,                    // 33: To Year (YYYY)
  // Field 34: Total dollar amount involved in known or suspicious activity
  "total_amount_digit1": string,                      // 34: Digit 1 (Least significant)
  "total_amount_digit2": string,                      // 34: Digit 2
  "total_amount_digit3": string,                      // 34: Digit 3
  "total_amount_digit4": string,                      // 34: Digit 4
  "total_amount_digit5": string,                      // 34: Digit 5
  "total_amount_digit6": string,                      // 34: Digit 6
  "total_amount_digit7": string,                      // 34: Digit 7
  "total_amount_digit8": string,                      // 34: Digit 8
  "total_amount_digit9": string,                      // 34: Digit 9
  "total_amount_digit10": string,                     // 34: Digit 10
  "total_amount_digit11": string,                     // 34: Digit 11 (Most significant)
  // Field 35: Summary characterization of suspicious activity
  "activity_bsa_structuring_money_laundering": boolean, // 35a: Bank Secrecy Act/Structuring
  "activity_bribery_gratuity": boolean,               // 35b: Bribery/Gratuity
  "activity_check_fraud": boolean,                    // 35c: Check Fraud
  "activity_check_kiting": boolean,                   // 35d: Check Kiting
  "activity_commercial_loan_fraud": boolean,          // 35e: Commercial Loan Fraud
  "activity_computer_intrusion": boolean,             // 35f: Computer Intrusion
  "activity_consumer_loan_fraud": boolean,            // 35g: Consumer Loan Fraud
  "activity_counterfeit_check": boolean,              // 35h: Counterfeit Check
  "activity_counterfeit_credit_debit_card": boolean,  // 35i: Counterfeit Credit/Debit Card
  "activity_counterfeit_instrument_other": boolean,   // 35j: Counterfeit Instrument (other)
  "activity_credit_card_fraud": boolean,              // 35k: Credit Card Fraud
  "activity_debit_card_fraud": boolean,               // 35l: Debit Card Fraud
  "activity_defalcation_embezzlement": boolean,       // 35m: Defalcation/Embezzlement
  "activity_false_statement": boolean,                // 35n: False Statement
  "activity_misuse_position_self_dealing": boolean,   // 35o: Misuse of Position or Self Dealing
  "activity_mortgage_loan_fraud": boolean,            // 35p: Mortgage Loan Fraud
  "activity_mysterious_disappearance": boolean,       // 35q: Mysterious Disappearance
  "activity_wire_transfer_fraud": boolean,            // 35r: Wire Transfer Fraud
  "activity_other": boolean,                          // 35s: Other
  "activity_other_description": string,               // 35s: Other Activity Description
  "activity_terrorist_financing": boolean,            // 35t: Terrorist Financing
  "activity_identity_theft": boolean,                 // 35u: Identity Theft
  // Field 36: Amount of loss prior to recovery (if applicable)
  "loss_amount_digit1": string,                       // 36: Digit 1 (Least significant)
  "loss_amount_digit2": string,                       // 36: Digit 2
  "loss_amount_digit3": string,                       // 36: Digit 3
  "loss_amount_digit4": string,                       // 36: Digit 4
  "loss_amount_digit5": string,                       // 36: Digit 5
  "loss_amount_digit6": string,                       // 36: Digit 6
  "loss_amount_digit7": string,                       // 36: Digit 7
  "loss_amount_digit8": string,                       // 36: Digit 8 (Most significant)
  // Field 37: Dollar amount of recovery (if applicable)
  "recovery_amount_digit1": string,                   // 37: Digit 1 (Least significant)
  "recovery_amount_digit2": string,                   // 37: Digit 2
  "recovery_amount_digit3": string,                   // 37: Digit 3
  "recovery_amount_digit4": string,                   // 37: Digit 4
  "recovery_amount_digit5": string,                   // 37: Digit 5
  "recovery_amount_digit6": string,                   // 37: Digit 6
  "recovery_amount_digit7": string,                   // 37: Digit 7
  "recovery_amount_digit8": string,                   // 37: Digit 8
  "recovery_amount_digit9": string,                   // 37: Digit 9 (Most significant)
  // Field 38: Has the suspicious activity had a material impact?
  "material_impact_yes": boolean,                     // 38a: Yes
  "material_impact_no": boolean,                      // 38b: No
  // Field 39: Has the institution's bonding company been notified?
  "bonding_company_notified_yes": boolean,            // 39a: Yes
  "bonding_company_notified_no": boolean,             // 39b: No
  // Field 40: Has any law enforcement agency already been advised?
  "notified_dea": boolean,                           // 40a: DEA
  "notified_fbi": boolean,                           // 40b: FBI
  "notified_irs": boolean,                           // 40c: IRS
  "notified_postal_inspection": boolean,              // 40d: Postal Inspection
  "notified_secret_service": boolean,                 // 40e: Secret Service
  "notified_us_customs": boolean,                     // 40f: U.S. Customs
  "notified_other_federal": boolean,                  // 40g: Other Federal
  "notified_state": boolean,                          // 40h: State
  "notified_local": boolean,                          // 40i: Local
  "agency_name_provided": boolean,                    // 40j: Check if Agency Name provided below
  "law_enforcement_agency_name": string,              // 40j: Agency Name (if g, h, or i checked)
  // Field 41-44: Law Enforcement Contact Information
  "law_enforcement_contact_1_name": string,           // Field 41: Contact Name 1
  "law_enforcement_contact_1_phone_area": string,     // Field 42: Phone 1 Area Code
  "law_enforcement_contact_1_phone_number": string,   // Field 42: Phone 1 Number
  "law_enforcement_contact_2_name": string,           // Field 43: Contact Name 2
  "law_enforcement_contact_2_phone_area": string,     // Field 44: Phone 2 Area Code
  "law_enforcement_contact_2_phone_number": string,   // Field 44: Phone 2 Number

  // --- Part IV: Contact for Assistance ---
  "contact_last_name": string,                        // Field 45: Last Name
  "contact_first_name": string,                       // Field 46: First Name
  "contact_middle_name": string,                      // Field 47: Middle Name/Initial
  "contact_title": string,                            // Field 48: Title
  // Field 49: Contact Phone Number
  "contact_phone_area_code": string,                  // 49: Area Code
  "contact_phone_number": string,                     // 49: Number
  // Field 50: Date Prepared
  "date_prepared_month": string,                      // 50: Month (MM)
  "date_prepared_day": string,                        // 50: Day (DD)
  "date_prepared_year": string,                       // 50: Year (YYYY)
  "filing_agency_name": string,                       // Field 51: Agency name of filer

  // --- Part V: Suspicious Activity Narrative ---
  "narrative_text": string                            // Narrative Text: Describe WHO, WHAT, WHEN, WHERE, WHY, HOW
}

Please generate the final output as a JSON object (no additional text).
"""

class SARGenerationAgent:
    """
    Agent for generating Suspicious Activity Reports from anomaly detection data.
    (Simplified: No BaseAgent inheritance)
    """

    def __init__(self, client):
        """Initialize the agent.

        Args:
            client: OpenAI client instance.
        """
        self.client = client

    def _format_input(self, input_data: Any) -> str:
        """Format the input data for the API."""
        if isinstance(input_data, dict):
            return json.dumps(input_data)
        return str(input_data)

    def _call_api(self, user_content_str: str) -> Any:
        """Call the OpenAI Responses API."""
         # Simple check to suggest JSON format if not obviously present
        if "json" not in user_content_str.lower():
             user_content_str = f"{user_content_str}\nPlease provide the response in JSON format."

        response = self.client.responses.create(
            model="o3-mini-2025-01-31",
            instructions=SYSTEM_PROMPT,
            input=user_content_str,
            text={"format": {"type": "json_object"}},
            reasoning={"effort": "high"},
            tools=[],
            store=True
        )
        return response

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """Extract and parse the JSON response content."""
        if response.status != "completed":
            error_msg = f"Response status: {response.status}"
            if response.error:
                error_msg = f"API Error: {response.error}"
            elif response.incomplete_details:
                error_msg = f"Incomplete response: {response.incomplete_details}"
            raise Exception(error_msg)

        if not response.output or len(response.output) == 0:
            raise Exception("No output items returned from the API")

        for item in response.output:
            if hasattr(item, 'type') and item.type == "message":
                if hasattr(item, 'content') and item.content and len(item.content) > 0:
                    content_block = item.content[0]
                    if hasattr(content_block, 'text'):
                        raw_text = content_block.text
                        try:
                            return json.loads(raw_text)
                        except json.JSONDecodeError as e:
                             raise Exception(f"Failed to parse JSON response: {e}\nRaw text: {raw_text}")

        raise Exception("No message-type output items found in response")

    def run(self, input_data: Any) -> Dict[str, Any]:
        """
        Generate a Suspicious Activity Report from anomaly detection data,
        potentially including verification feedback.

        Args:
            input_data: Either anomaly detection data alone or a dictionary containing
                       anomaly detection data and verification feedback.

        Returns:
            A complete SAR report in JSON format using the descriptive field names.
        """
        final_input_data = input_data

        # If input is a dictionary with verification feedback, prepare combined input
        if isinstance(input_data, dict) and "verification_feedback" in input_data:
            anomaly_data = input_data.get("anomaly_detection", {})
            verification_feedback = input_data.get("verification_feedback", {})

            # Structure input for the model to understand context
            final_input_data = {
                "anomaly_detection": anomaly_data,
                "verification_feedback": verification_feedback,
                "instruction": "Please revise the SAR report based on the verification feedback, using the provided descriptive field names. Output only the revised FLAT JSON SAR."
            }

        # Format, call API, and parse response
        formatted_input = self._format_input(final_input_data)
        api_response = self._call_api(formatted_input)
        parsed_response = self._parse_response(api_response)
        return parsed_response