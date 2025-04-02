# tmpmgtkylo_/app.py
# ... (keep existing imports)
import streamlit as st
import json
import os
from openai import OpenAI
import dotenv
import time
import traceback # For detailed error logging
import logging # Added logging

# --- Configuration ---
DEFAULT_SAMPLE_DATA = "sample_transactions.json"
DEFAULT_PDF_TEMPLATE = "resources/6710-06_descriptive.pdf"
DEFAULT_OUTPUT_DIR = "output"
SESSION_STATE_SAR_DATA = "final_sar_data"
SESSION_STATE_FILLED_PDF_PATH = "filled_pdf_path"

# --- Setup Logging ---
# Configure logging (basic example)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- Secrets and API Key ---
# ... (keep existing secrets logic)
api_key = st.secrets.get("api_key")
if not api_key:
    dotenv.load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

# --- Agent Imports ---
# ... (keep existing agent import logic)
AGENTS_LOADED = False
PDF_FILLER_LOADED = False
try:
    from agents.agent_01_data_ingestion import DataIngestionAgent
    from agents.agent_02_03_pattern_anomaly_detection import PatternAnomalyDetectionAgent
    from workflows.sar_workflow_manager import SARWorkflowManager
    AGENTS_LOADED = True
    try:
        from agents.agent_07_pdf_filling import PDFFillingAgent
        PDF_FILLER_LOADED = True
    except ImportError as pdf_e:
        st.warning(f"PDF Filling Agent not loaded: {pdf_e}. PDF generation will be unavailable.")
        logger.warning(f"PDF Filling Agent not loaded: {pdf_e}")
except ImportError as e:
    st.error(f"Failed to import core agents: {e}. Please ensure agent files exist and are importable.")
    logger.error(f"Failed to import core agents: {e}", exc_info=True)
    # AGENTS_LOADED remains False


# --- Page Config ---
# ... (keep existing page config)
st.set_page_config(
    page_title="SAR AI Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Helper Functions ---
@st.cache_resource # Cache the client for the session
def create_client(api_key_input):
    # ... (keep existing client creation logic)
    if not api_key_input:
        st.error("API Key is missing. Cannot create AI client.")
        return None
    try:
        client = OpenAI(api_key=api_key_input)
        # client.models.list() # Optional test call
        return client
    except Exception as e:
        st.error(f"Failed to create or validate OpenAI client: {e}")
        logger.error(f"Failed to create OpenAI client: {e}", exc_info=True)
        return None

# MODIFIED: load_sample_data now returns the entire structure containing different sets
@st.cache_data # Cache the loaded data to avoid reloading on every interaction
def load_sample_data(filepath=DEFAULT_SAMPLE_DATA) -> dict | None:
    """Loads sample transaction data sets from a JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Basic validation: Ensure it's a dictionary (expected top-level structure)
        if not isinstance(data, dict):
             st.error(f"Error: Sample data file '{filepath}' does not contain a valid JSON object (dictionary) at the top level.")
             logger.error(f"Sample data file '{filepath}' is not a dictionary.")
             return None
        # Optional: Check if *any* key contains a 'transactions' list
        has_transactions = any(
            isinstance(v, dict) and 'transactions' in v and isinstance(v['transactions'], list)
            for v in data.values()
        )
        if not has_transactions:
            st.warning(f"Warning: Sample data file '{filepath}' loaded, but no sets with a 'transactions' list were found.")
            logger.warning(f"No sets with 'transactions' list found in '{filepath}'.")
            # Decide if this is an error or just a warning (returning data allows UI to show keys)
        return data
    except FileNotFoundError:
        st.error(f"Error: Sample data file '{filepath}' not found.")
        logger.error(f"Sample data file '{filepath}' not found.")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Error: Could not decode JSON from '{filepath}'. Invalid format near line {e.lineno}, column {e.colno}.")
        logger.error(f"JSON decode error in '{filepath}': {e}", exc_info=True)
        return None
    except Exception as e:
        st.error(f"Error loading sample data from '{filepath}': {str(e)}")
        logger.error(f"Error loading sample data from '{filepath}': {e}", exc_info=True)
        return None

# --- Initialize Session State ---
# ... (keep existing session state init)
if SESSION_STATE_SAR_DATA not in st.session_state:
    st.session_state[SESSION_STATE_SAR_DATA] = None
if SESSION_STATE_FILLED_PDF_PATH not in st.session_state:
    st.session_state[SESSION_STATE_FILLED_PDF_PATH] = None
if 'selected_sample_set_key' not in st.session_state:
    st.session_state['selected_sample_set_key'] = None # To store the key of the selected sample set


# --- Sidebar ---
with st.sidebar:
    st.image("https://www.appliedaicourse.com/hubfs/Google%20Drive%20Integration/SAR%20AI%20Logo.png", width=80)
    st.markdown("# SAR AI Assistant")
    st.caption("Automated Suspicious Activity Reports")
    st.divider()

    # API Key Input
    st.header("Configuration")
    # ... (keep existing API key logic)
    if not api_key:
        api_key_input_val = st.text_input("Enter OpenAI API Key:", type="password", key="api_key_input", help="Required for AI agents.")
        if api_key_input_val:
             api_key = api_key_input_val # Assign if entered
             st.success("API Key provided.")
    else:
        st.success("API Key loaded.")

    st.divider()

    st.header("Data Input")
    input_option = st.radio(
        "Choose transaction data source:",
        ["Use Sample Data", "Upload Custom JSON File", "Enter Custom JSON Text"],
        key="data_input_method",
        label_visibility="collapsed"
    )

    transaction_data = None # Reset transaction_data at the start of sidebar rendering
    data_load_status = st.empty()

    # --- MODIFIED: Sample Data Selection ---
    if input_option == "Use Sample Data":
        all_sample_sets = load_sample_data() # Load the dictionary containing all sets

        if all_sample_sets:
            available_set_keys = list(all_sample_sets.keys())
            if not available_set_keys:
                data_load_status.error("Sample data file loaded, but no transaction sets found inside.")
            else:
                # Use session state to remember selection across minor reruns
                default_selection_index = 0
                if st.session_state['selected_sample_set_key'] in available_set_keys:
                    try:
                         default_selection_index = available_set_keys.index(st.session_state['selected_sample_set_key'])
                    except ValueError:
                         st.session_state['selected_sample_set_key'] = available_set_keys[0] # Reset if key vanished

                selected_set_key = st.selectbox(
                    "Select Sample Scenario:",
                    options=available_set_keys,
                    index=default_selection_index, # Default to first or remembered selection
                    key='sample_set_selector', # Assign a key for potential callbacks if needed
                    on_change=lambda: st.session_state.update(selected_sample_set_key=st.session_state.sample_set_selector) # Update state on change
                )

                # Retrieve the specific data for the selected set
                if selected_set_key and selected_set_key in all_sample_sets:
                    selected_set_data = all_sample_sets[selected_set_key]

                    # IMPORTANT: Ensure the selected data has the 'transactions' key
                    if isinstance(selected_set_data, dict) and 'transactions' in selected_set_data:
                        transaction_data = selected_set_data # Assign the specific set's data
                        set_description = selected_set_data.get('description', 'No description provided.')
                        data_load_status.success(f"Sample set '{selected_set_key}' loaded.")
                        logger.info(f"Sample set '{selected_set_key}' selected.")

                        with st.expander(f"View Sample Data: '{selected_set_key}'", expanded=False):
                            st.caption(f"Scenario: {set_description}")
                            st.json(transaction_data, expanded=False) # Show only the selected set's data
                    else:
                        data_load_status.error(f"Selected set '{selected_set_key}' is missing the required 'transactions' list.")
                        logger.error(f"Sample set '{selected_set_key}' loaded but missing 'transactions' key.")
                else:
                     data_load_status.warning("Please select a valid sample scenario.") # Should not happen with selectbox usually

        else:
            # Error message handled by load_sample_data
            pass # Keep the status placeholder empty or let load_sample_data show the error

    # --- Upload Custom JSON File ---
    elif input_option == "Upload Custom JSON File":
        # Reset selected sample set key if user switches away
        st.session_state['selected_sample_set_key'] = None
        uploaded_file = st.file_uploader("Upload JSON file (must contain 'transactions' key)", type=["json"], key="json_upload")
        if uploaded_file is not None:
            try:
                uploaded_data = json.load(uploaded_file)
                # Validate the structure of the uploaded file
                if isinstance(uploaded_data, dict) and "transactions" in uploaded_data and isinstance(uploaded_data["transactions"], list):
                     transaction_data = uploaded_data
                     data_load_status.success("File uploaded and parsed successfully.")
                     logger.info("Custom JSON file uploaded and validated.")
                else:
                     data_load_status.error("Invalid JSON structure. File must be a JSON object with a 'transactions' list.")
                     logger.warning("Uploaded JSON file has invalid structure.")

            except json.JSONDecodeError as e:
                data_load_status.error(f"Invalid JSON format: Error near line {e.lineno}, col {e.colno}.")
                logger.error(f"Uploaded JSON decode error: {e}", exc_info=True)
            except Exception as e:
                data_load_status.error(f"Error reading file: {str(e)}")
                logger.error(f"Error reading uploaded file: {e}", exc_info=True)

    # --- Enter Custom JSON Text ---
    elif input_option == "Enter Custom JSON Text":
        # Reset selected sample set key if user switches away
        st.session_state['selected_sample_set_key'] = None
        try:
            # Provide a minimal valid example structure in the default text
            default_data_str = json.dumps(
                {"transactions": [{"transaction_id": "TX_EXAMPLE", "amount": 100.00, "...":"..."}]},
                indent=2
            )
        except Exception:
            default_data_str = '{\n  "transactions": [\n    {\n      "transaction_id": "TX_EXAMPLE",\n      "amount": 100.00,\n      "...": "..."\n    }\n  ]\n}'

        # Use session state to persist text area content
        if 'json_text_area_val' not in st.session_state:
            st.session_state['json_text_area_val'] = default_data_str

        transaction_data_str = st.text_area(
            "Paste JSON data here:",
            value=st.session_state.json_text_area_val,
            height=250,
            key="json_text_area",
            help="Ensure the data is a JSON object with a 'transactions' key containing a list, like {'transactions': [...]}.",
            on_change=lambda: st.session_state.update(json_text_area_val=st.session_state.json_text_area)
        )
        if transaction_data_str:
            try:
                parsed_data = json.loads(transaction_data_str)
                # Validate the structure of the parsed data
                if isinstance(parsed_data, dict) and "transactions" in parsed_data and isinstance(parsed_data["transactions"], list):
                    transaction_data = parsed_data
                    data_load_status.success("JSON data parsed successfully.")
                    logger.info("Custom JSON text parsed and validated.")
                else:
                     data_load_status.error("Invalid JSON structure. Input must be a JSON object with a 'transactions' list.")
                     logger.warning("Pasted JSON text has invalid structure.")
                     transaction_data = None # Explicitly set to None if invalid

            except json.JSONDecodeError as e:
                data_load_status.error(f"Invalid JSON format: Error near line {e.lineno}, col {e.colno}.")
                logger.error(f"Pasted JSON decode error: {e}", exc_info=True)
                transaction_data = None # Explicitly set to None if invalid
            except Exception as e:
                data_load_status.error(f"Error parsing JSON: {str(e)}")
                logger.error(f"Error parsing pasted JSON: {e}", exc_info=True)
                transaction_data = None # Explicitly set to None if invalid

    st.divider()

# --- Main Content Area ---
st.title("🛡️ SAR AI Workflow")
st.markdown("Automate the detection of suspicious activities and the generation of SARs.")

# --- Prerequisites Check ---
# Need to potentially re-create client if API key was entered in sidebar
# Use the potentially updated api_key variable
client = create_client(api_key)

can_run_workflow = client and transaction_data and AGENTS_LOADED
run_button_disabled_reason = ""
if not client: run_button_disabled_reason += "AI Client (API Key) issue. "
if not transaction_data: run_button_disabled_reason += "Transaction data missing/invalid. "
if not AGENTS_LOADED: run_button_disabled_reason += "Core agent modules failed load. "


# --- Workflow Execution Button ---
if st.button("🚀 Run Full Workflow", type="primary", disabled=not can_run_workflow, use_container_width=True, key="run_workflow"):
    if not can_run_workflow:
        st.error(f"Cannot run workflow: {run_button_disabled_reason.strip()}")
    else:
        # --- (Rest of the workflow execution logic remains largely the same) ---
        # Clear previous results from session state
        st.session_state[SESSION_STATE_SAR_DATA] = None
        st.session_state[SESSION_STATE_FILLED_PDF_PATH] = None

        # --- Workflow UI Setup ---
        st.markdown("---")
        st.markdown("### Workflow Progress")
        status_placeholder = st.empty()
        progress_bar = st.progress(0, text="Initializing...")

        # Step Visualization
        step_cols = st.columns(4)
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
            # ... (keep existing update_step_status logic)
            if step_index >= len(steps_config): return # Safety check

            step = steps_config[step_index]
            current_status = ""
            log_message_detail = f"{f' - {message}' if message else ''}{f' - Details: {json.dumps(details)}' if details else ''}"

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
                        # Try to pretty-print JSON if details is likely json/dict
                        try:
                            st.json(details)
                        except:
                            st.write(details)

            elif status == "skipped":
                current_status = "Skipped"
                step["status_widget"].warning(current_status)

            log_level = logging.INFO
            if status == "failed": log_level = logging.ERROR
            elif status == "skipped": log_level = logging.WARNING

            logger.log(log_level, f"Step {step_index+1} ({step['name']}): {current_status}{log_message_detail}")
            if status == "failed" and exception_info:
                logger.error(f"Step {step_index+1} Exception:\n{exception_info}")


        # --- Workflow Execution Logic ---
        current_step_index = -1
        workflow_results = {} # Define workflow_results outside try block
        try:
            # --- Step 1: Data Ingestion ---
            # ... (Ingestion logic is unchanged, uses the selected transaction_data)
            current_step_index = 0
            step_name = steps_config[current_step_index]["name"]
            status_placeholder.info(f"Running: {step_name}...")
            update_step_status(current_step_index, "running")
            progress_bar.progress(5, text=f"Running {step_name}...")
            time.sleep(0.1)

            data_ingestion_agent = DataIngestionAgent()
            # IMPORTANT: transaction_data now holds the *selected* sample set or custom data
            processed_data = data_ingestion_agent.run(transaction_data)
            if not processed_data or not processed_data.get("transactions"):
                 raise ValueError("Data Ingestion returned no valid transactions.")

            update_step_status(current_step_index, "completed")
            with steps_config[current_step_index]["expander"]:
                st.write("Standardized Transaction Data (Sample):")
                st.json({"transactions": processed_data["transactions"][:3]}, expanded=True)
                st.caption(f"Total processed: {len(processed_data['transactions'])}")
            progress_bar.progress(20, text=f"{step_name} Completed.")


            # --- Step 2: Pattern Analysis & Anomaly Detection ---
            # ... (Analysis logic is unchanged)
            current_step_index = 1
            step_name = steps_config[current_step_index]["name"]
            status_placeholder.info(f"Running: {step_name}...")
            update_step_status(current_step_index, "running", message="Calling AI Model...")
            progress_bar.progress(25, text=f"Running {step_name}...")

            pattern_anomaly_detection_agent = PatternAnomalyDetectionAgent(client)
            analysis_results = pattern_anomaly_detection_agent.run(processed_data)

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
                    avg_score = summary.get("average_anomaly_score", "N/A")
                    metric_cols[2].metric("Avg. Anomaly Score", avg_score.capitalize() if isinstance(avg_score, str) else avg_score)
                    st.write("---")
                # Show sample transaction analysis
                st.json({"analyzed_transactions_sample": analysis_results["analyzed_transactions"][:2]}, expanded=True)
                st.caption(f"Full results contain {len(analysis_results['analyzed_transactions'])} analyzed transactions.")

            progress_bar.progress(50, text=f"{step_name} Completed.")


            # --- Step 3: SAR Generation & Verification Workflow ---
            # ... (Workflow Manager logic is unchanged)
            current_step_index = 2
            step_name = steps_config[current_step_index]["name"]
            status_placeholder.info(f"Running: {step_name} (May involve multiple AI calls)...")
            update_step_status(current_step_index, "running", message="Starting iterative process...")
            progress_bar.progress(55, text=f"Running {step_name}...")

            workflow_manager = SARWorkflowManager(client, max_iterations=3)
            workflow_results = workflow_manager.run(analysis_results) # Assign to outer scope variable

            final_sar_data = workflow_results.get("final_sar_report")
            if final_sar_data:
                st.session_state[SESSION_STATE_SAR_DATA] = final_sar_data

            update_step_status(current_step_index, "completed")
            with steps_config[current_step_index]["expander"]:
                st.write("SAR Workflow Iteration Results:")
                st.json(workflow_results, expanded=True)
            progress_bar.progress(85, text=f"{step_name} Completed.")


            # --- Step 4: Final Outcome ---
            # ... (Final Outcome logic is unchanged)
            current_step_index = 3
            step_name = steps_config[current_step_index]["name"]
            status_placeholder.success("Workflow Finished.")
            update_step_status(current_step_index, "running", message="Determining final status...")
            progress_bar.progress(90, text="Determining Final Outcome...")

            verification_status = workflow_results.get("final_status", "error")
            iteration_results = workflow_results.get("iteration_results", [])
            num_iterations = len(iteration_results)
            outcome_message = ""
            outcome_status_func = st.info

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
            else:
                 outcome_message = f"❓ Workflow finished with unexpected status: {verification_status}. Manual review required."
                 outcome_status_func = st.error
                 progress_bar.progress(100, text=f"Workflow Completed: Status '{verification_status}'")

            update_step_status(current_step_index, "completed")
            with steps_config[current_step_index]["placeholder"]:
                 st.markdown(f"**{steps_config[current_step_index]['icon']} {step_name}**")
                 outcome_status_func(outcome_message)
                 if final_sar_data:
                     with st.expander("View Final SAR JSON Data", expanded=False):
                          st.json(final_sar_data)
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
            # ... (Error handling logic is unchanged)
            error_traceback = traceback.format_exc()
            status_placeholder.error(f"Workflow Error!")
            st.error(f"An error occurred during workflow execution: {e}")
            logger.error(f"Workflow failed: {e}\n{error_traceback}")
            if current_step_index != -1:
                 update_step_status(current_step_index, "failed", str(e), exception_info=error_traceback)
            for i in range(current_step_index + 1, len(steps_config)):
                 update_step_status(i, "skipped")
            progress_bar.progress(100, text="Workflow Failed!")

# --- PDF Filling Section ---
st.markdown("---")
st.markdown("### SAR PDF Generation")

# Retrieve SAR data from session state
final_sar_to_fill = st.session_state.get(SESSION_STATE_SAR_DATA)
# Get workflow status *safely* from the workflow_results obtained during the run
# Use .get() to avoid KeyError if workflow didn't run or failed early
workflow_status = workflow_results.get("final_status") if workflow_results else None

# Check prerequisites for PDF filling
can_fill_pdf = final_sar_to_fill and PDF_FILLER_LOADED and (workflow_status in ["approved", "needs_revision"])
pdf_fill_disabled_reason = ""
if not final_sar_to_fill: pdf_fill_disabled_reason += "No final SAR data available from workflow run. "
if not PDF_FILLER_LOADED: pdf_fill_disabled_reason += "PDF Filler Agent module not loaded. "
# Handle case where workflow status is None (e.g., workflow didn't run)
if workflow_status not in ["approved", "needs_revision"]:
    status_display = f"'{workflow_status}'" if workflow_status else "not available"
    pdf_fill_disabled_reason += f"Workflow status is {status_display}, PDF filling not applicable. "


pdf_fill_placeholder = st.container()

with pdf_fill_placeholder:
    if st.button("📄 Fill SAR PDF Form", disabled=not can_fill_pdf, key="fill_pdf"):
        if not can_fill_pdf:
            st.error(f"Cannot fill PDF: {pdf_fill_disabled_reason.strip()}")
        else:
            pdf_status = st.status("Filling PDF Form...", expanded=True)
            try:
                pdf_agent = PDFFillingAgent()
                pdf_status.write(f"Using template: {DEFAULT_PDF_TEMPLATE}")
                filled_pdf_path = pdf_agent.run(
                    sar_data=final_sar_to_fill,
                    template_path=DEFAULT_PDF_TEMPLATE,
                    output_dir=DEFAULT_OUTPUT_DIR
                )

                if filled_pdf_path and os.path.exists(filled_pdf_path):
                    st.session_state[SESSION_STATE_FILLED_PDF_PATH] = filled_pdf_path
                    pdf_status.update(label="PDF Filling Successful!", state="complete", expanded=False)
                    logger.info(f"PDF filling completed: {filled_pdf_path}")
                    st.rerun() # Rerun to show download button
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

    # Show download button if PDF was generated
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
                 logger.error(f"Error reading filled PDF for download: {dl_exc}", exc_info=True)
        else:
            st.warning("Previously generated PDF file seems to be missing.")
            logger.warning(f"Tried to show download button, but file not found: {filled_pdf_path}")
            # Clean up session state if file is missing
            st.session_state[SESSION_STATE_FILLED_PDF_PATH] = None


# --- Footer ---
st.markdown("---")
st.caption("SAR AI Assistant v1.1 (Updated Sample Selection)")