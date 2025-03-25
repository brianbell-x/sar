from agents.base_agent import BaseAgent

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


class PatternAnomalyDetectionAgent(BaseAgent):
    def __init__(self, client):
        """Initialize the combined Pattern Analysis and Anomaly Detection Agent.

        Args:
            client: The client interface.
            model: The LLM model identifier.
        """
        super().__init__(client)
        self.system_prompt = SYSTEM_PROMPT

    def run(self, processed_data):
        """Analyze transaction patterns and detect anomalies in a single pass.
        
        This combined agent:
        1. Analyzes transaction patterns using reasoning strategies
        2. Computes anomaly scores and identifies suspicious behavior
        3. Cross-checks transactions against historical patterns
        4. Assigns risk levels and evaluates false positive probability
        5. Provides explanations for each anomaly decision
        
        Args:
            processed_data: Standardized transaction data.
        
        Returns:
            Combined analysis results conforming to the expected schema.
        """
        return super().run(processed_data)
