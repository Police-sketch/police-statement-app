import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Smart Police Statement Intake Assistant", layout="centered")

st.title("🛡️ Automated Police Statement Intake Assistant")
st.markdown("This system conducts a dynamic, multi-turn interview with citizens (via voice or text) and generates a formal police statement.")

# Sidebar for API Key input
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter OpenAI API Key", type="password")

if not api_key:
    st.warning("⚠️ Please enter your OpenAI API key in the sidebar to enable live multi-turn AI interviews and voice transcription.")
    st.stop()

client = OpenAI(api_key=api_key)

# Initialize multi-turn chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": (
                "You are a professional, thorough, and empathetic police investigator conducting an intake interview. "
                "Your job is to gather all necessary facts (Who, What, When, Where, Why, How, suspect/vehicle descriptions, license plates, evidence). "
                "CRITICAL INSTRUCTIONS: Ask ONLY ONE or TWO targeted follow-up questions at a time based on what the user just said, just like a real-life police officer. "
                "Do not jump straight to conclusions or wrap up too early. Keep probing until you have a complete investigative picture."
            )
        }
    ]

# Display conversation history (excluding system prompt)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 1. VOICE INPUT (Native Streamlit Audio Recorder)
audio_file = st.audio_input("🎙️ Or click to record your voice response")

user_input = None

if audio_file is not None:
    with st.spinner("Transcribing your voice..."):
        try:
            # Transcribe audio using OpenAI Whisper model
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=("audio_statement.wav", audio_file.getvalue())
            )
            user_input = transcript.text
            st.success(f"Transcribed Voice: {user_input}")
        except Exception as e:
            st.error(f"Transcription error: {e}")

# 2. TEXT INPUT (Fallback or primary typing box)
text_input = st.chat_input("Type your response here...")

# Determine if input came from voice or text
final_prompt = user_input if user_input else text_input

if final_prompt:
    # Append user response to history
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    with st.chat_message("user"):
        st.markdown(final_prompt)
        
    # Generate dynamic next question from AI officer
    with st.spinner("Police Officer is reviewing your statement..."):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages
        )
        ai_reply = response.choices[0].message.content
        
    # Append assistant response to history and rerun to update chat
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
    with st.chat_message("assistant"):
        st.markdown(ai_reply)
    st.rerun()

st.divider()

# 3. CONCLUDE & GENERATE REPORT BUTTON
if st.button("🏁 Conclude Interview & Generate Formal Police Statement"):
    with st.spinner("Compiling formal police report from full conversation transcript..."):
        summary_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages + [
                {
                    "role": "user", 
                    "content": "Based on our entire interview transcript above, generate a formal, legally structured Police Statement Report including Date/Time, Location, Incident Narrative Summary, Suspect/Vehicle descriptions, and a formal witness signature declaration block."
                }
            ]
        )
        formal_report = summary_response.choices[0].message.content
        
        st.subheader("📋 Official Police Statement Report")
        st.markdown(formal_report)
        st.download_button("📥 Download Official Report (.txt)", formal_report, file_name="Police_Statement_Report.txt")
