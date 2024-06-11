from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, ValidationError
from tempfile import NamedTemporaryFile
import subprocess
import requests
import srt
import os
from fastapi.templating import Jinja2Templates
from pathlib import Path
import openai

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize OpenAI client
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))


# Define a Pydantic model for the request body
class TTSSchema(BaseModel):
    text: str
    voice: str


# Define a Pydantic model for the request body
class TTSSRTSchema(BaseModel):
    voice: str


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def run_edge_tts(text, voice, output_file):
    process = subprocess.run(
        ["edge-tts", "--text", text, "-v", voice, "--write-media", output_file],
        capture_output=True,
    )
    return process.returncode, process.stdout, process.stderr


# Function to parse the SRT file
def parse_srt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        srt_content = file.read()
    subtitles = list(srt.parse(srt_content))
    return subtitles


# Function to generate individual audio clips
def generate_audio_clips(subtitles, voice, output_dir):
    audio_clips = []
    for i, subtitle in enumerate(subtitles):
        text = subtitle.content
        output_file = os.path.join(output_dir, f"clip_{i}.mp3")
        returncode, stdout, stderr = run_edge_tts(text, voice, output_file)
        if returncode != 0:
            raise Exception(f"Error generating audio clip: {stderr.decode()}")
        audio_clips.append((output_file, subtitle.start.total_seconds()))
    return audio_clips


def generate_speech(script, voice: str = "onyx"):
    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        },
        json={
            "model": "tts-1-1106",
            "input": script,
            "voice": voice,
        },
    )

    audio = b""
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        audio += chunk

    return audio


# Function to generate individual audio clips using OpenAI
async def generate_audio_clips_openai(subtitles, voice, output_dir):
    audio_clips = []
    for i, subtitle in enumerate(subtitles):
        text = subtitle.content
        output_file = os.path.join(output_dir, f"clip_{i}.mp3")

        response = generate_speech(text, voice)

        with open(output_file, "wb") as f:
            f.write(response)

        audio_clips.append((output_file, subtitle.start.total_seconds()))
    return audio_clips


# Function to merge audio clips
def merge_audio_clips(audio_clips, output_file):
    input_files = [f"file '{clip[0]}'" for clip in audio_clips]
    input_list_path = os.path.join(os.path.dirname(output_file), "input_list.txt")
    with open(input_list_path, "w", encoding="utf-8") as file:
        file.write("\n".join(input_files))

    merge_command = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", input_list_path, "-c", "copy", output_file]
    process = subprocess.run(merge_command, capture_output=True)
    print("FFmpeg stdout:", process.stdout.decode())
    print("FFmpeg stderr:", process.stderr.decode())

    if process.returncode != 0:
        raise Exception(f"Error merging audio clips: {process.stderr.decode()}")

    os.remove(input_list_path)  # Clean up the input list file


@app.get("/srt", response_class=HTMLResponse)
async def srt_form(request: Request):
    return templates.TemplateResponse("srt.html", {"request": request})


@app.post("/srt", response_class=HTMLResponse)
async def srt_form_post(request: Request, file: UploadFile = File(...), voice: str = Form(...)):
    try:
        filename = file.filename
        temp_file = NamedTemporaryFile(delete=False, suffix=".srt")
        with open(temp_file.name, "wb") as out_file:
            out_file.write(await file.read())
        temp_file.close()

        # Validate request data with Pydantic
        try:
            tts_data = TTSSRTSchema(voice=voice)
        except ValidationError as e:
            return templates.TemplateResponse("srt.html", {"request": request, "error": e.errors()})

        subtitles = parse_srt(temp_file.name)
        output_dir = os.path.dirname(temp_file.name)
        audio_clips = generate_audio_clips(subtitles, tts_data.voice, output_dir)

        output_audio_file = os.path.join(output_dir, "final_output.mp3")
        merge_audio_clips(audio_clips, output_audio_file)

        return FileResponse(output_audio_file, media_type="audio/mpeg", filename="output.mp3")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        for clip, _ in audio_clips:
            if os.path.exists(clip):
                os.remove(clip)


@app.get("/openai-srt", response_class=HTMLResponse)
async def srt_form_openai(request: Request):
    return templates.TemplateResponse("srt-openai.html", {"request": request})

@app.post("/openai-srt", response_class=HTMLResponse)
async def srt_form_post_openai(request: Request, file: UploadFile = File(...), voice: str = Form(...)):
    try:
        filename = file.filename
        temp_file = NamedTemporaryFile(delete=False, suffix=".srt")
        with open(temp_file.name, "wb") as out_file:
            out_file.write(await file.read())
        temp_file.close()

        # Validate request data with Pydantic
        try:
            tts_data = TTSSRTSchema(voice=voice)
        except ValidationError as e:
            return templates.TemplateResponse("srt.html", {"request": request, "error": e.errors()})

        subtitles = parse_srt(temp_file.name)
        output_dir = os.path.dirname(temp_file.name)
        audio_clips = await generate_audio_clips_openai(subtitles, tts_data.voice, output_dir)

        output_audio_file = os.path.join(output_dir, "final_output.mp3")
        merge_audio_clips(audio_clips, output_audio_file)

        return FileResponse(output_audio_file, media_type="audio/mpeg", filename="output.mp3")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        for clip, _ in audio_clips:
            if os.path.exists(clip):
                os.remove(clip)


@app.post("/say")
async def say(tts_data: TTSSchema):
    try:
        rand_audio_file = NamedTemporaryFile(delete=False, suffix=".mp3")
        try:
            returncode, stdout, stderr = run_edge_tts(tts_data.text, tts_data.voice, rand_audio_file.name)

            if returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Command 'edge-tts' returned non-zero exit status {returncode}. Command output: {stderr.decode()}",
                )

            return FileResponse(rand_audio_file.name, media_type="audio/mpeg", filename="output.mp3")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
        finally:
            rand_audio_file.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.post("/say_with_openai", response_class=FileResponse)
async def say_with_openai(tts_data: TTSSchema):
    try:
        rand_audio_file = NamedTemporaryFile(delete=False, suffix=".mp3")
        try:
            response = generate_speech(tts_data.text, tts_data.voice)

            with open(rand_audio_file.name, "wb") as f:
                f.write(response)

            return FileResponse(rand_audio_file.name, media_type="audio/mpeg", filename="output.mp3")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
        finally:
            rand_audio_file.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
