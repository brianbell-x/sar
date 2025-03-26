import logging
import os
from typing import Any, Dict, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFFillingAgent:
    """
    Agent for filling SAR PDF forms using standardized data.
    Handles PDF generation and file system operations.
    """

    def __init__(self):
        """Initialize the PDF filling agent."""
        logger.info("Initializing PDF Filling Agent")

    def run(self, 
            sar_data: Dict[str, Any],
            template_path: str = "resources/6710-06.pdf",
            output_dir: str = "output",
            field_info_path: str = "resources/field_analysis_descriptive.json") -> Optional[str]:
        """
        Fill a SAR PDF form with the provided data.

        Args:
            sar_data: SAR data in standardized format from SARGenerationAgent
            template_path: Path to blank PDF template
            output_dir: Directory to save filled PDFs
            field_info_path: Path to field mapping JSON

        Returns:
            Path to generated PDF file if successful, None otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Generate timestamped output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"sar_report_{timestamp}.pdf")

            logger.info(f"Filling PDF template at {template_path}")
            logger.debug(f"Using field info from {field_info_path}")

            # Import PDF filling function dynamically
            from resources.new_pdf_filler import fill_sar_pdf
            
            fill_sar_pdf(
                data=sar_data,
                template_path=template_path,
                output_path=output_path,
                field_info_path=field_info_path
            )

            logger.info(f"Successfully generated SAR PDF at {output_path}")
            return output_path

        except ImportError as e:
            logger.error(f"Failed to import PDF filling module: {e}")
        except FileNotFoundError as e:
            logger.error(f"Required file not found: {e}")
        except Exception as e:
            logger.error(f"Error filling PDF: {e}", exc_info=True)

        return None

# Example usage for testing
if __name__ == "__main__":
    # Minimal test data matching SAR schema
    test_data = {
        "financial_institution_name": "Test Bank",
        "financial_institution_ein": "123456789",
        "narrative_text": "Test suspicious activity report",
        # Add other required fields...
    }

    agent = PDFFillingAgent()
    result = agent.run(test_data)
    
    if result:
        print(f"Test successful! PDF generated at: {result}")
    else:
        print("Test failed")
