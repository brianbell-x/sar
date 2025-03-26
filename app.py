import streamlit as st
import json
import os
from openai import OpenAI
import dotenv
import time
import traceback # For detailed error logging

# --- Configuration ---
DEFAULT_SAMPLE_DATA = "sample_transactions.json"
DEFAULT_PDF_TEMPLATE = "resources/6710-06_descriptive.pdf" # Use the descriptive template
DEFAULT_OUTPUT_DIR = "output"
SESSION_STATE_SAR_DATA = "final_sar_data"
SESSION_STATE_FILLED_PDF_PATH = "filled_pdf_path"

# --- Secrets and API Key ---
# Using st.secrets which is preferred for deployment
api_key = st.secrets.get("api_key")
# Fallback to environment variable if not in secrets (useful for local dev)
if not api_key:
    dotenv.load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

# --- Agent Imports ---
AGENTS_LOADED = False
PDF_FILLER_LOADED = False
try:
    from agents.agent_01_data_ingestion import DataIngestionAgent
    from agents.agent_02_03_pattern_anomaly_detection import PatternAnomalyDetectionAgent
    from workflows.sar_workflow_manager import SARWorkflowManager
    AGENTS_LOADED = True
    # Import PDF filler agent separately to handle its potential absence gracefully
    try:
        from agents.agent_07_pdf_filling import PDFFillingAgent
        PDF_FILLER_LOADED = True
    except ImportError as pdf_e:
        st.warning(f"PDF Filling Agent not loaded: {pdf_e}. PDF generation will be unavailable.")

except ImportError as e:
    st.error(f"Failed to import core agents: {e}. Please ensure agent files exist and are importable.")
    # AGENTS_LOADED remains False

# --- Page Config ---
st.set_page_config(
    page_title="SAR AI Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Helper Functions ---
@st.cache_resource # Cache the client for the session
def create_client(api_key_input):
    """Create and configure the OpenAI API client."""
    if not api_key_input:
        st.error("API Key is missing. Cannot create AI client.")
        return None
    try:
        client = OpenAI(api_key=api_key_input)
        # Perform a simple test call if desired
        # client.models.list()
        return client
    except Exception as e:
        st.error(f"Failed to create or validate OpenAI client: {e}")
        return None

def load_sample_data(filepath=DEFAULT_SAMPLE_DATA):
    """Loads sample transaction data from a JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Error: Sample data file '{filepath}' not found.")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Error: Could not decode JSON from '{filepath}'. Invalid format near line {e.lineno}, column {e.colno}.")
        return None
    except Exception as e:
        st.error(f"Error loading sample data from '{filepath}': {str(e)}")
        return None

# --- Initialize Session State ---
if SESSION_STATE_SAR_DATA not in st.session_state:
    st.session_state[SESSION_STATE_SAR_DATA] = None
if SESSION_STATE_FILLED_PDF_PATH not in st.session_state:
    st.session_state[SESSION_STATE_FILLED_PDF_PATH] = None

# --- Sidebar ---
with st.sidebar:
    st.image("https://www.appliedaicourse.com/hubfs/Google%20Drive%20Integration/SAR%20AI%20Logo.png", width=80) # Placeholder logo
    st.markdown("# SAR AI Assistant")
    st.caption("Automated Suspicious Activity Reports")
    st.divider()

    # API Key Input (Moved here for better visibility)
    st.header("Configuration")
    if not api_key: # Only show input if not found in secrets/env
        api_key = st.text_input("Enter OpenAI API Key:", type="password", key="api_key_input", help="Required for AI agents.")
        if api_key:
             st.success("API Key provided.")
    else:
        st.success("API Key loaded.") # Indicate key is found

    st.divider()

    st.header("Data Input")
    input_option = st.radio(
        "Choose transaction data source:",
        ["Use Sample Data", "Upload Custom JSON File", "Enter Custom JSON Text"],
        key="data_input_method",
        # horizontal=True, # Consider removing horizontal if text wraps badly
        label_visibility="collapsed" # Hide the label
    )

    transaction_data = None
    data_load_status = st.empty() # Placeholder for data status message

    if input_option == "Use Sample Data":
        transaction_data = load_sample_data()
        if transaction_data:
            data_load_status.success("Sample data loaded.")
            with st.expander("View Sample Data"):
                st.json(transaction_data, expanded=False)
        else:
            data_load_status.error("Failed to load sample data.")


    elif input_option == "Upload Custom JSON File":
        uploaded_file = st.file_uploader("Upload JSON file", type=["json"], key="json_upload")
        if uploaded_file is not None:
            try:
                transaction_data = json.load(uploaded_file)
                data_load_status.success("File uploaded and parsed successfully.")
                custom_data_valid = True
            except json.JSONDecodeError as e:
                data_load_status.error(f"Invalid JSON format: Error near line {e.lineno}, col {e.colno}.")
            except Exception as e:
                data_load_status.error(f"Error reading file: {str(e)}")

    elif input_option == "Enter Custom JSON Text":
        try:
            with open(DEFAULT_SAMPLE_DATA, "r", encoding="utf-8") as f:
                default_data_str = f.read()
        except Exception:
            default_data_str = '{\n  "transactions": [\n    {\n      "transaction_id": "TX_EXAMPLE",\n      ...\n    }\n  ]\n}'

        transaction_data_str = st.text_area(
            "Paste JSON data here:",
            value=st.session_state.get("json_text_area_val", default_data_str), # Persist text area content
            height=250,
            key="json_text_area",
            help="Ensure the data follows the expected JSON structure, typically {'transactions': [...]}.",
            on_change=lambda: st.session_state.update(json_text_area_val=st.session_state.json_text_area) # Save on change
        )
        if transaction_data_str:
            try:
                transaction_data = json.loads(transaction_data_str)
                data_load_status.success("JSON data parsed successfully.")
                custom_data_valid = True
            except json.JSONDecodeError as e:
                data_load_status.error(f"Invalid JSON format: Error near line {e.lineno}, col {e.colno}.")
            except Exception as e:
                data_load_status.error(f"Error parsing JSON: {str(e)}")

    st.divider()

# --- Main Content Area ---
st.title("🛡️ SAR AI Workflow")
st.markdown("Automate the detection of suspicious activities and the generation of SARs.")

# --- Prerequisites Check ---
client = create_client(api_key) # Attempt to create client early for check
can_run_workflow = client and transaction_data and AGENTS_LOADED
run_button_disabled_reason = ""
if not client: run_button_disabled_reason += "AI Client (API Key) issue. "
if not transaction_data: run_button_disabled_reason += "Transaction data missing/invalid. "
if not AGENTS_LOADED: run_button_disabled_reason += "Core agent modules failed load. "

# --- Workflow Execution Button ---
if st.button("🚀 Run Full Workflow", type="primary", disabled=not can_run_workflow, use_container_width=True, key="run_workflow"):
    if not can_run_workflow: # Redundant check, but safe
        st.error(f"Cannot run workflow: {run_button_disabled_reason.strip()}")
    else:
        # Clear previous results from session state
        st.session_state[SESSION_STATE_SAR_DATA] = None
        st.session_state[SESSION_STATE_FILLED_PDF_PATH] = None

        # --- Workflow UI Setup ---
        st.markdown("---")
        st.markdown("### Workflow Progress")
        status_placeholder = st.empty()
        progress_bar = st.progress(0, text="Initializing...")

        # Step Visualization
        step_cols = st.columns(4) # Adjusted number of columns if needed
        step_placeholders = [col.container(border=True) for col in step_cols]
        steps_config = [
            {"name": "Data Ingestion", "icon": "📥", "placeholder": step_placeholders[0]},
            {"name": "Analysis & Detection", "icon": "🔬", "placeholder": step_placeholders[1]},
            {"name": "SAR Gen & Verify", "icon": "📝✅", "placeholder": step_placeholders[2]},
            {"name": "Final Outcome", "icon": "🏁", "placeholder": step_placeholders[3]},
        ]

        # Initialize step statuses in UI
        for i, step in enumerate(steps_config):
             with step["placeholder"]:
                 st.markdown(f"**{step['icon']} {step['name']}**")
                 step["status_widget"] = st.empty()
                 step["status_widget"].info("Pending...")
                 step["expander"] = st.expander("Details", expanded=False)

        # Helper to update step status and log errors
        def update_step_status(step_index, status, message=None, details=None, exception_info=None):
            if step_index >= len(steps_config): return # Safety check

            step = steps_config[step_index]
            current_status = ""
            if status == "running":
                current_status = f"Running... {message or ''}"
                step["status_widget"].info(current_status)
            elif status == "completed":
                current_status = "Completed"
                step["status_widget"].success(current_status)
            elif status == "failed":
                current_status = f"Failed"
                error_msg = f"{message or 'An error occurred.'}"
                step["status_widget"].error(current_status)
                with step["expander"]:
                    st.error(error_msg)
                    if exception_info:
                        st.code(exception_info, language="text") # Show traceback
                    if details:
                        st.write("Failure Details:")
                        st.json(details)
            elif status == "skipped":
                current_status = "Skipped"
                step["status_widget"].warning(current_status)

            logger.info(f"Step {step_index+1} ({step['name']}): {current_status}{f' - {message}' if message else ''}")
            if status == "failed":
                logger.error(f"Step {step_index+1} Failure: {message}\nDetails: {details}\nException:\n{exception_info}")

        # --- Workflow Execution Logic ---
        current_step_index = -1
        try:
            # --- Step 1: Data Ingestion ---
            current_step_index = 0
            step_name = steps_config[current_step_index]["name"]
            status_placeholder.info(f"Running: {step_name}...")
            update_step_status(current_step_index, "running")
            progress_bar.progress(5, text=f"Running {step_name}...")
            time.sleep(0.1) # Visual feedback

            data_ingestion_agent = DataIngestionAgent()
            processed_data = data_ingestion_agent.run(transaction_data)
            if not processed_data or not processed_data.get("transactions"):
                 raise ValueError("Data Ingestion returned no valid transactions.")

            update_step_status(current_step_index, "completed")
            with steps_config[current_step_index]["expander"]:
                st.write("Standardized Transaction Data (Sample):")
                st.json({"transactions": processed_data["transactions"][:3]}, expanded=True) # Show only first few
                st.caption(f"Total processed: {len(processed_data['transactions'])}")
            progress_bar.progress(20, text=f"{step_name} Completed.")

            # --- Step 2: Pattern Analysis & Anomaly Detection ---
            current_step_index = 1
            step_name = steps_config[current_step_index]["name"]
            status_placeholder.info(f"Running: {step_name}...")
            update_step_status(current_step_index, "running", message="Calling AI Model...")
            progress_bar.progress(25, text=f"Running {step_name}...")

            pattern_anomaly_detection_agent = PatternAnomalyDetectionAgent(client)
            analysis_results = pattern_anomaly_detection_agent.run(processed_data)
            # Basic validation of results structure
            if not analysis_results or "analyzed_transactions" not in analysis_results:
                 raise ValueError("Analysis & Detection did not return expected 'analyzed_transactions'.")


            update_step_status(current_step_index, "completed")
            with steps_config[current_step_index]["expander"]:
                st.write("Analysis & Detection Results:")
                # Show summary first
                summary = analysis_results.get("analysis_summary", {})
                if summary:
                    metric_cols = st.columns(3)
                    metric_cols[0].metric("Total Analyzed", summary.get("total_analyzed", "N/A"))
                    metric_cols[1].metric("Flagged Suspicious", summary.get("suspicious_count", "N/A"))
                    # Adjust how average score is displayed if it's text
                    avg_score = summary.get("average_anomaly_score", "N/A")
                    metric_cols[2].metric("Avg. Anomaly Score", avg_score.capitalize() if isinstance(avg_score, str) else avg_score)
                    st.write("---")
                # Show sample transaction analysis
                st.json({"analyzed_transactions_sample": analysis_results["analyzed_transactions"][:2]}, expanded=True)
                st.caption(f"Full results contain {len(analysis_results['analyzed_transactions'])} analyzed transactions.")

            progress_bar.progress(50, text=f"{step_name} Completed.")


            # --- Step 3: SAR Generation & Verification Workflow ---
            current_step_index = 2
            step_name = steps_config[current_step_index]["name"]
            status_placeholder.info(f"Running: {step_name} (May involve multiple AI calls)...")
            update_step_status(current_step_index, "running", message="Starting iterative process...")
            progress_bar.progress(55, text=f"Running {step_name}...")

            workflow_manager = SARWorkflowManager(client, max_iterations=3) # Allow configuring max iterations
            workflow_results = workflow_manager.run(analysis_results)

            # Store final SAR data in session state for potential PDF filling
            final_sar_data = workflow_results.get("final_sar_report")
            if final_sar_data:
                st.session_state[SESSION_STATE_SAR_DATA] = final_sar_data

            update_step_status(current_step_index, "completed")
            with steps_config[current_step_index]["expander"]:
                st.write("SAR Workflow Iteration Results:")
                st.json(workflow_results, expanded=True) # Show full workflow results here
            progress_bar.progress(85, text=f"{step_name} Completed.")


            # --- Step 4: Final Outcome ---
            current_step_index = 3
            step_name = steps_config[current_step_index]["name"]
            status_placeholder.success("Workflow Finished.")
            update_step_status(current_step_index, "running", message="Determining final status...") # Use running briefly
            progress_bar.progress(90, text="Determining Final Outcome...")

            verification_status = workflow_results.get("final_status", "error") # Use final_status key
            iteration_results = workflow_results.get("iteration_results", [])
            num_iterations = len(iteration_results)

            outcome_message = ""
            outcome_status_func = st.info # Default

            if verification_status == "approved":
                outcome_message = f"✅ SAR Approved after {num_iterations} iteration(s)."
                outcome_status_func = st.success
                progress_bar.progress(100, text="Workflow Completed: Approved")
            elif verification_status == "needs_revision":
                outcome_message = f"⚠️ Reached max iterations ({workflow_manager.max_iterations}). Final SAR needs manual review."
                outcome_status_func = st.warning
                progress_bar.progress(100, text="Workflow Completed: Needs Review")
            elif verification_status == "rejected":
                 outcome_message = f"❌ SAR Rejected after {num_iterations} iteration(s). Manual intervention required."
                 outcome_status_func = st.error
                 progress_bar.progress(100, text="Workflow Completed: Rejected")
            else: # Handle error/unknown status from workflow manager
                 outcome_message = f"❓ Workflow finished with unexpected status: {verification_status}. Manual review required."
                 outcome_status_func = st.error
                 progress_bar.progress(100, text=f"Workflow Completed: Status '{verification_status}'")

            # Display Final Outcome Status
            update_step_status(current_step_index, "completed") # Mark step as done
            with steps_config[current_step_index]["placeholder"]: # Reuse placeholder for final summary
                 st.markdown(f"**{steps_config[current_step_index]['icon']} {step_name}**") # Re-add title
                 outcome_status_func(outcome_message) # Show status message

                 # Show final SAR JSON (if available) in expander
                 if final_sar_data:
                     with st.expander("View Final SAR JSON Data", expanded=False):
                          st.json(final_sar_data)
                     # Add download button for the final SAR JSON
                     st.download_button(
                         label="⬇️ Download Final SAR JSON",
                         data=json.dumps(final_sar_data, indent=2),
                         file_name=f"final_sar_report_{time.strftime('%Y%m%d_%H%M%S')}.json",
                         mime="application/json",
                         key="download_sar_json"
                     )
                 else:
                      st.info("No final SAR data generated or available.")


        except Exception as e:
            # General error catching for the whole workflow
            error_traceback = traceback.format_exc()
            status_placeholder.error(f"Workflow Error!")
            st.error(f"An error occurred during workflow execution: {e}")
            logger.error(f"Workflow failed: {e}\n{error_traceback}")
            # Mark the currently running or last attempted step as failed
            if current_step_index != -1:
                 update_step_status(current_step_index, "failed", str(e), exception_info=error_traceback)
            # Mark subsequent steps as skipped
            for i in range(current_step_index + 1, len(steps_config)):
                 update_step_status(i, "skipped")
            progress_bar.progress(100, text="Workflow Failed!")

# --- PDF Filling Section (Outside the main workflow button) ---
st.markdown("---")
st.markdown("### SAR PDF Generation")

# Retrieve SAR data from session state if it exists and was approved/needs review
final_sar_to_fill = st.session_state.get(SESSION_STATE_SAR_DATA)
workflow_status = workflow_results.get("final_status") if 'workflow_results' in locals() else None

# Check prerequisites for PDF filling
can_fill_pdf = final_sar_to_fill and PDF_FILLER_LOADED and (workflow_status in ["approved", "needs_revision"])
pdf_fill_disabled_reason = ""
if not final_sar_to_fill: pdf_fill_disabled_reason += "No final SAR data available from workflow run. "
if not PDF_FILLER_LOADED: pdf_fill_disabled_reason += "PDF Filler Agent module not loaded. "
if workflow_status not in ["approved", "needs_revision"]: pdf_fill_disabled_reason += f"Workflow status is '{workflow_status}', PDF filling not applicable. "

pdf_fill_placeholder = st.container() # Placeholder for button and status

with pdf_fill_placeholder:
    if st.button("📄 Fill SAR PDF Form", disabled=not can_fill_pdf, key="fill_pdf"):
        if not can_fill_pdf: # Should be blocked by disabled state, but double-check
            st.error(f"Cannot fill PDF: {pdf_fill_disabled_reason.strip()}")
        else:
            pdf_status = st.status("Filling PDF Form...", expanded=True)
            try:
                pdf_agent = PDFFillingAgent()
                pdf_status.write(f"Using template: {DEFAULT_PDF_TEMPLATE}")
                filled_pdf_path = pdf_agent.run(
                    sar_data=final_sar_to_fill,
                    template_path=DEFAULT_PDF_TEMPLATE, # Uses the descriptive template
                    output_dir=DEFAULT_OUTPUT_DIR
                )

                if filled_pdf_path and os.path.exists(filled_pdf_path):
                    st.session_state[SESSION_STATE_FILLED_PDF_PATH] = filled_pdf_path
                    pdf_status.update(label="PDF Filling Successful!", state="complete", expanded=False)
                    logger.info(f"PDF filling completed: {filled_pdf_path}")
                    # Rerun to show download button immediately - place download logic outside button click
                    st.rerun()
                else:
                    st.session_state[SESSION_STATE_FILLED_PDF_PATH] = None
                    pdf_status.update(label="PDF Filling Failed.", state="error", expanded=True)
                    pdf_status.error("Failed to generate or find the filled PDF file. Check logs.")
                    logger.error("PDF Filling Agent run completed but no valid path returned or file not found.")

            except Exception as pdf_exc:
                st.session_state[SESSION_STATE_FILLED_PDF_PATH] = None
                error_traceback = traceback.format_exc()
                pdf_status.update(label="PDF Filling Error!", state="error", expanded=True)
                pdf_status.error(f"An error occurred during PDF filling: {pdf_exc}")
                pdf_status.code(error_traceback)
                logger.error(f"PDF filling failed: {pdf_exc}\n{error_traceback}")

    # Show download button if PDF was generated in this session run
    if st.session_state.get(SESSION_STATE_FILLED_PDF_PATH):
        filled_pdf_path = st.session_state[SESSION_STATE_FILLED_PDF_PATH]
        if os.path.exists(filled_pdf_path):
            try:
                with open(filled_pdf_path, "rb") as fp:
                    st.download_button(
                        label="⬇️ Download Filled SAR PDF",
                        data=fp,
                        file_name=os.path.basename(filled_pdf_path),
                        mime="application/pdf",
                        key="download_filled_pdf"
                    )
            except Exception as dl_exc:
                 st.error(f"Error preparing filled PDF for download: {dl_exc}")
        else:
            st.warning("Previously generated PDF file seems to be missing.")


# --- Footer or Additional Info ---
st.markdown("---")
st.caption("SAR AI Assistant v1.0")