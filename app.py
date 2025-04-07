import streamlit as st
import tempfile
import os
import time
from utils import execute_script, create_logger
import atexit

# ----- Configuration -----
APP_TITLE = "RPA Script Runner"
APP_ICON = "🤖"
EXPANDED_VIEW_SCRIPT = False  # Initially collapse script view
LOG_DISPLAY_HEIGHT = 400
RESULT_DISPLAY_HEIGHT = 400
LOG_AUTO_REFRESH_INTERVAL = 1  # seconds


# ----- Utility Functions -----
def cleanup():
    if st.session_state.script_path and os.path.exists(st.session_state.script_path):
        os.unlink(st.session_state.script_path)
    if st.session_state.log_file and os.path.exists(st.session_state.log_file):
        os.unlink(st.session_state.log_file)

# ----- Streamlit App -----

# Set page title and layout
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide"
)

# App title and description
st.title(APP_TITLE)
st.write("Upload, execute, and monitor your RPA scripts with real-time logs and results.")

# Initialize session state variables
if 'script_path' not in st.session_state:
    st.session_state.script_path = None
if 'script_name' not in st.session_state:
    st.session_state.script_name = None
if 'execution_status' not in st.session_state:
    st.session_state.execution_status = None
if 'log_file' not in st.session_state:
    st.session_state.log_file = None
if 'result' not in st.session_state:
    st.session_state.result = None
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'logs' not in st.session_state:
    st.session_state.logs = []

# Sidebar for script upload and controls
with st.sidebar:
    st.header("RPA Script Upload")

    uploaded_file = st.file_uploader("Choose a Python script", type=["py"])

    if uploaded_file is not None:
        # Save uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as temp_file:
            temp_file.write(uploaded_file.getvalue())
            st.session_state.script_path = temp_file.name
            st.session_state.script_name = uploaded_file.name

        st.success(f"File uploaded: {uploaded_file.name}")

        # Display script content
        st.subheader("Script Content")
        script_content = uploaded_file.getvalue().decode("utf-8")
        with st.expander("View Script", expanded=EXPANDED_VIEW_SCRIPT):  # Use constant
            st.code(script_content, language="python")

    # Execute/Stop buttons with layout improvements
    if st.session_state.script_path:
        col1, col2 = st.columns([1, 1])  # Evenly distribute columns

        with col1:
            execute_button = st.button(
                "🚀 Execute Script",  # More visually appealing
                disabled=st.session_state.is_running,
                type="primary",
                use_container_width=True  # Take up full column width
            )

        with col2:
            if st.session_state.is_running:
                stop_button = st.button(
                    "🛑 Stop Execution",  # More visually appealing
                    type="secondary",
                    use_container_width=True  # Take up full column width
                )
                if stop_button:
                    st.session_state.is_running = False
                    st.warning("Attempting to stop script execution...")
            else:
                st.empty() # Clear space when no button present

        if execute_button:
            st.session_state.is_running = True
            st.session_state.execution_status = "Running"
            st.session_state.logs = []
            st.session_state.result = None

            # Create a temporary log file
            log_fd, log_path = tempfile.mkstemp(suffix='.log')
            os.close(log_fd)
            st.session_state.log_file = log_path

            # Create logger
            logger = create_logger(log_path)
            logger.info(f"Starting execution of {st.session_state.script_name}")

            # Execute the script in a separate thread
            execute_script(
                st.session_state.script_path,
                log_path,
                lambda: setattr(st.session_state, 'is_running', False),
                lambda result: setattr(st.session_state, 'result', result),
                lambda status: setattr(st.session_state, 'execution_status', status)
            )
            st.rerun()

# Main area for log display and results
col1, col2 = st.columns([2, 1])


st.header("Execution Logs")

    # Status indicator with better visual representation
if st.session_state.execution_status:
        status_emoji = {
            "Running": "🟡",
            "Completed": "🟢",
            "Failed": "🔴",
            "Stopped": "⚪"
        }.get(st.session_state.execution_status, "⚪")

        status_message = f"{status_emoji} Status: **{st.session_state.execution_status}**"
        if st.session_state.execution_status == "Running":
            st.info(status_message)
        elif st.session_state.execution_status == "Completed":
            st.success(status_message)
        elif st.session_state.execution_status == "Failed":
            st.error(status_message)
        elif st.session_state.execution_status == "Stopped":
            st.warning(status_message)
        else:
            st.info(status_message)

    # Log display area
log_container = st.container(height=LOG_DISPLAY_HEIGHT)  # Set height using constant

    # Auto-refresh logs when script is running
if st.session_state.is_running and st.session_state.log_file:
        with log_container:
            if os.path.exists(st.session_state.log_file):
                with open(st.session_state.log_file, 'r') as f:
                    logs = f.readlines()

                    # Update the session state logs only if they have changed
                    if logs != st.session_state.logs:
                        st.session_state.logs = logs

                    for log in logs:
                        st.text(log.strip())

            # Auto-refresh every second while running
            time.sleep(LOG_AUTO_REFRESH_INTERVAL) #added to use constant value
            st.rerun()
else:
        # Display stored logs if available
        with log_container:
            for log in st.session_state.logs:
                st.text(log.strip())

# Register cleanup handler
atexit.register(cleanup)