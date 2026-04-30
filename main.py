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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main background */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
        border-right: 1px solid #30363d;
    }
    [data-testid="stSidebar"] * {
        color: #e6edf3 !important;
    }

    /* Provider badge in sidebar */
    .provider-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    .badge-groq   { background: #1a3a2a; color: #4ade80; border: 1px solid #22c55e; }
    .badge-ollama { background: #1e2d4a; color: #60a5fa; border: 1px solid #3b82f6; }

    /* Chat message styling */
    .stChatMessage {
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        background-color: #161b22;
        border: 1px solid #30363d;
    }
    .stChatMessage [data-testid="stMarkdownContainer"],
    .stChatMessage [data-testid="stMarkdownContainer"] p,
    .stChatMessage [data-testid="stMarkdownContainer"] li {
        color: #e6edf3 !important;
        font-size: 1.0rem;
        line-height: 1.65;
    }

    /* Headers */
    h1, h2, h3 {
        color: #e6edf3 !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
    }

    /* Dataframes */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #30363d;
        background-color: #161b22;
    }

    /* Radio buttons */
    [data-testid="stRadio"] label {
        color: #e6edf3 !important;
    }

    /* Divider */
    hr { border-color: #30363d !important; }

    /* Chat input */
    [data-testid="stChatInputTextArea"] {
        background-color: #161b22 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Configuration ---
API_BASE_URL = "http://localhost:8001"

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.divider()

    st.markdown("### 🤖 LLM Provider")
    llm_provider = st.radio(
        label="Choose backend",
        options=["groq", "ollama"],
        index=0,
        format_func=lambda x: "☁️  Groq  (llama-3.3-70b-versatile)" if x == "groq"
                               else "🦙  Ollama  (deepseek-v3.1:671b-cloud)",
        help=(
            "**Groq** — ChatGroq via langchain-groq. Fast cloud inference.\n\n"
            "**Ollama** — ChatOllama via langchain-ollama pointing to ollama.com."
        ),
    )

    badge_cls = "badge-groq" if llm_provider == "groq" else "badge-ollama"
    badge_label = "GROQ ACTIVE" if llm_provider == "groq" else "OLLAMA ACTIVE"
    st.markdown(
        f'<span class="provider-badge {badge_cls}">{badge_label}</span>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("### 📖 About")
    st.markdown(
        "Business Lens AI is an FMCG category intelligence assistant. "
        "Ask about revenues, trends, market share, and brand comparisons."
    )
    st.divider()
    st.caption("v1.1.0 — Groq + Ollama")

# ── Main header ──────────────────────────────────────────────────────────────
st.title("📈 Business Lens AI")
st.markdown(
    "*Your intelligent FMCG category intelligence assistant. "
    "Ask me about revenues, trends, and market share!*"
)
st.divider()

# ── Session State for Chat History ───────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I am Business Lens AI. I have access to internal sales data "
                "and competitor market metrics. How can I help you today?"
            ),
        }
    ]

# ── Display Chat History ─────────────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        content = message["content"]
        if isinstance(content, dict) and "dataframe" in content:
            st.dataframe(pd.DataFrame(content["dataframe"]), use_container_width=True)
        else:
            st.markdown(content)

# ── Chat Input ───────────────────────────────────────────────────────────────
if prompt := st.chat_input("E.g., What is the total revenue for ColaMax in 2024?"):

    # 1. Display and save user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Call FastAPI backend and display assistant response
    with st.chat_message("assistant"):
        provider_label = "Groq ☁️" if llm_provider == "groq" else "Ollama 🦙"
        with st.spinner(f"Analyzing intent via **{provider_label}** and crunching data…"):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/query",
                    json={"query": prompt, "llm_provider": llm_provider},
                    timeout=90,
                )
                response.raise_for_status()
                data = response.json()

                if data.get("type") == "dataframe":
                    df = pd.DataFrame(data["data"])
                    st.dataframe(df, use_container_width=True)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": {"dataframe": data["data"]}}
                    )
                else:
                    st.markdown(data["data"])
                    st.session_state.messages.append(
                        {"role": "assistant", "content": data["data"]}
                    )

            except requests.exceptions.ConnectionError:
                error_msg = (
                    "❌ **Cannot connect to the API server.**  "
                    "Make sure to run `uvicorn app:app --reload` first."
                )
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"❌ **Error executing query:** {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
