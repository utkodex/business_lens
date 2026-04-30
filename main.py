import streamlit as st
import pandas as pd
import requests

# --- Page Configuration ---
st.set_page_config(
    page_title="Business Lens AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Premium Design ---
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0e1117;
        color: #ffffff; /* Brighter white for general text */
    }
    
    /* Chat message styling */
    .stChatMessage {
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #161b22; /* Slightly lighter than main bg for contrast */
        border: 1px solid #30363d;
    }

    /* Target specific chat text elements */
    .stChatMessage [data-testid="stMarkdownContainer"], 
    .stChatMessage [data-testid="stMarkdownContainer"] p,
    .stChatMessage [data-testid="stMarkdownContainer"] li {
        color: #ffffff !important;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
    }
    
    /* Dataframes */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #2b313e;
        background-color: #1a1c24;
    }
    
    /* Sidebar text */
    .stSidebar [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Configuration ---
API_BASE_URL = "http://localhost:8000"

# --- App Header ---
st.title("📈 Business Lens AI")
st.markdown("*Your intelligent FMCG category intelligence assistant. Ask me about revenues, trends, and market share!*")
st.divider()

# --- Session State for Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am Business Lens AI. I have access to internal sales data and competitor market metrics. How can I help you today?"}
    ]

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        content = message["content"]
        if isinstance(content, dict) and "dataframe" in content:
            st.dataframe(pd.DataFrame(content["dataframe"]), use_container_width=True)
        else:
            st.markdown(content)

# --- Chat Input ---
if prompt := st.chat_input("E.g., What is the total revenue for ColaMax in 2024?"):
    
    # 1. Display and save user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Call FastAPI backend and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing intent and crunching data..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/query",
                    json={"query": prompt},
                    timeout=60
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("type") == "dataframe":
                    df = pd.DataFrame(data["data"])
                    st.dataframe(df, use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": {"dataframe": data["data"]}})
                else:
                    st.markdown(data["data"])
                    st.session_state.messages.append({"role": "assistant", "content": data["data"]})
                    
            except requests.exceptions.ConnectionError:
                error_msg = "❌ **Cannot connect to the API server.** Make sure to run `uvicorn app:app --reload` first."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"❌ **Error executing query:** {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
                if data.get("type") == "dataframe":
                    df = pd.DataFrame(data["data"])
                    st.dataframe(df, use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "content": {"dataframe": data["data"]}})
                else:
                    st.markdown(f'<div class="assistant-content">{data["data"]}</div>', unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": data["data"]})
                    
            except requests.exceptions.ConnectionError:
                error_msg = "❌ **Cannot connect to the API server.**"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"❌ **Error:** {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
