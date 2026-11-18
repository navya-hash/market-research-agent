import os
import sys
import io
import time
import pathlib
import datetime
import secrets
from dotenv import load_dotenv
import streamlit as st
import yaml
import streamlit_authenticator as stauth

# Load environment variables
load_dotenv()

# Streamlit Page Config
st.set_page_config(
    page_title="Market Research AI Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .agent-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        font-size: 0.9rem;
    }
    .status-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-ready { background-color: #DEF7EC; color: #03543F; }
    .badge-missing { background-color: #FDE8E8; color: #9B1C1C; }
</style>
""", unsafe_allow_html=True)


# Custom Stream Redirector to stream CrewAI stdout to UI
class StreamlitLogRedirector:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.buffer = io.StringIO()

    def write(self, data):
        self.buffer.write(data)
        # Update streamlit placeholder with the current buffer
        val = self.buffer.getvalue()
        # Keep last 5000 characters to prevent DOM overloading
        display_val = val[-5000:] if len(val) > 5000 else val
        self.placeholder.code(display_val, language="bash")

    def flush(self):
        pass


def ensure_reports_dir():
    reports_dir = pathlib.Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def list_saved_reports():
    reports_dir = ensure_reports_dir()
    reports = list(reports_dir.glob("*.md"))
    reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return reports


# Helper to convert Streamlit secrets (AttrDict) to standard dictionary
def to_clean_dict(obj):
    if hasattr(obj, "items"):
        return {str(k): to_clean_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_clean_dict(v) for v in obj]
    return obj


# Safe getter for Streamlit Cloud secrets (prevents StreamlitSecretNotFoundError when run locally)
def safe_get_secret(key=None, default=None):
    try:
        if not hasattr(st, "secrets"):
            return default
        if key is None:
            return st.secrets
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        # Thrown by Streamlit if no secrets.toml or cloud secrets exist
        pass
    return default


# ================= AUTHENTICATION GATE =================
enable_auth = os.getenv("ENABLE_AUTH", "true").lower() == "true"
auth_file_path = pathlib.Path("config/auth.yaml")
auth_example_path = pathlib.Path("config/auth.yaml.example")
authenticator = None
is_using_cloud_secrets = False
auth_config = None

if enable_auth:
    # 1. PRIORITY: Check Streamlit Cloud Secrets safely (no local file needed in cloud)
    secrets_creds = safe_get_secret("credentials")
    if secrets_creds:
        try:
            auth_config = {
                "credentials": to_clean_dict(secrets_creds),
                "cookie": to_clean_dict(safe_get_secret("cookie", {}))
            }
            is_using_cloud_secrets = True
        except Exception as e:
            st.warning(f"Could not parse credentials from Streamlit Secrets: {e}")

    # 2. FALLBACK: Check local config/auth.yaml (or create from template if missing)
    if not auth_config:
        if not auth_file_path.exists() and auth_example_path.exists():
            import shutil
            auth_file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(auth_example_path, auth_file_path)

        if auth_file_path.exists():
            try:
                with open(auth_file_path, "r", encoding="utf-8") as f:
                    auth_config = yaml.safe_load(f)
            except Exception as e:
                st.warning(f"Could not load local authentication config: {e}")

    # 3. Dynamic Cookie Secret & Authenticator Initialization
    if auth_config and "credentials" in auth_config:
        # Generate a fallback session key if none provided
        if "_session_auth_cookie_key" not in st.session_state:
            st.session_state["_session_auth_cookie_key"] = secrets.token_hex(32)

        # Dynamic Cookie Secret: Checked from env variable, st.secrets, or config
        cloud_cookie_key = safe_get_secret("AUTH_COOKIE_KEY")
        cloud_cookie_dict = safe_get_secret("cookie")
        if cloud_cookie_dict and hasattr(cloud_cookie_dict, "get"):
            cloud_cookie_key = cloud_cookie_key or cloud_cookie_dict.get("key")

        cookie_key = (
            os.getenv("AUTH_COOKIE_KEY")
            or cloud_cookie_key
            or auth_config.get("cookie", {}).get("key")
            or st.session_state["_session_auth_cookie_key"]
        )

        cookie_name = auth_config.get("cookie", {}).get("name", "market_research_auth_cookie")
        expiry_days = float(auth_config.get("cookie", {}).get("expiry_days", 30.0))

        authenticator = stauth.Authenticate(
            credentials=auth_config["credentials"],
            cookie_name=cookie_name,
            cookie_key=cookie_key,
            cookie_expiry_days=expiry_days
        )

if authenticator:
    auth_status = st.session_state.get("authentication_status")

    if not auth_status:
        tab_login, tab_register = st.tabs(["🔑 Sign In", "📝 Create Account"])

        with tab_login:
            authenticator.login(location="main")
            auth_status = st.session_state.get("authentication_status")
            if auth_status is False:
                st.error("❌ Incorrect username or password. Please try again.")
            elif auth_status is None:
                st.info("🔒 Please sign in to access the Market Research Agent, or switch to **Create Account** to register.")

        with tab_register:
            try:
                email, username, name = authenticator.register_user(
                    location="main",
                    captcha=False,
                    roles=["analyst"]
                )
                if email:
                    st.success(f"🎉 User **{username}** registered successfully! Switch to the **Sign In** tab to log in.")
                    if is_using_cloud_secrets:
                        st.info("💡 Running via Streamlit Cloud Secrets. For permanent access across cloud restarts, update your Cloud Secrets.")
                    elif auth_file_path.exists():
                        with open(auth_file_path, "w", encoding="utf-8") as f:
                            yaml.safe_dump(auth_config, f, default_flow_style=False)
            except Exception as e:
                st.error(f"Registration error: {e}")

        # Stop execution so unauthorized users cannot access the app
        st.stop()


# ================= SIDEBAR =================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bullish.png", width=64)
    st.title("Settings & Status")

    if authenticator and st.session_state.get("authentication_status"):
        user_name = st.session_state.get("name", "User")
        st.markdown(f"👤 Logged in as **{user_name}**")
        try:
            authenticator.logout(button_name="Log out", location="sidebar")
        except Exception:
            pass
        st.divider()

    st.subheader("🔑 API Key Status")
    groq_key_present = bool(os.getenv("GROQ_API_KEY") or os.getenv("groq_api_key"))
    openai_key_present = bool(os.getenv("OPENAI_API_KEY") or os.getenv("openai_api_key"))
    serper_key_present = bool(os.getenv("SERPER_API_KEY") or os.getenv("serper_api_key"))

    col_k1, col_k2 = st.columns(2)
    with col_k1:
        if groq_key_present:
            st.markdown('<span class="status-badge badge-ready">✓ Groq Key Set</span>', unsafe_allow_html=True)
        elif openai_key_present:
            st.markdown('<span class="status-badge badge-ready">✓ OpenAI Key Set</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge badge-missing">✗ LLM Key Missing</span>', unsafe_allow_html=True)

    with col_k2:
        if serper_key_present:
            st.markdown('<span class="status-badge badge-ready">✓ Serper Set</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge badge-missing">✗ Serper Missing</span>', unsafe_allow_html=True)

    with st.expander("Configure Keys in Session"):
        custom_groq = st.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY") or os.getenv("groq_api_key") or "")
        custom_openai = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY") or os.getenv("openai_api_key") or "")
        custom_serper = st.text_input("Serper API Key", type="password", value=os.getenv("SERPER_API_KEY") or os.getenv("serper_api_key") or "")
        if custom_groq:
            os.environ["GROQ_API_KEY"] = custom_groq
        if custom_openai:
            os.environ["OPENAI_API_KEY"] = custom_openai
        if custom_serper:
            os.environ["SERPER_API_KEY"] = custom_serper

    st.divider()

    st.subheader("🤖 Model Configuration")
    env_model = os.getenv("MODEL", "openai/gpt-oss-120b")
    available_models = [
        "openai/gpt-oss-120b",
        "groq/llama-3.3-70b-versatile",
        "groq/llama-3.1-70b-versatile",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gemini/gemini-1.5-pro",
        "claude-3-5-sonnet-20241022"
    ]
    if env_model not in available_models:
        available_models.insert(0, env_model)
            
    default_idx = available_models.index(env_model)
    selected_model = st.selectbox("Select LLM Model", available_models, index=default_idx)
    os.environ["MODEL"] = selected_model

    st.divider()

    st.subheader("👥 Multi-Agent Workflow")
    st.markdown("""
    **Sequential Pipeline**:
    1. **Market Specialist**: TAM / SAM / SOM & trends
    2. **Competitive Analyst**: Competitor matrix & gaps
    3. **Customer Researcher**: Personas & pain points
    4. **Product Strategist**: MVP features & roadmap
    5. **Business Analyst**: Investment memo & financials
    """)

    st.divider()

    # Past Reports Viewer
    st.subheader("📁 Saved Reports")
    saved_reports = list_saved_reports()
    if saved_reports:
        report_names = [r.name for r in saved_reports]
        selected_report_name = st.selectbox("View previous report", ["Select a report..."] + report_names)
        if selected_report_name != "Select a report...":
            report_path = pathlib.Path("reports") / selected_report_name
            if report_path.exists():
                with open(report_path, "r", encoding="utf-8") as f:
                    st.session_state["viewed_report"] = f.read()
                    st.session_state["viewed_report_name"] = selected_report_name
    else:
        st.caption("No past reports found in `reports/` yet.")


# ================= MAIN AREA =================
st.markdown('<div class="main-header">📈 AI Market Research Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Autonomous multi-agent research pipeline conducting in-depth market analysis, competitive benchmarking, customer persona modeling, and business strategy formulation.</div>', unsafe_allow_html=True)

# Input Form
with st.container():
    st.markdown("### 💡 What product or venture idea do you want to research?")
    
    default_idea = "An AI powered tool that summarizes youtube videos on my channel and posts the summary on various social media platforms like LinkedIn, Instagram, Facebook, X, WhatsApp"
    
    product_idea = st.text_area(
        label="Product Idea Description",
        value=default_idea,
        height=110,
        placeholder="Describe your product idea, target audience, key features, and problem it solves..."
    )

    with st.expander("⚙️ Optional Strategic Focus"):
        col1, col2 = st.columns(2)
        with col1:
            target_geo = st.text_input("Target Geography", placeholder="e.g., Global, North America, India, Europe")
        with col2:
            industry_sector = st.text_input("Industry / Vertical", placeholder="e.g., Creator Economy, EdTech, SaaS, Healthcare")

    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        start_btn = st.button("🚀 Run Research Crew", type="primary", use_container_width=True)
    with col_info:
        st.caption("The 5 agents will collaborate sequentially using web search and scraping tools. Typically takes 2-5 minutes depending on research depth.")

# Research Execution
if start_btn:
    if not product_idea.strip():
        st.error("Please enter a product idea before running the research crew.")
    else:
        # Build enriched input if additional context provided
        full_product_idea = product_idea.strip()
        if target_geo:
            full_product_idea += f"\nTarget Geography: {target_geo}"
        if industry_sector:
            full_product_idea += f"\nIndustry Sector: {industry_sector}"

        st.info("Initiating Multi-Agent Research Crew. Progress and agent thought processes are streamed below:")

        progress_container = st.container()
        with progress_container:
            st.markdown("#### 🔄 Live Agent Execution & Search Logs")
            log_placeholder = st.empty()
            status_text = st.status("Initializing Crew...", expanded=True)

        redirector = StreamlitLogRedirector(log_placeholder)
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:
            status_text.update(label="Agents actively analyzing market, searching competitors, and drafting strategy...", state="running")
            sys.stdout = redirector
            sys.stderr = redirector

            # Dynamic import of MarketResearchAgent
            from market_research_agent.crew import MarketResearchAgent
            from crewai import LLM

            ensure_reports_dir()

            # Execute crew
            crew_instance = MarketResearchAgent(llm=LLM(model=selected_model)).crew()
            result = crew_instance.kickoff(inputs={"product_idea": full_product_idea})

            # Check output file
            report_file = pathlib.Path("reports/report.md")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_report_file = pathlib.Path(f"reports/report_{timestamp}.md")

            final_report_text = ""
            if report_file.exists():
                with open(report_file, "r", encoding="utf-8") as f:
                    final_report_text = f.read()
                # Also save a timestamped copy so it appears in history
                with open(backup_report_file, "w", encoding="utf-8") as f:
                    f.write(final_report_text)
            elif result:
                final_report_text = str(result)
                with open(report_file, "w", encoding="utf-8") as f:
                    f.write(final_report_text)
                with open(backup_report_file, "w", encoding="utf-8") as f:
                    f.write(final_report_text)

            status_text.update(label="✅ Market Research Completed Successfully!", state="complete", expanded=False)
            st.session_state["latest_report"] = final_report_text
            st.session_state["viewed_report"] = final_report_text
            st.session_state["viewed_report_name"] = f"report_{timestamp}.md"

        except Exception as e:
            status_text.update(label="❌ An error occurred during execution", state="error", expanded=True)
            st.error(f"Execution Error: {e}")
            st.markdown("""
            **Troubleshooting Tips:**
            - Verify your `OPENAI_API_KEY` (or chosen LLM provider key) is valid and has available quota.
            - Ensure `SERPER_API_KEY` is configured if Serper web search is being used.
            - Check internet connectivity.
            """)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


# ================= REPORT DISPLAY SECTION =================
display_report = st.session_state.get("viewed_report") or st.session_state.get("latest_report")
report_source_name = st.session_state.get("viewed_report_name", "report.md")

# If no report in session, but report.md exists on disk, load it
if not display_report and pathlib.Path("reports/report.md").exists():
    try:
        with open("reports/report.md", "r", encoding="utf-8") as f:
            display_report = f.read()
            report_source_name = "report.md"
    except Exception:
        pass

if display_report:
    st.divider()
    header_col, download_col = st.columns([3, 1])
    with header_col:
        st.markdown(f"### 📑 Market Research Report (`{report_source_name}`)")
    with download_col:
        st.download_button(
            label="⬇️ Download Report (.md)",
            data=display_report,
            file_name=report_source_name,
            mime="text/markdown",
            use_container_width=True
        )

    tab_report, tab_raw = st.tabs(["📄 Formatted Report", "📝 Raw Markdown"])

    with tab_report:
        st.markdown(display_report)

    with tab_raw:
        st.code(display_report, language="markdown")
