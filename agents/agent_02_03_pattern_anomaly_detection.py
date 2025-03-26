import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# System Prompt remains the same
SYSTEM_PROMPT = """
Analyze financial transaction data to detect suspicious patterns and validate against historical patterns

PATTERN ANALYSIS:
- Flag transactions ≥ $5,000 with identifiable suspect
- Flag transactions ≥ $25,000 regardless of suspect
- Flag evidence of insider trading
- Flag BSA violations and money laundering
- Score anomalies as: very low, low, medium, high, very high
- Provide confidence ratings for detection methods
- Rank feature importance with direction (positive/negative)
- Summarize common patterns across transactions

ANOMALY DETECTION:
- Cross-check transactions with historical patterns
- Assign risk level: low, medium, high, or critical
- Evaluate false positive probability: low, medium, high
- Cite historical context and patterns used
- Provide explanation for each anomaly decision

JSON OUTPUT SCHEMA:
{
    "analyzed_transactions": [
        {
            "transaction_id": "string",
            "anomaly_score": "string (e.g., 'very low', 'low', 'medium', 'high', 'very high')",
            "is_suspicious": "boolean",
            "pattern_indicators": ["string"],
            "feature_importances": [
                {
                    "feature_name": "string",
                    "importance_value": "number",
                    "direction": "string (positive or negative)"
                }
            ],
            "risk_level": "string (low, medium, high, critical)",
            "false_positive": "string (low, medium, high)",
            "historical_citations": ["string"],
            "explanation": "string"
        }
    ],
    "analysis_summary": {
        "total_analyzed": "integer",
        "suspicious_count": "integer",
        "average_anomaly_score": "string (e.g., 'low', 'medium', 'high')",
        "common_patterns": ["string (optional)"],
        "flagged_count": "integer",
        "false_positives_filtered": "integer"
    }
}
"""

class PatternAnomalyDetectionAgent:
    """
    Agent for analyzing transaction patterns and detecting anomalies using an LLM.
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
        logger.debug("Calling Pattern Anomaly Detection API...")
        try:
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

    def run(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze transaction patterns and detect anomalies.

        Args:
            processed_data: Standardized transaction data from the ingestion agent.

        Returns:
            Combined analysis results conforming to the expected schema.

        Raises:
            TypeError: If input data cannot be formatted to JSON.
            ConnectionError: If the API call fails.
            ValueError: If the API response is invalid, incomplete, or cannot be parsed.
        """
        logger.info("Running Pattern Anomaly Detection Agent...")
        try:
            formatted_input = self._format_input(processed_data)
            logger.debug(f"Formatted Input for API (first 500 chars):\n{formatted_input[:500]}")

            api_response = self._call_api(formatted_input)
            parsed_response = self._parse_response(api_response)
            logger.info("Pattern Anomaly Detection Agent completed successfully.")
            return parsed_response

        except (TypeError, ConnectionError, ValueError) as e:
            logger.error(f"Pattern Anomaly Detection Agent failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Pattern Anomaly Detection Agent: {e}", exc_info=True)
            raise RuntimeError(f"Unexpected error during pattern analysis: {e}") from e
