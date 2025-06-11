import wave
import numpy as np
import os

def create_notification_sound(filename="data/audio/notification.wav"):
    """Create a default notification sound file"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Audio parameters
    duration = 0.5  # seconds
    sample_rate = 44100  # Hz
    frequency = 800  # Hz
    
    # Generate a simple beep
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(2 * np.pi * frequency * t) * 0.5
    
    # Add a fade in/out
    fade_samples = int(sample_rate * 0.05)
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    
    tone[:fade_samples] *= fade_in
    tone[-fade_samples:] *= fade_out
    
    # Convert to 16-bit PCM
    tone = (tone * 32767).astype(np.int16)
    
    # Save as a WAV file
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(tone.tobytes())
    
    return filename

if __name__ == "__main__":
    filename = create_notification_sound()
    print(f"Created notification sound: {filename}")