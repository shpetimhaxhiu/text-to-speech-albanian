# tts/__init__.py

# This file initializes the Text To Speech functionality

# You can include code here to convert the text to speech using a specific library or API
# For example, you can use the pyttsx3 library to convert text to speech

# Import the necessary libraries
import pyttsx3

# Initialize the Text To Speech engine
engine = pyttsx3.init()

# Define a function to convert text to speech
def convert_text_to_speech(text, lang, gender):
    # Set the language and gender of the voice
    engine.setProperty('voice', f'{lang}+{gender}')

    # Convert the text to speech
    engine.say(text)
    engine.runAndWait()