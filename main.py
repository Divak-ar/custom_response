from fastapi import FastAPI, WebSocket, UploadFile, Form
import os
import asyncio
import speech_recognition as sr
from pydub import AudioSegment
from fastapi.responses import FileResponse

app = FastAPI()
audio_folder = "audio_files"

# Ensure audio directory exists
os.makedirs(audio_folder, exist_ok=True)

@app.post("/upload/")
async def upload_audio(file: UploadFile, trigger_phrase: str = Form(...), duration: int = Form(...)):
    """API to upload audio response and set trigger phrases"""
    file_path = os.path.join(audio_folder, file.filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return {"message": "File uploaded successfully", "file_path": file_path, "trigger_phrase": trigger_phrase, "duration": duration}

@app.websocket("/listen/")
async def listen_audio(websocket: WebSocket):
    """WebSocket connection for real-time speech recognition"""
    await websocket.accept()
    
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)

    while True:
        with mic as source:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        try:
            text = recognizer.recognize_google(audio)
            await websocket.send_text(text)
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            await websocket.send_text(f"Error: {e}")

@app.get("/play/{filename}")
async def play_audio(filename: str):
    """API to play stored audio responses"""
    file_path = os.path.join(audio_folder, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/wav")
    return {"error": "File not found"}
