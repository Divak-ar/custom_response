import streamlit as st
import os
import time
import uuid
import datetime
import numpy as np
import wave
from voice_listener import VoiceListener
from email_sender import EmailSender
from audio_handler import save_audio_file
from config_handler import ConfigHandler

# Create necessary directories
os.makedirs("data/audio/notification", exist_ok=True)
os.makedirs("data/audio/response", exist_ok=True)

# Set page configuration for better mobile experience
st.set_page_config(
    page_title="Voice Email Trigger",
    page_icon="📧",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better mobile experience and styling
st.markdown("""
<style>
    /* General styling improvements */
    .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
    }
    
    h1, h2, h3 {
        color: #1E88E5;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        height: 3rem;
        font-size: 1.2rem;
        background-color: #1E88E5;
        color: white;
        border-radius: 6px;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #1565C0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Form input styling - CHANGED TEXT COLOR TO LIGHT GREEN */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        font-size: 1rem;
        padding: 0.5rem;
        border-radius: 6px;
        border: 1px solid #E0E0E0;
        color: #4CAF50 !important;  /* Light green text color */
    }
    
    /* Text area styling - CHANGED TEXT COLOR TO LIGHT GREEN */
    .stTextArea textarea {
        color: #4CAF50 !important;  /* Light green text color */
    }
    
    /* Other input elements - CHANGED TEXT COLOR TO LIGHT GREEN */
    .stSelectbox select, .stMultiselect select {
        color: #4CAF50 !important;  /* Light green text color */
    }
    
    /* Form text elements - CHANGED TEXT COLOR TO LIGHT GREEN */
    input, select, textarea {
        color: #4CAF50 !important;  /* Light green text color */
    }
    
    /* Cards for recipient display */
    .email-card {
        background-color: #f8f9fa;
        border-radius: 6px;
        padding: 10px;
        margin: 5px 0;
        border-left: 4px solid #1E88E5;
        color: #000000;  /* Black text for better visibility */
        font-weight: 500;
    }
    
    /* Mobile-friendly adjustments */
    @media (max-width: 640px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1rem;
        }
        .stButton>button {
            height: 2.5rem;
            font-size: 1rem;
        }
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background-color: #1E88E5;
    }
    
    /* Info boxes */
    .info-box {
        background-color: #E3F2FD;
        border-radius: 6px;
        padding: 10px 15px;
        margin: 10px 0;
        border-left: 4px solid #1E88E5;
        color: #0D47A1;
    }
    
    /* Success box */
    .success-box {
        background-color: #E8F5E9;
        border-radius: 6px;
        padding: 10px 15px;
        margin: 10px 0;
        border-left: 4px solid #43A047;
        color: #1B5E20;
    }
    
    /* Radio buttons and checkboxes */
    .st-cc {
        color: #4CAF50;  /* Light green */
    }
    
    /* Dividers */
    hr {
        margin: 2rem 0;
        border-color: #E0E0E0;
    }
    
    /* Fix text color on blue buttons */
    button p {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Load configuration
config = ConfigHandler.get_config()

# Application state
if 'is_listening' not in st.session_state:
    st.session_state.is_listening = False
if 'listener' not in st.session_state:
    st.session_state.listener = None
if 'recipients' not in st.session_state:
    st.session_state.recipients = []
if 'cc_recipients' not in st.session_state:
    st.session_state.cc_recipients = []
if 'new_recipient' not in st.session_state:
    st.session_state.new_recipient = ""
if 'new_cc' not in st.session_state:
    st.session_state.new_cc = ""
if 'notification_choice' not in st.session_state:
    st.session_state.notification_choice = "default"

def add_recipient():
    if st.session_state.new_recipient and "@" in st.session_state.new_recipient:
        if st.session_state.new_recipient not in st.session_state.recipients:
            st.session_state.recipients.append(st.session_state.new_recipient)
        
def add_cc_recipient():
    if st.session_state.new_cc and "@" in st.session_state.new_cc:
        if st.session_state.new_cc not in st.session_state.cc_recipients:
            st.session_state.cc_recipients.append(st.session_state.new_cc)

def remove_recipient(email):
    st.session_state.recipients.remove(email)

def remove_cc_recipient(email):
    st.session_state.cc_recipients.remove(email)

def create_beautiful_email(subject, trigger_phrase, trigger_count, has_audio=False):
    """Create a professionally formatted HTML email"""
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Audio instructions section if audio is included
    audio_section = ""
    if has_audio:
        audio_section = """
        <div class="detail audio-section">
            <p><strong>📢 Audio Notification:</strong> A sound notification is attached to this email.</p>
            <p>Check the email attachments to download and play the notification sound.</p>
        </div>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333333;
                max-width: 600px;
                margin: 0 auto;
            }}
            .header {{
                background-color: #1E88E5;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                padding: 20px;
                border: 1px solid #E0E0E0;
                border-top: none;
                border-radius: 0 0 8px 8px;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 12px;
                color: #757575;
                text-align: center;
            }}
            .detail {{
                background-color: #f5f5f5;
                padding: 10px 15px;
                margin: 10px 0;
                border-radius: 5px;
                border-left: 4px solid #1E88E5;
            }}
            .audio-section {{
                border-left-color: #FF9800;
                background-color: #FFF8E1;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>{subject}</h2>
        </div>
        <div class="content">
            <p>This is an automated email generated by the Voice Email Trigger system.</p>
            
            <div class="detail">
                <p><strong>Triggered on:</strong> {current_time}</p>
                <p><strong>Trigger phrase:</strong> "{trigger_phrase}"</p>
                <p><strong>Required detections:</strong> {trigger_count}</p>
            </div>
            
            {audio_section}
            
            <p>If you did not expect this email or believe it was sent in error, please disregard.</p>
        </div>
        <div class="footer">
            <p>This is an automated message from the Voice Email Trigger application.</p>
            <p>© {datetime.datetime.now().year} Voice Email Trigger</p>
        </div>
    </body>
    </html>
    """
    
    return html_content

def main():
    # Simple tab navigation
    tab1, tab2 = st.tabs(["📧 Voice Email Trigger", "ℹ️ Instructions"])
    
    with tab1:
        st.title("🎙️ Voice Email Trigger")
        
        # Show a warning if no config is found
        if not config:
            st.error("No configuration found. Please check your configuration files.")
            st.stop()
        
        # Recipients section outside the form for better interaction
        st.subheader("👥 Email Recipients")
        
        # Update the recipient form section
        with st.form("add_recipient_form", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text_input(
                    "Recipient email",
                    key="new_recipient",
                    placeholder="email@example.com"
                )
            with col2:
                if st.form_submit_button("Add"):
                    add_recipient()
        
        # Update the CC recipient form section
        with st.form("add_cc_form", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text_input(
                    "CC recipient",
                    key="new_cc",
                    placeholder="cc@example.com"
                )
            with col2:
                if st.form_submit_button("Add CC"):
                    add_cc_recipient()
        
        # Display recipients
        if st.session_state.recipients:
            for email in st.session_state.recipients:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"""<div class="email-card">{email}</div>""", unsafe_allow_html=True)
                with col2:
                    if st.button("❌", key=f"del_{email}", help="Remove recipient"):
                        remove_recipient(email)
                        st.experimental_rerun()
        
        if st.session_state.cc_recipients:
            st.markdown("##### CC Recipients")
            for email in st.session_state.cc_recipients:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"""<div class="email-card">{email}</div>""", unsafe_allow_html=True)
                with col2:
                    if st.button("❌", key=f"delcc_{email}", help="Remove CC recipient"):
                        remove_cc_recipient(email)
                        st.experimental_rerun()
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Add audio settings section
        st.subheader("🔊 Audio Settings")
        
        # Custom notification sound (to be sent with email)
        st.markdown("##### Email Notification Sound")
        st.markdown("This sound will be attached to the email and can be played by the recipient.")
        notification_file = st.file_uploader(
            "Upload notification sound",
            type=["wav"],
            key="notification_file_upload",  # <-- Changed key here
            help="This sound will be attached to the email for the recipient"
        )
        notification_path = None
        if notification_file:
            notification_path = save_audio_file(notification_file, "data/audio/notification")
            st.audio(notification_file, format="audio/wav")
            st.success("Notification sound uploaded successfully!")

        # Response sound (played locally when triggered)
        st.markdown("##### Local Response Sound")
        st.markdown("This sound will play on your device when the trigger is detected.")
        response_file = st.file_uploader(
            "Upload response sound",
            type=["wav"],
            key="response_file_upload",  # <-- Changed key here
            help="This sound will play on your device when triggered"
        )
        response_path = None
        if response_file:
            response_path = save_audio_file(response_file, "data/audio/response")
            st.audio(response_file, format="audio/wav")
            st.success("Response sound uploaded successfully!")
      
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Main form
        with st.form("trigger_form"):
            # Voice trigger settings
            st.subheader("✨ Voice Trigger Settings")
            
            trigger_phrase = st.text_input(
                "Trigger phrase",
                placeholder="e.g., send email now, help needed, emergency alert",
                help="The system will listen for this phrase"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                trigger_count = st.number_input(
                    "Trigger count",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="Number of detections needed"
                )
            
            with col2:
                phrase_listen_duration = st.number_input(
                    "Phrase listen window (seconds)",
                    min_value=3,
                    max_value=30,
                    value=20,  # Set default to 20 seconds as requested
                    help="How long to listen for each phrase attempt"
                )
            
            total_duration = st.slider(
                "Total app runtime (minutes)",
                min_value=1,
                max_value=120,
                value=30,  # Set default to 30 minutes as requested
                help="Total time the app will run listening for trigger phrases"
            )
            
            # Email settings
            st.subheader("📨 Email Content")
            
            email_subject = st.text_input(
                "Subject",
                placeholder="Voice Triggered Alert",
                help="The subject line of your email"
            )
            
            # Submit button
            submitted = st.form_submit_button("▶️ Start Listening")
            
            if submitted and not st.session_state.is_listening:
                if not trigger_phrase:
                    st.error("Please enter a trigger phrase.")
                    st.stop()
                
                if not st.session_state.recipients:
                    st.error("Please add at least one recipient.")
                    st.stop()
                
                if not email_subject:
                    st.error("Please enter an email subject.")
                    st.stop()
                
                # Prepare email content
                email_html = create_beautiful_email(
                    email_subject,
                    trigger_phrase,
                    trigger_count,
                    has_audio=notification_path is not None
                )
                
                # Prepare email config
                email_config = {
                    "sender": config["email_config"]["sender_email"],
                    "password": config["email_config"]["password"],
                    "server": "Gmail",
                    "smtp_server": config["email_config"]["smtp_server"],
                    "smtp_port": config["email_config"]["port"],
                    "subject": email_subject,
                    "body": email_html,
                    "html_content": True,
                    "to_emails": st.session_state.recipients,
                    "cc_emails": st.session_state.cc_recipients,
                    "attachment_path": notification_path  # Add the audio attachment
                }
                
                # Set up voice listener
                st.session_state.is_listening = True
                listener = VoiceListener(
                    trigger_phrases=[trigger_phrase],
                    response_audio_path=response_path,
                    trigger_count=trigger_count,
                    email_config=email_config,
                    phrase_time_limit=phrase_listen_duration
                )
                st.session_state.listener = listener
        
        # Display listening status and controls outside the form
        if st.session_state.is_listening:
            st.markdown("""<div class="info-box">🎤 <b>Listening for trigger phrase...</b></div>""", unsafe_allow_html=True)
            
            # Display progress
            progress_container = st.empty()
            status_text = st.empty()
            count_text = st.empty()
            
            # Stop button
            if st.button("⏹️ Stop Listening", key="stop_listening"):
                if st.session_state.listener:
                    st.session_state.listener.stop_listening()
                st.session_state.is_listening = False
                st.success("Listening stopped.")
                st.experimental_rerun()
            
            # Start the listener
            listener = st.session_state.listener
            listener.start_listening(total_duration)  # Total duration in minutes
            
            # Update progress
            start_time = time.time()
            end_time = start_time + (total_duration * 60)
            
            while time.time() < end_time and listener.is_running():
                elapsed = time.time() - start_time
                progress = min(elapsed / (total_duration * 60), 1.0)
                
                remaining_mins = int((total_duration * 60 - elapsed) / 60)
                remaining_secs = int((total_duration * 60 - elapsed) % 60)
                
                progress_container.progress(progress)
                status_text.markdown(f"""<div class="info-box">⏱️ Remaining: {remaining_mins} min {remaining_secs} sec</div>""", unsafe_allow_html=True)
                
                count = listener.get_trigger_count()
                count_text.markdown(f"""<div class="info-box">🔊 Detected: {count}/{listener.trigger_count}</div>""", unsafe_allow_html=True)
                
                # If email was sent, show success message
                if hasattr(listener, 'email_sent') and listener.email_sent:
                    recipients_list = ", ".join(st.session_state.recipients)
                    st.markdown(f"""<div class="success-box">✅ <b>Email sent successfully!</b></div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div class="info-box">📧 <b>Sent to:</b> {recipients_list}</div>""", unsafe_allow_html=True)
                    
                    if st.session_state.cc_recipients:
                        cc_list = ", ".join(st.session_state.cc_recipients)
                        st.markdown(f"""<div class="info-box">📋 <b>CC:</b> {cc_list}</div>""", unsafe_allow_html=True)
                    
                    listener.email_sent = False  # Reset flag
                
                time.sleep(0.1)
            
            # After listening completes
            if not listener.is_running():
                st.session_state.is_listening = False
                status_text.text("Listening complete.")
    
    with tab2:
        st.title("Instructions")
        
        st.markdown("""
        ## 📝 How to Use This App

        ### Getting Started:

        1. **Add Email Recipients:**
           - Enter email addresses for your recipients
           - Add CC recipients if needed
           - You must add at least one recipient

        2. **Audio Settings:**
           - Upload an email notification sound that will be attached to the email
           - Upload a local response sound that will play on your device when triggered

        3. **Set Your Trigger Phrase:**
           - Choose a distinct word or phrase that will trigger the email
           - Example: "send help email" or "emergency alert"

        4. **Configure Trigger Settings:**
           - **Trigger Count**: How many times your phrase needs to be detected
           - **Phrase Listen Window**: How long (in seconds) the app listens for each phrase attempt
           - **Total Runtime**: How long the app will run in total

        5. **Email Configuration:**
           - Enter a clear subject line for your email

        6. **Start Listening:**
           - Click the "Start Listening" button
           - Speak your trigger phrase the required number of times
           - The app will automatically send the email when triggered

        ### Voice Recognition Tips:

        - Speak clearly at a normal pace
        - Keep the microphone close
        - Minimize background noise
        - Use distinctive phrases that aren't common in conversation
        - Test different phrases if recognition is inconsistent

        ### Important Notes:

        - Keep the app tab open while listening
        - The app will stop listening after the set runtime
        - You can manually stop listening at any time
        - Email will be sent automatically when the trigger count is reached
        """)

if __name__ == "__main__":
    main()