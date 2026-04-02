import streamlit as st
import re
from rag import process_urls, generate_answer

st.set_page_config(page_title="Real-Estate-Q-A-Tool", layout="wide", page_icon="🤖")
st.markdown("""
    <style>
        /* Custom Typography Alignments */
        h2 {
            font-size: 2.0rem !important;
            font-weight: 700 !important;
            margin-bottom: 1.2rem !important;
            color: #ffffff !important;
        }
        
        h3 {
            font-size: 1.6rem !important;
            font-weight: 600 !important;
            margin-bottom: 1rem !important;
            color: #e2e8f0 !important;
        }

        /* Title */
        .main-title { 
            font-size: 3rem; 
            font-weight: 800; 
            text-align: center; 
            color: #ffffff;
            margin-bottom: 2rem;
            animation: fadeInDown 0.8s ease-out;
            padding-top: 1.5rem;
        }
        
        /* Glassmorphism Answer Box */
        .answer-box {
            background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            color: #e2e8f0;
            padding: 2.5rem;
            border-radius: 1.2rem;
            font-size: 1.15rem;
            line-height: 1.6;
            box-shadow: 0 15px 35px -10px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            animation: fadeInUp 0.6s ease-out;
            margin-bottom: 2.5rem;
        }
        
        /* Typography hierarchy and spacing */
        .answer-box p {
            margin-bottom: 0.8rem;
            margin-top: 0;
            font-size: 1.15rem !important;
            color: #e2e8f0 !important;
        }
        .answer-box b, .answer-box strong {
            font-weight: 700 !important;
            color: #ffffff !important;
        }
        .answer-box ul, .answer-box ol {
            margin-bottom: 1rem;
            margin-left: 2rem;
        }
        .answer-box li {
            margin-bottom: 0.5rem;
            font-size: 1.25rem !important;
            color: #f8fafc !important;
        }
        .answer-box h1, .answer-box h2, .answer-box h3, .answer-box h4 {
            color: #ffffff !important;
            font-weight: 800 !important;
            margin-top: 0 !important;
            margin-bottom: 0.8rem !important;
            line-height: 1.3 !important;
        }
        .answer-box h3 {
            font-size: 1.5rem !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 0.4rem;
        }
        
        /* Sleek Pill Links */
        .source-link a {
            display: inline-flex;
            align-items: center;
            background: rgba(78, 101, 255, 0.1);
            color: #8da0ff !important;
            padding: 0.6rem 1.4rem;
            border-radius: 2rem;
            text-decoration: none;
            font-weight: 500;
            font-size: 1.1rem;
            margin-right: 1rem;
            margin-bottom: 1rem;
            border: 1px solid rgba(78, 101, 255, 0.3);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            animation: fadeInUp 0.8s ease-out;
            /* Fix for long runaway URLs breaking out of the box */
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .source-link a:hover {
            background: #4E65FF;
            color: #ffffff !important;
            transform: translateY(-3px);
            box-shadow: 0 10px 25px -5px rgba(78, 101, 255, 0.5);
            border-color: #4E65FF;
        }
        
        /* Animations */
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Streamlit Element Styling to Increase Font Sizes */
        p, .stMarkdown p {
            font-size: 1.15rem !important;
            color: #cbd5e1 !important;
        }
        
        .stTextInput label, .stSelectbox label {
            font-size: 1.25rem !important;
            font-weight: 600 !important;
            color: #e2e8f0 !important;
            padding-bottom: 0.5rem !important;
        }
        
        .stTextInput input {
            font-size: 1.15rem !important;
            padding: 0.8rem 1rem !important;
        }
        
        .stButton button {
            font-size: 1.2rem !important;
            font-weight: 600 !important;
            padding: 0.6rem 1.5rem !important;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🤖 Real-Estate-Q-A-Tool</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar inputs
with st.sidebar.container(border=True):
    st.header("🔗 Enter Article URLs")

    # Initialize session state for URL inputs if it doesn't exist
    if 'url_count' not in st.session_state:
        st.session_state.url_count = 1

    urls = []
    for i in range(st.session_state.url_count):
        url = st.text_input(f"URL {i+1}", key=f"url_input_{i}", label_visibility="collapsed", placeholder=f"Enter URL {i+1}...")
        urls.append(url)

    if st.button("➕ Add URL"):
        st.session_state.url_count += 1
        st.rerun()

    st.markdown("---")
    process_url_button = st.button("🚀 Process URLs")

# Placeholder for feedback
placeholder = st.empty()

# Handle URL Processing
if process_url_button:
    valid_urls = [url.strip().lstrip(':').strip() for url in urls if url.strip()]
    if not valid_urls:
        st.sidebar.warning("⚠️ You must provide at least one valid URL.")
    else:
        try:
            progress_bar = placeholder.progress(0, text="⏳ **Initializing process...**")
            total_steps = 6
            for i, status in enumerate(process_urls(valid_urls)):
                progress = min(int(((i + 1) / total_steps) * 100), 100)
                progress_bar.progress(progress, text=f"⏳ **{status}**")
            
            st.session_state["urls_processed"] = True 
        except Exception as e:
            placeholder.error(f"❌ Error during processing: {e}")
            
if st.session_state.get("urls_processed"):
    placeholder.success("✅ URLs processed successfully.")

with st.form("query_form"):
    st.markdown("## Ask a Question")
    query = st.text_input("💬 Enter your question here")
    submit_button = st.form_submit_button("Ask ✨")

if submit_button and query:
    if not st.session_state.get("urls_processed"):
        st.error("⚠️ You must process URLs first before asking a question.")
    else:
        try:
            with st.spinner("Generating answer..."):
                answer, sources = generate_answer(query)

            # Convert basic markdown formatting to HTML for the custom styling box
            paragraphs = answer.split("\n\n")
            formatted_answer = ""
            for p in paragraphs:
                pt = p.strip()
                if pt:
                    pt_formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', pt)
                    # Support for headings and LLM fallbacks
                    if pt_formatted.startswith('### '):
                        formatted_answer += f"<h3>{pt_formatted[4:]}</h3>\n"
                    elif pt_formatted.startswith('## '):
                        formatted_answer += f"<h2>{pt_formatted[3:]}</h2>\n"
                    elif pt_formatted.startswith('# '):
                        formatted_answer += f"<h1>{pt_formatted[2:]}</h1>\n"
                    elif pt_formatted.startswith('<b>') and pt_formatted.endswith('</b>') and len(pt_formatted) < 100:
                        formatted_answer += f"<h3>{pt_formatted.replace('<b>', '').replace('</b>', '')}</h3>\n"
                    else:
                        formatted_answer += f"<p>{pt_formatted}</p>\n"

            st.markdown("### 🧠 Answer")
            st.markdown(f'<div class="answer-box">\n{formatted_answer}\n</div>', unsafe_allow_html=True)

            if sources:
                sources_html = ""
                seen_sources = set()
                for source in re.split(r'[,\n ]+', sources):
                    # Clean up any markdown hallucinated by the model (asterisks, brackets, etc.)
                    clean_src = source.strip('*[]() \n\t')
                    
                    # Ensure the extracted source is actually a valid URL
                    if clean_src and clean_src.startswith("http") and clean_src not in seen_sources:
                        seen_sources.add(clean_src)
                        sources_html += f'<span class="source-link"><a href="{clean_src}" target="_blank">🔗 {clean_src}</a></span>'
                
                if sources_html:
                    st.markdown("### 📄 Sources used for this conclusion")
                    st.markdown(sources_html, unsafe_allow_html=True)
        except RuntimeError:
            st.error("⚠️ You must process URLs first.")
