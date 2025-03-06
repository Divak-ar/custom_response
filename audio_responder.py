import speech_recognition as sr
import os
import time
import wave
import pyaudio
import re

class AudioResponder:
    def __init__(self, trigger_phrases=None, response_audio_path=None):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.running = True  # Keep the loop running
        
        self.trigger_phrases = trigger_phrases or ["yes or no", "yes r no", "yes no"]
        self.trigger_patterns = [re.compile(r'\b' + re.escape(phrase.lower()) + r'\b') for phrase in self.trigger_phrases]
        self.response_audio_path = response_audio_path or "yes_sir.wav"

        if not os.path.exists(self.response_audio_path):
            print(f"Warning: Response audio file '{self.response_audio_path}' not found.")

        with self.microphone as source:
            print("Adjusting for ambient noise. Please remain silent...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Adjustment complete.")

    def play_audio_response(self):
        try:
            wf = wave.open(self.response_audio_path, 'rb')
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)

            chunk_size = 1024
            data = wf.readframes(chunk_size)

            while data:
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

    def listen(self, duration_mins=1):
        self.running = True
        end_time = time.time() + duration_mins * 60  # Convert hours to seconds

        print(f"Listening for trigger phrases: {', '.join(self.trigger_phrases)}")
        print(f"Listening for {duration_mins * 60} seconds...")

        while self.running and time.time() < end_time:
            with self.microphone as source:
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)

                    try:
                        text = self.recognizer.recognize_google(audio)
                        print(f"Heard: {text}")

                        if self.check_for_trigger(text):
                            print("Trigger phrase detected!")
                            self.play_audio_response()
                            
                            # Continue listening instead of stopping
                            print("Continuing to listen...")

                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        print(f"Could not request results: {e}")

                except sr.WaitTimeoutError:
                    pass  # No speech detected within timeout period

        print("Listener stopped.")

def main():
    duration_mins = float(input("Enter duration in mins: "))

    responder = AudioResponder()
    try:
        responder.listen(duration_mins)
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")

    print("Program terminated.")

if __name__ == "__main__":
    main()
