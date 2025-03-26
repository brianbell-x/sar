# File: agents/agent_07_pdf_filling.py
import logging
import os
from typing import Any, Dict, Optional
from datetime import datetime
# Import the simplified filler function
from resources.new_pdf_filler import fill_sar_pdf

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFFillingAgent:
    """
    Agent for filling SAR PDF forms using standardized data and a template
    that has DESCRIPTIVE field names (pre-processed by update_field_names.py).
    """
    DEFAULT_TEMPLATE = "resources/6710-06_descriptive.pdf"
    DEFAULT_OUTPUT_DIR = "output"

    def __init__(self):
        """Initialize the PDF filling agent."""
        logger.info("Initializing PDF Filling Agent")

    def run(self,
            sar_data: Dict[str, Any],
            template_path: str = DEFAULT_TEMPLATE,
            output_dir: str = DEFAULT_OUTPUT_DIR) -> Optional[str]:
        """
        Fill a SAR PDF form (with descriptive names) using the provided data.

        Args:
            sar_data: SAR data in standardized format (dict with descriptive keys)
                      from SARGenerationAgent.
            template_path: Path to the modified PDF template with descriptive field names.
            output_dir: Directory to save the filled PDF.

        Returns:
            Path to the generated PDF file if successful, None otherwise.
        """
        try:
            # --- Pre-computation/Validation ---
            if not os.path.exists(template_path):
                logger.error(f"PDF template not found at '{template_path}'.")
                logger.error("Ensure you have run 'update_field_names.py' to create this file.")
                return None

            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Generate timestamped output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"sar_report_filled_{timestamp}.pdf"
            output_path = os.path.join(output_dir, output_filename)

            logger.info(f"Attempting to fill PDF template: {template_path}")
            logger.info(f"Output will be saved to: {output_path}")
            logger.debug(f"Using SAR data with keys: {list(sar_data.keys())[:10]}...") # Log first few keys

            # --- Core Logic: Call the simplified filler ---
            fill_sar_pdf(
                data=sar_data,
                template_path=template_path,
                output_path=output_path
            )

            if os.path.exists(output_path):
                logger.info(f"Successfully generated SAR PDF at {output_path}")
                return output_path
            else:
                # This case should ideally not happen if fill_sar_pdf doesn't error, but check anyway
                logger.error(f"PDF filling process completed but output file not found at {output_path}")
                return None

        except ImportError as e:
            # Should not happen if file structure is correct
            logger.error(f"Failed to import PDF filling module: {e}", exc_info=True)
        except FileNotFoundError as e:
            # Already handled template not found, could be other FS issues
            logger.error(f"File system error during PDF filling: {e}", exc_info=True)
        except Exception as e:
            # Catch errors from fill_sar_pdf
            logger.error(f"Error during PDF filling process: {e}", exc_info=True)

        return None

# Example usage for testing (using the descriptive test data function)
if __name__ == "__main__":
    from resources.new_pdf_filler import create_test_data_descriptive # Use descriptive data

    print("--- PDF Filling Agent Test ---")
    # Minimal test data matching SAR schema (using descriptive keys)
    test_data = create_test_data_descriptive()
    print(f"Using test data with {len(test_data)} fields.")

    agent = PDFFillingAgent()
    # Use default template path expected by the agent
    result_path = agent.run(test_data)

    if result_path:
        print(f"\nTest successful! PDF generated at: {result_path}")
        # Try opening the file (platform dependent)
        # try:
        #     if os.name == 'nt': # Windows
        #         os.startfile(result_path)
        #     elif sys.platform == 'darwin': # macOS
        #         subprocess.call(('open', result_path))
        #     else: # Linux variants
        #         subprocess.call(('xdg-open', result_path))
        # except Exception as e:
        #      print(f"(Could not auto-open file: {e})")
    else:
        print("\nTest failed. Check logs for errors.")
        print(f"Ensure the template '{agent.DEFAULT_TEMPLATE}' exists.")