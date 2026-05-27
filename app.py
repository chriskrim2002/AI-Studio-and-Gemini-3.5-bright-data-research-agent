import streamlit as st
import os
from agent import run_research_agent

# Set up page configurations
st.set_page_config(
    page_title="Gemini 3.5 Autonomous Research Agent",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Gemini 3.5 Autonomous Research Agent")
st.subheader("Powered by Google AI Studio & Bright Data")
st.write(
    "Enter any company name below. The agent will autonomously execute parallel Google searches, "
    "scrape target webpages with BeautifulSoup, and synthesize a complete Markdown report."
)

# Input field
company = st.text_input("Enter Company or Startup Name:", placeholder="e.g., Mistral AI, Udio, Cursor")

if st.button("Generate Research Report", type="primary"):
    if not company:
        st.warning("Please enter a company name.")
    else:
        # Visual loading spinner for the user
        with st.spinner(f"Agent is actively searching and scraping web sources for '{company}'..."):
            try:
                # Runs the main agent loop
                report = run_research_agent(company)
                
                st.success("Research Complete!")
                
                # Split page into columns
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("### 📄 Generated Report")
                    st.markdown(report)
                    
                with col2:
                    st.markdown("### ⚙️ Actions")
                    # Create a direct download button for the generated report
                    st.download_button(
                        label="📥 Download Markdown Report",
                        data=report,
                        file_name=f"{company.lower().replace(' ', '_')}_report.md",
                        mime="text/markdown"
                    )
            except Exception as e:
                st.error(f"An error occurred during execution: {e}")