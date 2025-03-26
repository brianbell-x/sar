import streamlit as st
import json
import os
from openai import OpenAI
import dotenv
import time # For potential visual delays/spinners if needed

api_key = st.secrets.get("api_key")

# --- Agent Imports ---
# Assuming these are correctly placed and importable
try:
    from agents.agent_01_data_ingestion import DataIngestionAgent
    from agents.agent_02_03_pattern_anomaly_detection import PatternAnomalyDetectionAgent
    from agents.agent_05_sar_generation import SARGenerationAgent
    from agents.agent_06_compliance_verification import ComplianceVerificationAgent
    AGENTS_LOADED = True
except ImportError as e:
    st.error(f"Failed to import agents: {e}. Please ensure agent files exist and are importable.")
    AGENTS_LOADED = False

# Load environment variables
dotenv.load_dotenv()

# Page configuration
st.set_page_config(
    page_title="SAR AI",
    page_icon="🛡️", # Changed icon
    layout="wide",
    initial_sidebar_state="expanded",
)

def create_client(api_key):
    """Create and configure the OpenAI API client."""
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to create OpenAI client: {e}")
        return None

def load_sample_data(filepath="sample_transactions.json"):
    """Loads sample transaction data from a JSON file."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Error: Sample data file '{filepath}' not found.")
        return None
    except json.JSONDecodeError:
        st.error(f"Error: Could not decode JSON from '{filepath}'.")
        return None
    except Exception as e:
        st.error(f"Error loading sample data: {str(e)}")
        return None


with st.sidebar:
    st.markdown("# SAR AI Assistant")
    st.caption("Automated Suspicious Activity Reports")
    st.divider()



    st.header("Data Input")
    input_option = st.radio(
        "Choose transaction data source:",
        ["Use Sample Data", "Upload Custom JSON File", "Enter Custom JSON Text"],
        key="data_input_method",
        horizontal=True,
        label_visibility="collapsed" # Hide the label "Choose transaction data source:"
    )

    transaction_data = None
    sample_data_loaded = False
    custom_data_valid = False

    if input_option == "Use Sample Data":
        transaction_data = load_sample_data()
        if transaction_data:
            sample_data_loaded = True
            # st.success("Sample data ready.") # Less verbose

    elif input_option == "Upload Custom JSON File":
        uploaded_file = st.file_uploader("Upload JSON file", type=["json"])
        if uploaded_file is not None:
            try:
                transaction_data = json.load(uploaded_file)
                st.success("File uploaded and parsed successfully.")
                custom_data_valid = True
            except json.JSONDecodeError:
                st.error("Invalid JSON format in uploaded file.")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")

    elif input_option == "Enter Custom JSON Text":
        try:
            # Provide sample data structure as a placeholder/example
            with open("sample_transactions.json", "r") as f:
                default_data_str = f.read()
        except Exception:
            default_data_str = '{\n  "transactions": [\n    {\n      "transaction_id": "TX_EXAMPLE",\n      ...\n    }\n  ]\n}'

        transaction_data_str = st.text_area(
            "Paste JSON data here:",
            value=default_data_str,
            height=250,
            key="json_text_area",
            help="Ensure the data follows the expected JSON structure."
        )
        if transaction_data_str:
            try:
                transaction_data = json.loads(transaction_data_str)
                st.success("JSON data parsed successfully.")
                custom_data_valid = True
            except json.JSONDecodeError:
                st.error("Invalid JSON format. Please check your input.")
            except Exception as e:
                st.error(f"Error parsing JSON: {str(e)}")

    # Display sample data if loaded and selected
    if sample_data_loaded and input_option == "Use Sample Data":
         with st.expander("View Sample Data"):
            st.json(transaction_data, expanded=False) # Keep collapsed by default

# Check prerequisites before allowing workflow run
can_run_workflow = api_key and transaction_data and AGENTS_LOADED
run_button_disabled_reason = ""
if not api_key: run_button_disabled_reason += "API Key missing. "
if not transaction_data: run_button_disabled_reason += "Transaction data missing or invalid. "
if not AGENTS_LOADED: run_button_disabled_reason += "Agent modules failed to load. "


if st.button("Run Fraud Detection Workflow", type="primary", disabled=not can_run_workflow, use_container_width=True):

    if not can_run_workflow: # Redundant check, but safe
        st.error(f"Cannot run workflow: {run_button_disabled_reason.strip()}")
    else:
        client = create_client(api_key)
        if not client:
            st.error("Failed to initialize AI client. Check API Key.")
        else:
            # --- Workflow Execution ---
            st.markdown("### Workflow Progress")
            status_placeholder = st.empty()
            progress_bar = st.progress(0, text="Initializing...")

            # Create columns for step visualization
            step_cols = st.columns(4)
            step_placeholders = [col.container(border=True) for col in step_cols]

            # Define step details
            steps_config = [
                {"name": "Data Ingestion", "icon": "📥", "placeholder": step_placeholders[0]},
                {"name": "Analysis & Detection", "icon": "🔬", "placeholder": step_placeholders[1]},
                {"name": "SAR Generation", "icon": "📝", "placeholder": step_placeholders[2]},
                {"name": "Compliance Verification", "icon": "✅", "placeholder": step_placeholders[3]},
            ]

            # Initialize step statuses
            for i, step in enumerate(steps_config):
                 with step["placeholder"]:
                     st.markdown(f"**{step['icon']} {step['name']}**")
                     step["status_widget"] = st.empty()
                     step["status_widget"].info("Pending...")
                     step["expander"] = st.expander("Details", expanded=False)


            # Helper to update step status
            def update_step_status(step_index, status, message=None):
                step = steps_config[step_index]
                if status == "running":
                    step["status_widget"].info(f"Running... {message or ''}")
                elif status == "completed":
                    step["status_widget"].success("Completed")
                elif status == "failed":
                    step["status_widget"].error(f"Failed: {message or ''}")

            try:
                # --- Step 1: Data Ingestion ---
                current_step_index = 0
                step_name = steps_config[current_step_index]["name"]
                status_placeholder.info(f"Running: {step_name}...")
                update_step_status(current_step_index, "running")
                progress_bar.progress(5, text=f"Running {step_name}...")

                data_ingestion_agent = DataIngestionAgent() # Uses Python code now
                processed_data = data_ingestion_agent.run(transaction_data)

                progress_bar.progress(20, text=f"{step_name} Completed.")
                update_step_status(current_step_index, "completed")
                with steps_config[current_step_index]["expander"]:
                    st.write("Standardized Transaction Data:")
                    st.json(processed_data)

                # --- Step 2: Pattern Analysis & Anomaly Detection ---
                current_step_index = 1
                step_name = steps_config[current_step_index]["name"]
                status_placeholder.info(f"Running: {step_name}...")
                update_step_status(current_step_index, "running")
                progress_bar.progress(25, text=f"Running {step_name}...")

                pattern_anomaly_detection_agent = PatternAnomalyDetectionAgent(client)
                analysis_results = pattern_anomaly_detection_agent.run(processed_data)

                progress_bar.progress(50, text=f"{step_name} Completed.")
                update_step_status(current_step_index, "completed")
                with steps_config[current_step_index]["expander"]:
                    st.write("Analysis & Detection Results:")
                    st.json(analysis_results)
                    # Display summary metrics
                    summary = analysis_results.get("analysis_summary", {})
                    if summary:
                        st.write("---")
                        metric_cols = st.columns(3)
                        metric_cols[0].metric("Total Analyzed", summary.get("total_analyzed", "N/A"))
                        metric_cols[1].metric("Flagged Suspicious", summary.get("suspicious_count", "N/A"))
                        metric_cols[2].metric("Avg. Anomaly Score", summary.get("average_anomaly_score", "N/A").capitalize())


                # --- Step 3 & 4: SAR Generation & Compliance Verification (Iterative) ---
                st.divider()
                st.markdown("### SAR Generation & Verification Cycle")

                sar_generation_agent = SARGenerationAgent(client)
                compliance_verification_agent = ComplianceVerificationAgent(client)

                max_iterations = 3
                iteration_results = [] # Store results for each iteration

                sar_report = None
                compliance_verification = None
                verification_status = "needs_generation" # Initial status

                # Create tabs for iterations
                tabs = st.tabs([f"Iteration {i+1}" for i in range(max_iterations)])

                for i in range(max_iterations):
                    with tabs[i]:
                        iter_cols = st.columns(2)

                        # --- SAR Generation ---
                        with iter_cols[0]:
                            st.markdown(f"#### {steps_config[2]['icon']} SAR Generation (Iter. {i+1})")
                            gen_status = st.empty()

                            if verification_status == "needs_generation" or verification_status == "needs_revision":
                                current_step_index = 2
                                step_name = steps_config[current_step_index]["name"]
                                status_placeholder.info(f"Running: {step_name} (Iter. {i+1})...")
                                update_step_status(current_step_index, "running", f"(Iter. {i+1})")
                                gen_status.info("Generating...")
                                progress_bar.progress(50 + (i * 15), text=f"Running {step_name} (Iter. {i+1})...")

                                # Prepare input for SAR generation
                                if i == 0: # First iteration
                                    input_for_sar = analysis_results
                                else: # Subsequent iterations include feedback
                                    input_for_sar = {
                                        "anomaly_detection": analysis_results, # Always provide original analysis
                                        "verification_feedback": compliance_verification # Include previous feedback
                                    }

                                sar_report = sar_generation_agent.run(input_for_sar)
                                gen_status.success("Generated")
                                update_step_status(current_step_index, "completed") # Mark step as completed after first successful gen
                                st.json(sar_report)
                            elif verification_status == "approved":
                                 gen_status.success("Approved in previous iteration.")
                                 if sar_report: st.json(sar_report) # Show the approved report again
                                 else: st.warning("Approved, but SAR report data missing.")
                            else: # Rejected or other status
                                 gen_status.error(f"Skipped due to status: {verification_status}")
                                 if sar_report: st.json(sar_report) # Show the last generated report

                        # --- Compliance Verification ---
                        with iter_cols[1]:
                            st.markdown(f"#### {steps_config[3]['icon']} Compliance Verification (Iter. {i+1})")
                            ver_status_widget = st.empty()

                            # Only verify if a SAR was generated/available in this loop
                            if sar_report and verification_status != "approved":
                                current_step_index = 3
                                step_name = steps_config[current_step_index]["name"]
                                status_placeholder.info(f"Running: {step_name} (Iter. {i+1})...")
                                update_step_status(current_step_index, "running", f"(Iter. {i+1})")
                                ver_status_widget.info("Verifying...")
                                progress_bar.progress(60 + (i * 15), text=f"Running {step_name} (Iter. {i+1})...")

                                compliance_verification = compliance_verification_agent.run(sar_report)
                                verification_status = compliance_verification.get("verification_result", {}).get("verification_status", "error")
                                is_compliant = compliance_verification.get("verification_result", {}).get("is_compliant", False)
                                compliance_score = compliance_verification.get("verification_result", {}).get("compliance_score")

                                # Display verification status clearly
                                if verification_status == "approved":
                                    ver_status_widget.success(f"Status: Approved (Score: {compliance_score if compliance_score is not None else 'N/A'})")
                                elif verification_status == "needs_revision":
                                    ver_status_widget.warning(f"Status: Needs Revision (Score: {compliance_score if compliance_score is not None else 'N/A'})")
                                else: # rejected or other
                                    ver_status_widget.error(f"Status: {verification_status.capitalize()} (Score: {compliance_score if compliance_score is not None else 'N/A'})")

                                update_step_status(current_step_index, "completed") # Mark step completed after first verification
                                st.json(compliance_verification)

                                # Store results
                                iteration_results.append({
                                    "iteration": i + 1,
                                    "sar_report": sar_report,
                                    "compliance_verification": compliance_verification,
                                    "status": verification_status
                                })
                            elif verification_status == "approved":
                                ver_status_widget.success("Approved.")
                                if compliance_verification: st.json(compliance_verification)
                            else:
                                ver_status_widget.info("Verification skipped (SAR not generated or already approved).")


                    # Check if approved, break the loop
                    if verification_status == "approved":
                        status_placeholder.success(f"SAR Approved in Iteration {i+1}!")
                        break
                    elif verification_status == "rejected":
                         status_placeholder.error(f"SAR Rejected in Iteration {i+1}. Stopping.")
                         break # Stop if rejected

                # --- Final Outcome ---
                st.divider()
                st.markdown("### Final Outcome")
                final_status_col, final_report_col = st.columns([1, 2])

                with final_status_col:
                    if verification_status == "approved":
                        st.success(f"✅ SAR Approved after {len(iteration_results)} iteration(s).")
                        progress_bar.progress(100, text="Workflow Completed: Approved")
                    elif verification_status == "needs_revision":
                        st.warning(f"⚠️ Reached maximum iterations ({max_iterations}). Final SAR needs manual review.")
                        progress_bar.progress(100, text="Workflow Completed: Needs Review")
                    elif verification_status == "rejected":
                         st.error(f"❌ SAR Rejected. Manual intervention required.")
                         progress_bar.progress(100, text="Workflow Completed: Rejected")
                    else: # Should not happen in normal flow, but handle error/unknown
                         st.error(f"❓ Workflow finished with unexpected status: {verification_status}. Manual review required.")
                         progress_bar.progress(100, text=f"Workflow Completed: Status {verification_status}")

                with final_report_col:
                    if sar_report:
                         st.markdown("**Final SAR Report Data:**")
                         # Provide download for the last generated SAR
                         st.download_button(
                             label="⬇️ Download Final SAR JSON",
                             data=json.dumps(sar_report, indent=2),
                             file_name=f"final_sar_report_{time.strftime('%Y%m%d_%H%M%S')}.json",
                             mime="application/json"
                         )
                         with st.expander("View Final SAR JSON", expanded=False):
                             st.json(sar_report)
                    else:
                         st.info("No final SAR report generated or available.")


            except Exception as e:
                status_placeholder.error(f"An error occurred during workflow execution!")
                st.exception(e)
                # Mark the currently running step as failed if possible
                if 'current_step_index' in locals():
                     update_step_status(current_step_index, "failed", str(e))
                progress_bar.progress(100, text="Workflow Failed!") # Show progress bar full on error
