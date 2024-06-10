from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from tempfile import NamedTemporaryFile
from pydantic import BaseModel, ValidationError
from typing import List
import asyncio
import subprocess
import srt
import datetime
import os

app = Flask(__name__)


# Define a Pydantic model for the request body
class TTSSchema(BaseModel):
    text: str
    voice: str


# Define a Pydantic model for the request body
class TTSSRTSchema(BaseModel):
    voice: str


@app.route("/")
def index():
    return render_template("index.html")


async def run_edge_tts(text, voice, output_file):
    process = await asyncio.create_subprocess_exec(
        "edge-tts",
        "--text",
        text,
        "-v",
        voice,
        "--write-media",
        output_file,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return process.returncode, stdout, stderr


# Function to parse the SRT file
def parse_srt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        srt_content = file.read()
    subtitles = list(srt.parse(srt_content))
    return subtitles


# Function to generate individual audio clips
async def generate_audio_clips(subtitles, voice, output_dir):
    audio_clips = []
    for i, subtitle in enumerate(subtitles):
        text = subtitle.content
        output_file = os.path.join(output_dir, f"clip_{i}.mp3")
        returncode, stdout, stderr = await run_edge_tts(text, voice, output_file)
        if returncode != 0:
            raise Exception(f"Error generating audio clip: {stderr.decode()}")
        audio_clips.append((output_file, subtitle.start.total_seconds()))
    return audio_clips


# Function to merge audio clips
def merge_audio_clips(audio_clips, output_file):
    input_files = [f"file '{clip[0]}'" for clip in audio_clips]
    timestamps = [f"{clip[1]}" for clip in audio_clips]
    input_list_path = os.path.join(os.path.dirname(output_file), "input_list.txt")
    with open(input_list_path, "w", encoding="utf-8") as file:
        file.write("\n".join(input_files))

    merge_command = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", input_list_path, "-c", "copy", output_file]
    subprocess.run(merge_command, check=True)

    os.remove(input_list_path)  # Clean up the input list file


@app.route("/srt", methods=["GET", "POST"])
async def srt_form_post():
    if request.method == "GET":
        return render_template("srt.html")
    elif request.method == "POST":
        try:
            if "file" not in request.files:
                return jsonify({"error": "No file part"}), 400
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "No selected file"}), 400

            filename = secure_filename(file.filename)
            temp_file = NamedTemporaryFile(delete=False, suffix=".srt")
            file.save(temp_file.name)
            temp_file.close()

            # Validate request data with Pydantic
            try:
                voice = request.form["voice"]
                tts_data = TTSSRTSchema(voice=voice)
            except ValidationError as e:
                return jsonify({"error": e.errors()}), 400

            subtitles = parse_srt(temp_file.name)
            output_dir = os.path.dirname(temp_file.name)
            audio_clips = await generate_audio_clips(subtitles, tts_data.voice, output_dir)

            output_audio_file = os.path.join(output_dir, "final_output.mp3")
            merge_audio_clips(audio_clips, output_audio_file)

            return send_file(output_audio_file, mimetype="audio/mpeg", as_attachment=False, download_name="output.mp3")

        except Exception as e:
            return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
        finally:
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
            for clip, _ in audio_clips:
                if os.path.exists(clip):
                    os.remove(clip)


@app.route("/say", methods=["POST"])
async def say():
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Invalid JSON data"}), 400

        # Validate request data with Pydantic
        try:
            tts_data = TTSSchema(**data)
        except ValidationError as e:
            return jsonify({"error": e.errors()}), 400

        rand_audio_file = NamedTemporaryFile(delete=False, suffix=".mp3")
        try:
            returncode, stdout, stderr = await run_edge_tts(tts_data.text, tts_data.voice, rand_audio_file.name)

            if returncode != 0:
                return (
                    jsonify(
                        {
                            "error": f"Command 'edge-tts' returned non-zero exit status {returncode}. Command output: {stderr.decode()}"
                        }
                    ),
                    500,
                )

            return send_file(
                rand_audio_file.name, mimetype="audio/mpeg", as_attachment=False, download_name="output.mp3"
            )
        except Exception as e:
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500
        finally:
            rand_audio_file.close()
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
