import streamlit as st
import os
import re
from agent import run_research_agent, SpeechmaticsVoiceService

# Set up page configurations
st.set_page_config(
    page_title="Gemini 3.5 Autonomous Research Agent",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Gemini 3.5 Autonomous Research Agent")
st.subheader("Powered by Google AI Studio & Bright Data")
st.write(
    "Enter a company name below, or **upload a voice recording** from any mobile phone or laptop."
)

# Create layout tabs: Text Input vs Voice Input
tab1, tab2 = st.tabs(["⌨️ Text Query", "🎙️ Voice Query"])

company = ""

with tab1:
    text_input = st.text_input("Enter Company or Startup Name:", placeholder="e.g., Mistral AI, Udio, Cursor")
    if text_input:
        company = text_input

with tab2:
    audio_file = st.file_uploader(
        "Upload a voice recording of the company name (.wav, .mp3, .aac, .m4a):", 
        type=["wav", "mp3", "aac", "m4a"]
    )
    if audio_file is not None:
        file_ext = audio_file.name.split(".")[-1].lower()
        temp_audio_path = f"temp_query.{file_ext}"
        
        with open(temp_audio_path, "wb") as f:
            f.write(audio_file.read())
            
        st.audio(temp_audio_path, format=f"audio/{file_ext}")
        
        # Run Speechmatics transcription
        with st.spinner("Speechmatics is transcribing your voice recording..."):
            try:
                transcribed_query = SpeechmaticsVoiceService.transcribe_audio(temp_audio_path)
                if transcribed_query:
                    company = re.sub(r'[^\w\s]', '', transcribed_query).strip()
                    st.info(f"Transcribed Search Query: **{company}**")
                else:
                    st.error("Speechmatics returned an empty transcript. Please make sure the audio contains clear speech.")
            except Exception as e:
                # Renders the EXACT error details inside your red warning box instantly!
                st.error(f"Speechmatics failed to transcribe. Details: {e}")

# Trigger generate button
if st.button("Generate Research Report", type="primary"):
    if not company:
        st.warning("Please enter a company name or upload an audio file first.")
    else:
        with st.spinner(f"Agent is actively searching and scraping web sources for '{company}'..."):
            try:
                report = run_research_agent(company)
                
                st.success("Research Complete!")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("### 📄 Generated Report")
                    st.markdown(report)
                    
                with col2:
                    st.markdown("### ⚙️ Actions")
                    st.download_button(
                        label="📥 Download Markdown Report",
                        data=report,
                        file_name=f"{company.lower().replace(' ', '_')}_report.md",
                        mime="text/markdown"
                    )
            except Exception as e:
                st.error(f"An error occurred during execution: {e}")