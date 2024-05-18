# Text to Speech Flask Application

This Flask application converts text to speech using the `edge-tts` command-line tool. It provides a web interface for users to input text and select a voice, and it returns an audio file of the spoken text.

## Table of Contents

- [Text to Speech Flask Application](#text-to-speech-flask-application)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Usage](#usage)
  - [API Endpoints](#api-endpoints)
    - [`POST /say`](#post-say)
      - [Request Body](#request-body)
      - [Example Request](#example-request)
      - [Example Response](#example-response)
  - [Error Handling](#error-handling)
  - [Contributing](#contributing)
  - [License](#license)
  - [Contact](#contact)

## Overview

This project is a simple text-to-speech (TTS) web application built with Flask. It uses `edge-tts` to generate speech from text. The application includes a web interface and a RESTful API endpoint for generating audio files.

## Features

- Web interface for entering text and selecting voice options.
- RESTful API endpoint for programmatic access.
- Asynchronous processing using `asyncio` for non-blocking operations.
- Input validation with Pydantic to ensure correct data types.

## Prerequisites

Before running the application, ensure you have the following installed:

- Python 3.8 or higher
- Flask
- Pydantic
- `edge-tts` (Edge Text to Speech CLI)
- `ffmpeg` (optional, if additional audio processing is needed)

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/shpetimhaxhiu/text-to-speech-albanian.git
    cd text-to-speech-albanian
    ```

2. Create a virtual environment and activate it:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

4. Ensure `edge-tts` is installed and accessible from the command line. Follow the installation instructions from the [edge-tts repository](https://github.com/rany2/edge-tts).

## Usage

1. Run the Flask application:

    ```bash
    python app.py
    ```

2. Open your web browser and navigate to `http://127.0.0.1:5000` to access the web interface.

3. Enter the text you want to convert to speech, select the desired voice, and click "Speak".

## API Endpoints

### `POST /say`

Convert text to speech and return the audio file.

#### Request Body

- `text` (string): The text to convert to speech.
- `voice` (string): The voice to use for speech synthesis.

#### Example Request

```bash
curl -X POST http://127.0.0.1:5000/say \
-H "Content-Type: application/json" \
-d '{
  "text": "Ky është një shembull i një teksti që mund të përdorni për të dëgjuar si zë.",
  "voice": "sq-AL-IlirNeural"
}'
```

#### Example Response

- Success: Returns the generated audio file.
- Error: Returns an error message in JSON format.

## Error Handling

The application includes error handling for the following scenarios:

- Invalid JSON data in the request.
- Validation errors for missing or incorrect data types.
- Errors during the execution of the `edge-tts` command.
- General exceptions during request processing.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any changes or improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

**Shpetim Haxhiu**  
- Email: [shpetim.h@gmail.com](mailto:shpetim.h@gmail.com)
- Phone: +383 49 299-348
- LinkedIn: [Shpetim Haxhiu](https://linkedin.com/in/shpetimhaxhiu)