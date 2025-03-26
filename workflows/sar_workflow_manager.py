import json
import logging
from typing import Dict, Optional, List, Tuple
from agents.agent_05_sar_generation import SARGenerationAgent
from agents.agent_06_compliance_verification import ComplianceVerificationAgent

logger = logging.getLogger(__name__)

class SARWorkflowManager:
    """
    Manages the iterative SAR generation and verification workflow.
    Handles the loop between SAR generation and compliance verification,
    using AI agents for both steps.
    """

    def __init__(self, client, max_iterations: int = 3):
        """
        Initialize the workflow manager.

        Args:
            client: OpenAI client instance.
            max_iterations: Maximum number of generation-verification cycles.
        """
        if not client:
            raise ValueError("OpenAI client is required.")
        self.sar_agent = SARGenerationAgent(client)
        self.verification_agent = ComplianceVerificationAgent(client)
        self.max_iterations = max(1, max_iterations) # Ensure at least 1 iteration
        logger.info(f"SARWorkflowManager initialized with max_iterations={self.max_iterations}")

    def run(self, analysis_results: Dict) -> Dict:
        """
        Run the iterative SAR generation and verification workflow.

        Args:
            analysis_results: Output from the PatternAnomalyDetectionAgent.
                              Expected to contain information about suspicious transactions.

        Returns:
            Dictionary containing the workflow execution summary:
            - "final_sar_report": The last generated SAR report (dict), or None if failed.
            - "final_verification": The last verification result (dict), or None if failed.
            - "iteration_results": List of dictionaries, each containing results
                                   from one iteration ('iteration', 'sar_report',
                                   'verification_result', 'status').
            - "final_status": Final status string ('approved', 'needs_revision', 'rejected', 'error').
            - "error_message": Optional error message if the workflow failed.
        """
        iteration_results: List[Dict] = []
        current_sar_report: Optional[Dict] = None
        last_verification_result: Optional[Dict] = None
        current_status: str = "needs_generation" # Initial status
        error_message: Optional[str] = None

        if not analysis_results or not isinstance(analysis_results, dict):
             logger.error("Invalid or empty analysis_results provided to SAR workflow.")
             return {
                 "final_sar_report": None,
                 "final_verification": None,
                 "iteration_results": [],
                 "final_status": "error",
                 "error_message": "Invalid input: analysis_results missing or not a dictionary."
             }

        for iteration in range(self.max_iterations):
            iteration_num = iteration + 1
            logger.info(f"--- Starting SAR Workflow Iteration {iteration_num}/{self.max_iterations} ---")
            iteration_data = {"iteration": iteration_num}

            try:
                # --- 1. Generate or Revise SAR ---
                if current_status in ["needs_generation", "needs_revision"]:
                    logger.info(f"Iteration {iteration_num}: Generating SAR (Status: {current_status})...")
                    # Prepare input for SAR agent, including previous feedback if available
                    input_data_for_sar = {
                        "anomaly_detection": analysis_results,
                        # Pass previous verification only if revision is needed
                        "verification_feedback": last_verification_result if current_status == "needs_revision" else None,
                        "instruction": (f"Please {'revise the SAR based on the feedback' if current_status == 'needs_revision' else 'generate the SAR'} "
                                        f"using the provided anomaly data. Ensure output is FLAT JSON with descriptive field names.")
                    }
                    current_sar_report = self.sar_agent.run(input_data_for_sar)
                    iteration_data["sar_report"] = current_sar_report
                    logger.info(f"Iteration {iteration_num}: SAR Generated/Revised.")
                    # Basic check on SAR report structure (optional but good)
                    if not current_sar_report or not isinstance(current_sar_report, dict):
                         raise ValueError("SAR Generation Agent returned invalid or empty report.")

                else:
                     # Should not happen if logic is correct, but handles unexpected states
                     logger.warning(f"Iteration {iteration_num}: Skipping SAR generation (Status: {current_status}).")
                     iteration_data["sar_report"] = current_sar_report # Keep previous report


                # --- 2. Verify Compliance ---
                if not current_sar_report:
                    # Cannot verify if SAR generation failed or was skipped inappropriately
                    raise ValueError("Cannot perform verification: SAR report is missing.")

                logger.info(f"Iteration {iteration_num}: Verifying SAR compliance...")
                last_verification_result = self.verification_agent.run(current_sar_report)
                iteration_data["verification_result"] = last_verification_result
                logger.info(f"Iteration {iteration_num}: Verification complete.")

                # Extract status from verification result
                current_status = last_verification_result.get("verification_result", {}).get("verification_status", "error")
                iteration_data["status"] = current_status
                logger.info(f"Iteration {iteration_num}: Verification Status = {current_status.upper()}")

                # Validate status
                if current_status not in ["approved", "needs_revision", "rejected"]:
                    logger.error(f"Iteration {iteration_num}: Invalid status '{current_status}' received from Verification Agent.")
                    current_status = "error" # Treat unexpected status as error
                    iteration_data["status"] = current_status
                    raise ValueError(f"Verification Agent returned unrecognized status: {current_status}")

            except Exception as e:
                logger.error(f"Error during SAR Workflow Iteration {iteration_num}: {e}", exc_info=True)
                error_message = f"Error in iteration {iteration_num}: {e}"
                iteration_data["status"] = "error"
                iteration_data["error"] = str(e)
                iteration_results.append(iteration_data) # Store partial iteration result
                current_status = "error" # Set final status to error
                break # Exit loop on error

            # --- Store Iteration Results ---
            iteration_results.append(iteration_data)

            # --- Check Termination Conditions ---
            if current_status == "approved":
                logger.info(f"Iteration {iteration_num}: SAR Approved. Workflow finished.")
                break
            elif current_status == "rejected":
                logger.info(f"Iteration {iteration_num}: SAR Rejected. Workflow finished.")
                break
            elif iteration_num == self.max_iterations and current_status == "needs_revision":
                logger.warning(f"Iteration {iteration_num}: Reached max iterations. Final status is 'needs_revision'.")
                # Status remains 'needs_revision'

        # --- Compile Final Results ---
        final_result = {
            "final_sar_report": current_sar_report,
            "final_verification": last_verification_result,
            "iteration_results": iteration_results,
            "final_status": current_status, # The status after the last successful iteration or 'error'
            "error_message": error_message
        }
        logger.info(f"SAR Workflow completed with final status: {final_result['final_status']}")
        return final_result