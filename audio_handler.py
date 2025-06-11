import os
import tempfile
import uuid
from pydub import AudioSegment

def save_audio_file(uploaded_file, directory="data/audio"):
    """Save an uploaded audio file to the specified directory"""
    os.makedirs(directory, exist_ok=True)
    
    # Generate a unique filename if none provided
    if not uploaded_file.name:
        file_extension = ".wav"
        filename = f"{uuid.uuid4()}{file_extension}"
    else:
        # Make sure filename is unique
        base, ext = os.path.splitext(uploaded_file.name)
        filename = f"{base}_{uuid.uuid4()}{ext}"
    
    # Full path to save the file
    file_path = os.path.join(directory, filename)
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def convert_audio_to_wav(file_path):
    """Convert various audio formats to WAV format"""
    try:
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # If already WAV, return the path
        if ext == '.wav':
            return file_path
            
        # Load audio file
        audio = AudioSegment.from_file(file_path)
        
        # Create output path
        output_path = os.path.splitext(file_path)[0] + ".wav"
        
        # Export as WAV
        audio.export(output_path, format="wav")
        
        # Remove original file if conversion succeeded
        if os.path.exists(output_path):
            os.remove(file_path)
            
        return output_path
    except Exception as e:
        print(f"Error converting audio: {e}")
        return file_path