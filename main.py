"""
PaperPilot - AI Research Assistant
A Streamlit application for searching and analyzing academic papers across multiple databases
"""

import streamlit as st
import asyncio
from datetime import datetime
from mcp_server.client import agent_instance

# Command-line interface (commented out in favor of Streamlit UI)
# if __name__ == "__main__":
#     user_prompt = input("Enter your research topic or keywords: ")
#     asyncio.run(agent_instance(user_prompt, model="gpt-4o", temperature=0, timeout=60))

# Page configuration
st.set_page_config(
    page_title="PaperPilot - AI Research Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(120deg, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #64748b;
        margin-bottom: 2rem;
    }
    .result-card {
        padding: 1.5rem;
        border-radius: 10px;
        background: white;
        border: 1px solid #e2e8f0;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(120deg, #2563eb, #7c3aed);
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        border: none;
        font-size: 1.1rem;
    }
    .stButton>button:hover {
        background: linear-gradient(120deg, #1d4ed8, #6d28d9);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "search_count" not in st.session_state:
    st.session_state.search_count = 0

# Header
st.markdown('<div class="main-header">📚 PaperPilot</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Your AI-Powered Research Assistant for Academic Papers</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/books.png", width=100)
    st.markdown("### 🔍 Search Settings")
    
    # Model selection
    model = st.selectbox(
        "AI Model",
        ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        index=0,
        help="Select the OpenAI model for processing"
    )
    
    # Temperature slider
    temperature = st.slider(
        "Creativity Level",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.1,
        help="0 = Focused and precise, 1 = Creative and varied"
    )
    
    # Timeout setting
    timeout = st.slider(
        "Timeout (seconds)",
        min_value=30,
        max_value=300,
        value=60,
        step=10,
        help="Maximum time to wait for response"
    )
    
    st.markdown("---")
    
    # Database info
    st.markdown("### 📊 Available Databases")
    st.markdown("""
    - 🎓 **Google Scholar** - Cross-disciplinary research
    - 🔬 **arXiv** - Physics, CS, Math
    - 🧬 **PubMed** - Medical & Life Sciences
    """)
    
    st.markdown("---")
    
    # Statistics
    st.markdown("### 📈 Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Searches", st.session_state.search_count)
    with col2:
        st.metric("History", len(st.session_state.search_history))
    
    # Clear history button
    if st.button("🗑️ Clear History"):
        st.session_state.search_history = []
        st.session_state.search_count = 0
        st.rerun()

# Main content area
st.markdown("---")

# Search examples
with st.expander("💡 Search Examples & Tips", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🔬 By Topic**")
        st.code("machine learning in healthcare")
        st.code("quantum computing applications")
    with col2:
        st.markdown("**👤 By Author**")
        st.code("papers by Geoffrey Hinton")
        st.code("Yann LeCun neural networks")
    with col3:
        st.markdown("**📅 By Date**")
        st.code("CRISPR research since 2020")
        st.code("recent COVID-19 vaccines")

# Main search interface
st.markdown("### 🔍 What would you like to research?")

# Search input with form for Enter key support
with st.form(key="search_form", clear_on_submit=False):
    user_query = st.text_area(
        "Enter your research question or topic (Press Ctrl+Enter to search):",
        placeholder="Example: Find recent papers on brain functional connectivity using fMRI...",
        height=100,
        help="Be specific! Mention authors, topics, or date ranges for better results."
    )
    
    # Search button
    search_button = st.form_submit_button("🚀 Search Papers", type="primary")

# Process search
if search_button and user_query:
    with st.spinner("🔍 Searching across Google Scholar, arXiv, and PubMed..."):
        try:
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🔌 Connecting to research databases...")
            progress_bar.progress(25)
            
            status_text.text("🤖 AI is analyzing your query...")
            progress_bar.progress(50)
            
            # Run the agent
            result = asyncio.run(
                agent_instance(
                    user_query, 
                    model=model, 
                    temperature=temperature, 
                    timeout=timeout
                )
            )
            
            status_text.text("📊 Processing results...")
            progress_bar.progress(75)
            
            # Store results
            st.session_state.current_result = result
            st.session_state.search_count += 1
            st.session_state.search_history.append({
                "query": user_query,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model": model
            })
            
            progress_bar.progress(100)
            status_text.text("✅ Search complete!")
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 **Troubleshooting Tips:**\n- Make sure all MCP servers are running\n- Check your API keys in .env file\n- Verify internet connection")

# Display results
if st.session_state.current_result:
    st.markdown("---")
    st.markdown("### 📄 Results")
    
    # Display the result in a nice card
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown(st.session_state.current_result)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📋 Copy Results"):
            st.code(st.session_state.current_result)
    with col2:
        if st.button("💾 Save to File"):
            # Save results
            filename = f"research_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w") as f:
                f.write(f"Query: {user_query}\n\n")
                f.write(f"Results:\n{st.session_state.current_result}")
            st.success(f"✅ Saved to {filename}")
    with col3:
        if st.button("🔄 New Search"):
            st.session_state.current_result = None
            st.rerun()

# Search history
if st.session_state.search_history:
    st.markdown("---")
    with st.expander("📜 Search History", expanded=False):
        for idx, search in enumerate(reversed(st.session_state.search_history[-10:])):
            st.markdown(f"""
            **{idx + 1}.** {search['query']}  
            *{search['timestamp']}* | Model: `{search['model']}`
            """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**🔗 Databases**")
    st.markdown("Google Scholar • arXiv • PubMed")
with col2:
    st.markdown("**🤖 Powered by**")
    st.markdown("OpenAI GPT-4 • FastMCP")
with col3:
    st.markdown("**📚 PaperPilot**")
    st.markdown("Academic Research Assistant")
