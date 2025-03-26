import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# System Prompt remains the same
SYSTEM_PROMPT = """
Validate SAR reports against FinCEN requirements

- Check required fields and format compliance
- Verify WHO, WHAT, WHEN, WHERE, WHY, HOW elements
- Flag missing or inconsistent information
- Assess narrative quality
- Evaluate supporting evidence
- Assign compliance score (0-100)
- Set verification status: approved, needs_revision, rejected
- Identify issues by section, type, severity
- Provide recommendations for corrections

JSON OUTPUT SCHEMA:
{
    "verification_result": {
        "report_id": "string",
        "verification_timestamp": "string (ISO 8601 date-time format)",
        "is_compliant": "boolean",
        "compliance_score": "number (optional)",
        "verification_status": "string (approved, needs_revision, rejected)",
        "ready_for_submission": "boolean"
    },
    "fincen_requirements": {
        "required_fields_present": "boolean",
        "format_compliance": "boolean",
        "narrative_quality": "string (excellent, good, adequate, inadequate)",
        "supporting_evidence_sufficient": "boolean (optional)"
    },
    "issues": [
        {
            "section": "string",
            "issue_type": "string (missing_information, format_error, inconsistency, insufficient_detail)",
            "description": "string",
            "severity": "string (critical, major, minor)",
            "recommendation": "string (optional)"
        }
    ],
    "llm_verification": {
        "completeness_assessment": "string",
        "accuracy_assessment": "string",
        "consistency_check": "string (optional)",
        "overall_quality": "string (excellent, good, adequate, inadequate)"
    },
    "verification_summary": "string"
}
"""

class ComplianceVerificationAgent:
    """
    Agent for verifying SAR report compliance with FinCEN requirements using an LLM.
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
        try:
            if isinstance(input_data, dict):
                return json.dumps(input_data, indent=2)
            return str(input_data)
        except TypeError as e:
            logger.error(f"Failed to format input data: {e}")
            raise TypeError(f"Input data formatting failed: {e}") from e

    def _call_api(self, user_content_str: str) -> Any:
        """Call the OpenAI Responses API."""
        logger.debug("Calling Compliance Verification API...")
        try:
            # Simple check to suggest JSON format if not obviously present
            if "json" not in user_content_str.lower():
                 user_content_str = f"{user_content_str}\nPlease provide the response in JSON format."

            response = self.client.responses.create(
                model='o3-mini-2025-01-31',
                instructions=SYSTEM_PROMPT,
                input=user_content_str,
                text={"format": {"type": "json_object"}},
                reasoning={"effort": "high"},
                tools=[],
                store=True
            )
            logger.debug(f"API Response Status: {response.status}")
            return response
        except Exception as e:
            logger.error(f"API call failed: {e}", exc_info=True)
            raise ConnectionError(f"Failed to communicate with OpenAI API: {e}") from e

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """Extract and parse the JSON response content."""
        if response.status != "completed":
            error_msg = f"API response status not completed: {response.status}"
            if response.error:
                error_msg = f"API Error: {response.error}"
            elif response.incomplete_details:
                error_msg = f"Incomplete response: {response.incomplete_details}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if not response.output or len(response.output) == 0:
            logger.error("No output items returned from the API")
            raise ValueError("No output items returned from the API")

        # Iterate through output items to find the message content
        for item in response.output:
            if hasattr(item, 'type') and item.type == "message":
                if hasattr(item, 'content') and item.content and len(item.content) > 0:
                    content_block = item.content[0]
                    if hasattr(content_block, 'text'):
                        raw_text = content_block.text
                        logger.debug(f"Raw API response text received:\n{raw_text[:500]}...")
                        try:
                            parsed_json = json.loads(raw_text)
                            if not isinstance(parsed_json, dict):
                                raise ValueError("Parsed JSON is not a dictionary.")
                            return parsed_json
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON response: {e}\nRaw text sample: {raw_text[:500]}...")
                            raise ValueError(f"Failed to parse JSON response: {e}") from e
                        except ValueError as ve:
                            logger.error(f"Parsed JSON validation failed: {ve}")
                            raise

        logger.error("No message-type output item with text content found in API response.")
        raise ValueError("No message-type output items found in response")

    def run(self, sar_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify SAR report compliance against FinCEN requirements.

        Args:
            sar_report: SAR report generated by the SAR Generation Agent.

        Returns:
            Verification results with compliance assessment and issues.

        Raises:
            TypeError: If input data cannot be formatted to JSON.
            ConnectionError: If the API call fails.
            ValueError: If the API response is invalid, incomplete, or cannot be parsed.
        """
        logger.info("Running Compliance Verification Agent...")
        try:
            formatted_input = self._format_input(sar_report)
            logger.debug(f"Formatted Input for API (first 500 chars):\n{formatted_input[:500]}")

            api_response = self._call_api(formatted_input)
            parsed_response = self._parse_response(api_response)
            logger.info("Compliance Verification Agent completed successfully.")
            return parsed_response

        except (TypeError, ConnectionError, ValueError) as e:
            logger.error(f"Compliance Verification Agent failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Compliance Verification Agent: {e}", exc_info=True)
            raise RuntimeError(f"Unexpected error during compliance verification: {e}") from e
