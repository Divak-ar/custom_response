import speech_recognition as sr
import os
import time
import wave
import pyaudio
import re
import threading
from email_sender import EmailSender

class VoiceListener:
    def __init__(self, trigger_phrases=None, response_audio_path=None, trigger_count=3, 
                 email_config=None, phrase_time_limit=5):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self._running = False
        self._thread = None
        
        self.trigger_phrases = trigger_phrases or ["send email"]
        self.trigger_patterns = [re.compile(r'\b' + re.escape(phrase.lower()) + r'\b') for phrase in self.trigger_phrases]
        self.response_audio_path = response_audio_path
        
        self.trigger_count = trigger_count
        self.current_trigger_count = 0
        self.phrase_time_limit = phrase_time_limit  # New parameter for phrase listen duration
        
        self.email_config = email_config
        self.email_sender = EmailSender(**email_config) if email_config else None
        
        # Flag to track if email was sent (for UI feedback)
        self.email_sent = False

        if self.response_audio_path and not os.path.exists(self.response_audio_path):
            print(f"Warning: Response audio file '{self.response_audio_path}' not found.")

    def adjust_for_ambient_noise(self):
        with self.microphone as source:
            print("Adjusting for ambient noise. Please remain silent...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Adjustment complete.")

    def play_audio_response(self):
        if not self.response_audio_path:
            return
            
        try:
            wf = wave.open(self.response_audio_path, 'rb')
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)

            chunk_size = 1024
            data = wf.readframes(chunk_size)

            while data and self._running:
                stream.write(data)
                data = wf.readframes(chunk_size)

            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()

            print("Response played.")
        except Exception as e:
            print(f"Error playing audio response: {e}")

    def check_for_trigger(self, text):
        text = text.lower()
        return any(pattern.search(text) for pattern in self.trigger_patterns)

    def is_running(self):
        return self._running
        
    def get_trigger_count(self):
        return self.current_trigger_count

    def listen_for_triggers(self, duration_mins=60):
        self.adjust_for_ambient_noise()
        
        end_time = time.time() + duration_mins * 60  # Convert minutes to seconds
        self.current_trigger_count = 0  # Reset counter
        self.email_sent = False  # Reset email sent flag

        print(f"Listening for trigger phrases: {', '.join(self.trigger_phrases)}")
        print(f"Listening for {duration_mins} minutes with {self.phrase_time_limit}s phrase time limit")

        detection_period_start = time.time()  # Start time for the detection window
        
        while self._running and time.time() < end_time:
            # Check if we need to reset the count (if the detection period has expired)
            current_time = time.time()
            seconds_in_period = current_time - detection_period_start
            
            # If more than the phrase time window has passed since first detection
            # and we haven't reached the threshold, reset the counter
            if self.current_trigger_count > 0 and seconds_in_period > self.phrase_time_limit:
                print(f"Detection window of {self.phrase_time_limit}s expired. Resetting count from {self.current_trigger_count} to 0")
                self.current_trigger_count = 0
                detection_period_start = current_time  # Reset the period start time
            
            with self.microphone as source:
                try:
                    print(f"Listening for speech...")
                    # Use a shorter phrase_time_limit for better responsiveness
                    audio = self.recognizer.listen(source, phrase_time_limit=min(5, self.phrase_time_limit))
                    print("Audio captured, processing...")

                    try:
                        text = self.recognizer.recognize_google(audio)
                        print(f"Heard: {text}")

                        if self.check_for_trigger(text):
                            print("Trigger phrase detected!")
                            
                            # If this is the first detection in a new period, reset the start time
                            if self.current_trigger_count == 0:
                                detection_period_start = time.time()
                                
                            self.current_trigger_count += 1
                            print(f"Trigger count: {self.current_trigger_count}/{self.trigger_count}")
                            
                            if self.response_audio_path:
                                self.play_audio_response()
                            
                            # Check if we've reached the required count within the time window
                            if self.current_trigger_count >= self.trigger_count:
                                print(f"Trigger threshold reached! Sending email immediately...")
                                self.send_email()
                                self.current_trigger_count = 0  # Reset counter after sending
                                detection_period_start = time.time()  # Reset detection window

                    except sr.UnknownValueError:
                        print("Could not understand audio")
                    except sr.RequestError as e:
                        print(f"Could not request results: {e}")

                except Exception as e:
                    print(f"Error during listening: {e}")
                    # Continue immediately to next iteration
                    continue

        print("Listening stopped.")
        self._running = False

    def send_email(self):
        if self.email_sender:
            try:
                result = self.email_sender.send_email(
                    self.email_config.get("subject", "Voice Triggered Email"),
                    self.email_config.get("body", "This is an automated email."),
                    self.email_config.get("to_emails", []),
                    self.email_config.get("cc_emails", []),
                    html_content=self.email_config.get("html_content", False),
                    attachment_path=self.email_config.get("attachment_path")
                )
                if result:
                    print("Email sent successfully!")
                    self.email_sent = True  # Set flag for UI feedback
                else:
                    print("Failed to send email.")
            except Exception as e:
                print(f"Error sending email: {e}")
        else:
            print("Email sender not configured.")

    def start_listening(self, duration_mins=60):
        if self._running:
            return False
            
        self._running = True
        self._thread = threading.Thread(target=self.listen_for_triggers, args=(duration_mins,))
        self._thread.daemon = True
        self._thread.start()
        return True

    def stop_listening(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        return True