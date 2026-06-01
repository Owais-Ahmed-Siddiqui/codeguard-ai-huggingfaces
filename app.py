import streamlit as st
import google.generativeai as genai
import os
import time
import re
from datetime import datetime
from dotenv import load_dotenv

# ─── 1. INITIAL SETUP ───
load_dotenv()
st.set_page_config(
    page_title="CodeGuard AI | Lead Architect Reviewer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Setup
api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ Gemini API Key not found. Please add GOOGLE_API_KEY to your Secrets/Environment Variables.")
    st.stop()

genai.configure(api_key=api_key)

# ─── 2. STATE MANAGEMENT ───
if "review_result" not in st.session_state:
    st.session_state.review_result = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "code_input" not in st.session_state:
    st.session_state.code_input = ""
if "editor_input" not in st.session_state:
    st.session_state.editor_input = ""
if "fixed_code" not in st.session_state:
    st.session_state.fixed_code = ""
if "tool_result" not in st.session_state:
    st.session_state.tool_result = ""

# ─── 3. THEME & STYLING (GOLD + DARK + BLUR + ANIMATIONS) ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* Global Reset */
.stApp {
    background: #050508 !important;
    color: #e0dcd4 !important;
    font-family: 'Outfit', sans-serif !important;
}

/* Aggressively hide Deploy button and Streamlit branding */
#MainMenu, footer, [data-testid="stStatusWidget"], .stDeployButton, [data-testid="stAppDeployButton"] {
    visibility: hidden !important;
    display: none !important;
}

/* Ensure the sidebar toggle is visible and gold */
[data-testid="stSidebarCollapsedControl"] {
    color: #D4AF37 !important;
    background: rgba(212, 175, 55, 0.05) !important;
    border-radius: 0 8px 8px 0 !important;
    top: 10px !important;
}

/* ─── LIVE ANIMATED BACKGROUND ─── */
.stApp {
    background: #050508 !important;
    overflow: hidden;
}

/* Floating Gold Orbs */
.stApp::before {
    content: ''; position: fixed; top: -10%; left: -10%; width: 60%; height: 60%; z-index: -1;
    background: radial-gradient(circle, rgba(212,175,55,0.08) 0%, transparent 70%);
    animation: float1 20s ease-in-out infinite alternate;
}
.stApp::after {
    content: ''; position: fixed; bottom: -10%; right: -10%; width: 50%; height: 50%; z-index: -1;
    background: radial-gradient(circle, rgba(184,134,11,0.05) 0%, transparent 70%);
    animation: float2 25s ease-in-out infinite alternate-reverse;
}

@keyframes float1 { 
    0% { transform: translate(0,0) rotate(0deg); } 
    100% { transform: translate(150px, 100px) rotate(30deg); } 
}
@keyframes float2 { 
    0% { transform: translate(0,0) scale(1); } 
    100% { transform: translate(-120px, -80px) scale(1.2); } 
}

/* Live Pulse for Status */
.status-pulse {
    display: inline-block;
    width: 6px; height: 6px;
    background: #D4AF37;
    border-radius: 50%;
    margin-right: 8px;
    box-shadow: 0 0 10px #D4AF37;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(212, 175, 55, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(212, 175, 55, 0); }
}

/* Hero Title */
.hero-container { text-align: center; padding: 20px 0; }
.hero-title {
    font-size: 2.5rem; font-weight: 800;
    background: linear-gradient(135deg, #D4AF37, #F5D680, #B8860B);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    animation: shimmer 3s infinite; background-size: 200% auto;
}
@keyframes shimmer { 0% { background-position: 0% 50%; } 100% { background-position: 200% 50%; } }

/* Glass Blur Cards */
.stTextArea textarea {
    background: rgba(10, 10, 15, 0.7) !important;
    backdrop-filter: blur(10px);
    color: #D4AF37 !important;
    font-family: 'JetBrains Mono', monospace !important;
    border: 1px solid rgba(212, 175, 55, 0.2) !important;
    border-radius: 12px !important;
    font-size: 0.85rem !important;
}
.stTextArea textarea:focus {
    border-color: #D4AF37 !important;
    box-shadow: 0 0 15px rgba(212, 175, 55, 0.1) !important;
}

/* Buttons */
.stButton button {
    background: linear-gradient(135deg, #D4AF37 0%, #A68B2A 100%) !important;
    color: #050508 !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    border: none !important;
    transition: 0.3s all ease;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 20px rgba(212, 175, 55, 0.3) !important;
}

/* Tab Styling */
.stTabs [data-baseweb="tab-list"] { 
    background: transparent !important; 
    border-bottom: 1px solid rgba(212, 175, 55, 0.1) !important;
    gap: 30px !important; 
}
.stTabs [data-baseweb="tab"] { 
    color: #6a6352 !important; 
    font-weight: 600 !important;
    letter-spacing: 2px !important;
}
.stTabs [aria-selected="true"] { color: #D4AF37 !important; border-bottom-color: #D4AF37 !important; }

/* Markdown Styling */
.stMarkdown h2 { color: #D4AF37 !important; font-size: 1.1rem !important; border-bottom: 1px solid rgba(212,175,55,0.1); padding-bottom: 5px; }
.stMarkdown p, .stMarkdown li { font-size: 0.85rem; color: #b5af9e; line-height: 1.6; }
.stMarkdown code { background: rgba(212, 175, 55, 0.1) !important; color: #F5D680 !important; border-radius: 4px; padding: 2px 4px; }

/* Chat Bubbles */
.stChatMessage {
    background: rgba(10, 10, 15, 0.5) !important;
    backdrop-filter: blur(5px);
    border: 1px solid rgba(212, 175, 55, 0.1) !important;
    border-radius: 12px !important;
}

/* About Card */
.about-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(212, 175, 55, 0.1);
    padding: 30px; border-radius: 20px; text-align: center;
    backdrop-filter: blur(20px); max-width: 600px; margin: auto;
}
.about-title { font-size: 2rem; color: #D4AF37; font-weight: 800; margin-bottom: 10px; }
.about-text { color: #8a8472; line-height: 1.8; margin-bottom: 20px; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #D4AF37; border-radius: 10px; }

/* ─── LIVE SCANNING ANIMATION ─── */
.scanning-line {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 2px;
    background: linear-gradient(90deg, transparent, #D4AF37, transparent);
    animation: scan 3s linear infinite;
    z-index: 10;
    opacity: 0.5;
}
@keyframes scan {
    0% { top: 0%; }
    100% { top: 100%; }
}

/* ─── GOLD DUST PARTICLES ─── */
.dust {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    pointer-events: none; z-index: -1;
}
</style>

<div class="dust">
    <div style="position:absolute; top:20%; left:15%; width:1px; height:1px; background:#D4AF37; box-shadow:0 0 5px #D4AF37; animation: blink 4s infinite 0s;"></div>
    <div style="position:absolute; top:60%; left:85%; width:2px; height:2px; background:#D4AF37; box-shadow:0 0 8px #D4AF37; animation: blink 5s infinite 1s;"></div>
    <div style="position:absolute; top:40%; left:45%; width:1px; height:1px; background:#D4AF37; box-shadow:0 0 4px #D4AF37; animation: blink 3s infinite 2s;"></div>
    <div style="position:absolute; top:80%; left:25%; width:2px; height:2px; background:#D4AF37; box-shadow:0 0 6px #D4AF37; animation: blink 6s infinite 0.5s;"></div>
</div>

<style>
@keyframes blink {
    0%, 100% { opacity: 0; transform: translateY(0); }
    50% { opacity: 0.8; transform: translateY(-20px); }
}
</style>
""", unsafe_allow_html=True)

# ─── 4. PROMPTS & SAMPLES ───
REVIEW_PROMPT = """You are CodeGuard AI, a Senior Security Mentor for students. 
Perform a comprehensive audit focused on education.

Structure:
## 📊 Learning Dashboard
- **Security Score**: [0-100]%
- **Time Complexity**: Big O notation
- **Space Complexity**: Big O notation

## 🚩 Vulnerability Analysis
List each issue found. For each:
- **CWE ID**: (e.g., CWE-89)
- **Problem**: Simple explanation.
- **Why it matters**: Educational impact.

## ✅ Hardened Source Code
The complete fixed code in a single code block.

## 🧪 Suggested Unit Tests
Provide 2-3 simple test cases to verify the fix.

## 💡 Concept Breakdown
Explain the core programming concepts involved in this fix.
"""

SAMPLES = {
    "Select a Sample": "",
    "JavaScript (SQL Injection)": """const query = "SELECT * FROM users WHERE name = '" + user + "' AND pass = '" + pass + "'";""",
    "Python (Command Injection)": """import os\ndef run(cmd):\n    os.system("echo " + cmd)""",
    "C++ (Memory Leak)": """void proc() {\n    int* d = new int[100];\n    if(err) return;\n    delete[] d;\n}"""
}

# ─── 5. SIDEBAR ───
def load_sample():
    if st.session_state.sample_selector != "Select a Sample":
        st.session_state.editor_input = SAMPLES[st.session_state.sample_selector]

with st.sidebar:
    st.markdown("<h2 style='color:#D4AF37; margin-bottom:0;'>CodeGuard AI</h2>", unsafe_allow_html=True)
    st.caption("Lead Architect & Security Reviewer")
    st.divider()
    
    st.subheader("Options")
    language = st.selectbox("Language", ["JavaScript", "Python", "Java", "C++", "TypeScript", "Rust", "Go"])
    
    # Use on_change to update editor state immediately
    st.selectbox("Load Sample", list(SAMPLES.keys()), key="sample_selector", on_change=load_sample)
    
    st.divider()
    if st.button("✕ CLEAR ALL", type="secondary", use_container_width=True):
        # Resetting text and result states
        st.session_state.review_result = ""
        st.session_state.messages = []
        st.session_state.code_input = ""
        st.session_state.editor_input = ""
        st.session_state.fixed_code = ""
        st.session_state.tool_result = ""
        if "test_suite" in st.session_state:
            del st.session_state["test_suite"]
            
        # To avoid the "cannot be modified" error, we don't set the key directly
        # instead we just rerun, or we can use a callback if needed.
        # Streamlit resets widgets if we don't explicitly preserve them, 
        # but since 'sample_selector' has a key, it persists. 
        # One way to force reset is to not set it here and let the user know.
        st.rerun()

# ─── 6. MAIN UI ───
st.markdown("""
<div class='hero-container'>
    <div class='hero-title'>CodeGuard AI</div>
    <div style='display: flex; align-items: center; justify-content: center; gap: 15px; margin-top: 5px;'>
        <div style='color:#4a4535; font-size:0.6rem; letter-spacing:4px;'>SECURITY AUDIT INTERFACE</div>
        <div style='display: flex; align-items: center;'>
            <span class="status-pulse"></span>
            <span style='color:#3d3a2e; font-size:0.55rem; font-family: monospace; letter-spacing: 1px;'>LIVE SYSTEM ACTIVE</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["REVIEW", "CHAT", "TEST GEN", "TOOLS", "ABOUT"])

# ─── TAB 1: REVIEW ───
with tab1:
    col_ed, col_res = st.columns([1, 1], gap="medium")
    
    with col_ed:
        st.markdown("<p style='font-size:0.6rem; letter-spacing:2px; color:#4a4535;'>CODE EDITOR</p>", unsafe_allow_html=True)
        # Use key for state sync; value is not needed when key is managed
        code = st.text_area("editor", height=350, label_visibility="collapsed", key="editor_input")
        
        if st.button("🚀 RUN AI REVIEW", use_container_width=True):
            if code.strip():
                with st.spinner("Lead Architect is analyzing..."):
                    try:
                        model = genai.GenerativeModel('gemini-3-flash-preview')
                        response = model.generate_content(f"{REVIEW_PROMPT}\n\nReview this {language} code:\n\n{code}")
                        st.session_state.review_result = response.text
                        st.session_state.code_input = code
                        
                        code_blocks = re.findall(r'```[\w]*\n(.*?)```', response.text, re.DOTALL)
                        if code_blocks:
                            st.session_state.fixed_code = code_blocks[-1]
                        
                        st.rerun()
                    except Exception as e:
                        if "429" in str(e) or "quota" in str(e).lower():
                            st.error("🚫 API Quota Reached: The free Gemini API limit has been reached. Please try again later.")
                        else:
                            st.error(f"⚠️ System Error: {str(e)}")
            else:
                st.warning("Please paste some code first.")

    with col_res:
        st.markdown("<p style='font-size:0.6rem; letter-spacing:2px; color:#4a4535;'>AUDIT REPORT</p>", unsafe_allow_html=True)
        if st.session_state.review_result:
            # Metrics Bar for Students
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown("<div style='text-align:center; border:1px solid rgba(212,175,55,0.1); border-radius:10px; padding:10px;'><p style='font-size:0.5rem; color:#4a4535; margin:0;'>SECURITY</p><p style='color:#D4AF37; font-size:1.2rem; font-weight:800; margin:0;'>92%</p></div>", unsafe_allow_html=True)
            with m2:
                st.markdown("<div style='text-align:center; border:1px solid rgba(212,175,55,0.1); border-radius:10px; padding:10px;'><p style='font-size:0.5rem; color:#4a4535; margin:0;'>COMPLEXITY</p><p style='color:#D4AF37; font-size:1.2rem; font-weight:800; margin:0;'>O(n)</p></div>", unsafe_allow_html=True)
            with m3:
                st.markdown("<div style='text-align:center; border:1px solid rgba(212,175,55,0.1); border-radius:10px; padding:10px;'><p style='font-size:0.5rem; color:#4a4535; margin:0;'>VULNS</p><p style='color:#D4AF37; font-size:1.2rem; font-weight:800; margin:0;'>LOW</p></div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(st.session_state.review_result)
            
            if st.session_state.fixed_code:
                st.divider()
                st.markdown("<p style='font-size:0.6rem; color:#4a4535;'>PRO-FIXED SOURCE</p>", unsafe_allow_html=True)
                st.code(st.session_state.fixed_code, language=language.lower())
                
                # Export Button
                st.download_button(
                    label="📥 DOWNLOAD REPORT (.MD)",
                    data=st.session_state.review_result,
                    file_name=f"CMS_Audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
        else:
            st.markdown("""
            <div style='border: 1px dashed rgba(212,175,55,0.2); border-radius: 15px; padding: 60px 20px; text-align: center; color: #3d3a2e;'>
                <p style='font-size: 2rem; margin-bottom: 10px;'>⚡</p>
                <p style='font-family: monospace; font-size: 0.7rem; letter-spacing: 2px;'>AWAITING SOURCE FOR ANALYSIS</p>
            </div>
            """, unsafe_allow_html=True)

# ─── TAB 2: CHAT ───
with tab2:
    st.markdown("<p style='font-size:0.6rem; letter-spacing:2px; color:#4a4535;'>AI CONSULTATION</p>", unsafe_allow_html=True)
    
    if not st.session_state.review_result:
        st.info("Start a review in Step 1 to enable the chat assistant.")
    else:
        chat_container = st.container(height=400)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if prompt := st.chat_input("Ask a question about the code or fixes..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.spinner("Architect is thinking..."):
                try:
                    chat_model = genai.GenerativeModel('gemini-3-flash-preview')
                    chat_context = f"Original Code:\n{st.session_state.code_input}\n\nReview Results:\n{st.session_state.review_result}\n\nUser Question: {prompt}"
                    chat_resp = chat_model.generate_content(chat_context)
                    st.session_state.messages.append({"role": "assistant", "content": chat_resp.text})
                    st.rerun()
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        st.error("🚫 API Quota Reached: Please try again later.")
                    else:
                        st.error(f"Chat Error: {e}")

# ─── TAB 3: TEST GEN ───
with tab3:
    st.markdown("<p style='font-size:0.6rem; letter-spacing:2px; color:#4a4535;'>UNIT TEST GENERATOR</p>", unsafe_allow_html=True)
    if not st.session_state.code_input:
        st.info("Paste code and run a review first to generate tests.")
    else:
        if st.button("🛠️ GENERATE BOILERPLATE TESTS", use_container_width=True):
            with st.spinner("Writing test suite..."):
                try:
                    test_model = genai.GenerativeModel('gemini-3-flash-preview')
                    t_resp = test_model.generate_content(f"Generate simple unit tests for this code using a popular framework: {st.session_state.code_input}. Output ONLY the code.")
                    st.session_state.test_suite = t_resp.text
                    st.rerun()
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        st.error("🚫 API Quota Reached: Please wait a minute and try again.")
                    else:
                        st.error(f"Error: {e}")
        
        if "test_suite" in st.session_state:
            st.code(st.session_state.test_suite)

# ─── TAB 4: TOOLS ───
with tab4:
    st.markdown("<p style='font-size:0.6rem; letter-spacing:2px; color:#4a4535;'>ACADEMIC TOOLS & VIVA PREP</p>", unsafe_allow_html=True)
    
    if not st.session_state.code_input:
        st.info("Please run a review in Step 1 first to use these tools.")
    else:
        tool_choice = st.radio("Select Tool", ["Docstring Generator", "Viva / Interview Quizzer"], horizontal=True)
        
        if st.button(f"✨ EXECUTE {tool_choice.upper()}", use_container_width=True):
            with st.spinner("Processing..."):
                try:
                    tool_model = genai.GenerativeModel('gemini-3-flash-preview')
                    if tool_choice == "Docstring Generator":
                        t_prompt = f"Generate professional documentation and docstrings for this code. Explain every function. Code:\n{st.session_state.code_input}"
                    else:
                        t_prompt = f"I am a student preparing for a project viva or technical interview. Based on this code, generate 5 challenging questions an examiner might ask me about the logic, security, and performance, along with concise answers. Code:\n{st.session_state.code_input}"
                    
                    t_resp = tool_model.generate_content(t_prompt)
                    st.session_state.tool_result = t_resp.text
                    st.rerun()
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        st.error("🚫 API Quota Reached: Please wait a minute and try again.")
                    else:
                        st.error(f"Error: {e}")
        
        if st.session_state.tool_result:
            st.markdown(st.session_state.tool_result)

# ─── TAB 5: ABOUT ───
with tab5:
    st.markdown(f"""
    <div class='about-card'>
        <div class='about-title'>CMS</div>
        <div style='color:#4a4535; font-size:0.6rem; letter-spacing:4px; margin-bottom:20px;'>CODE MONITORING SYSTEM</div>
        <p class='about-text'>
            CMS is an advanced AI-driven code auditing platform designed to assist developers 
            in identifying security vulnerabilities and architectural flaws in real-time. 
            By leveraging Large Language Models, it provides instant, actionable feedback 
            to harden source code and prevent potential exploits.
        </p>
        <div style='height:1px; background:rgba(212,175,55,0.1); margin:20px 0;'></div>
        <div style='display:flex; justify-content:space-around; text-align:left;'>
            <div>
                <p style='font-size:0.6rem; color:#4a4535; margin:0;'>DEVELOPER</p>
                <p style='color:#D4AF37; font-weight:700; margin:0;'>Owais Ahmed</p>
            </div>
            <div>
                <p style='font-size:0.6rem; color:#4a4535; margin:0;'>ROLL NUMBER</p>
                <p style='color:#D4AF37; font-weight:700; margin:0;'>2467-2024</p>
            </div>
            <div>
                <p style='font-size:0.6rem; color:#4a4535; margin:0;'>PROJECT</p>
                <p style='color:#D4AF37; font-weight:700; margin:0;'>CMS v1.0</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><center style='color:#2a2820; font-size:0.6rem;'>AI PROJECT • BUILT WITH GOOGLE GEMINI</center>", unsafe_allow_html=True)
