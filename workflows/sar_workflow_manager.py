import json
from typing import Dict, Optional
from agents.agent_05_sar_generation import SARGenerationAgent
from agents.agent_06_compliance_verification import ComplianceVerificationAgent

class SARWorkflowManager:
    """
    Manages the iterative SAR generation and verification workflow.
    Handles the loop between SAR generation and compliance verification.
    """
    
    def __init__(self, client, max_iterations: int = 3):
        """Initialize with client and max iterations."""
        self.sar_agent = SARGenerationAgent(client)
        self.verification_agent = ComplianceVerificationAgent(client)
        self.max_iterations = max_iterations

    def run(self, analysis_results: Dict) -> Dict:
        """
        Run the iterative SAR generation and verification workflow.
        
        Args:
            analysis_results: Output from anomaly detection agent
            
        Returns:
            Dictionary containing:
            - final_sar_report: The last generated SAR report
            - final_verification: The last verification result
            - iteration_results: List of all iteration results
            - status: Final status (approved, needs_revision, rejected)
        """
        iteration_results = []
        sar_report = None
        verification_result = None
        status = "needs_generation"

        for iteration in range(self.max_iterations):
            # Generate or revise SAR
            if status in ["needs_generation", "needs_revision"]:
                input_data = {
                    "anomaly_detection": analysis_results,
                    "verification_feedback": verification_result if verification_result else None,
                    "instruction": f"Please {'revise' if iteration > 0 else 'generate'} the SAR report"
                }
                sar_report = self.sar_agent.run(input_data)

            # Verify compliance
            verification_result = self.verification_agent.run(sar_report)
            status = verification_result.get("verification_result", {}).get("verification_status", "error")

            # Store iteration results
            iteration_results.append({
                "iteration": iteration + 1,
                "sar_report": sar_report,
                "verification_result": verification_result,
                "status": status
            })

            # Check termination conditions
            if status == "approved":
                break
            elif status == "rejected":
                break

        return {
            "final_sar_report": sar_report,
            "final_verification": verification_result,
            "iteration_results": iteration_results,
            "status": status
        }
