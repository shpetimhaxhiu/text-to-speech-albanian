from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from tempfile import NamedTemporaryFile
from pydantic import BaseModel
import asyncio
import subprocess

app = Flask(__name__)


# Define a Pydantic model for the request body
class TTSSchema(BaseModel):
    text: str = "Ky eshte nje tekst shembull per te konfirmuar qe programi punon si duhet."
    lang: str = "sq-AL"
    gender: str = "sq-AL-IlirNeural"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/say", methods=["POST"])
async def say():
    """
    POST /say
    This endpoint generates an audio file from the provided text and voice.
    ---
    parameters:
      - name: text
      in: body
      type: string
      required: true
      description: The text to convert to speech.
      - name: voice
      in: body
      type: string
      required: true
      description: The voice to use for the speech.
    responses:
      200:
      description: The audio file was successfully generated.
      schema:
        type: object
        properties:
        audio:
          type: string
          description: The name of the audio file.
      400:
      description: The request data was invalid.
      500:
      description: An error occurred while generating the audio file.
    """
    # Get JSON data from request
    data = request.get_json(force=True)

    # Validate request data
    if not data or not all(key in data for key in ("text", "voice")):
        return jsonify({"error": "Both 'text' and 'voice' parameters are required"}), 400

    # Create a temporary file for the audio
    rand_audio_file = NamedTemporaryFile(delete=False, suffix=".mp3")

    # Run the edge-tts command asynchronously
    try:
        process = await asyncio.create_subprocess_exec(
            "edge-tts",
            "--text",
            data["text"],
            "-v",
            data["voice"],
            "--write-media",
            rand_audio_file.name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Wait for the command to finish
        stdout, stderr = await process.communicate()

        # Check the command's exit status
        if process.returncode != 0:
            return (
                jsonify(
                    {
                        "error": f"Command 'edge-tts' returned non-zero exit status {process.returncode}. Command output: {stderr.decode()}"
                    }
                ),
                500,
            )

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    # Return the name of the audio file
    return jsonify({"audio": rand_audio_file.name}), 200


if __name__ == "__main__":
    app.run(debug=True)
