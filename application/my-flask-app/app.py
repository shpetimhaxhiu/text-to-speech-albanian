from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from tempfile import NamedTemporaryFile
from pydantic import BaseModel, ValidationError
import asyncio
import subprocess

app = Flask(__name__)


# Define a Pydantic model for the request body
class TTSSchema(BaseModel):
    text: str
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
