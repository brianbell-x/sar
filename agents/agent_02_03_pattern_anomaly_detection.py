import json
from typing import Any, Dict

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

    def run(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze transaction patterns and detect anomalies.

        Args:
            processed_data: Standardized transaction data from the ingestion agent.

        Returns:
            Combined analysis results conforming to the expected schema.
        """
        formatted_input = self._format_input(processed_data)
        api_response = self._call_api(formatted_input)
        parsed_response = self._parse_response(api_response)
        return parsed_response