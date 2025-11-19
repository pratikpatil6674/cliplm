from openai import OpenAI
import base64
import os

# --- Configuration ---
# 1. Use your Gemini API Key.
# It's best practice to load this from an environment variable (GEMINI_API_KEY)
GEMINI_API_KEY = "AIzaSyCggmUdIyDlDJG0tz2rEObph5Z_lQlH4nQ" #os.getenv("GEMINI_API_KEY") 

# 2. Set the custom base_url for the Gemini API's OpenAI compatibility layer.
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
MODEL_NAME = "gemini-2.5-flash" # Use a compatible Gemini model

IMAGE_PATH = "document.png" # ⬅️ Replace with your image file name
PROMPT = "Extract all text from this image and provide the clean text output and its EN translation."

# Initialize the OpenAI client with the Gemini specific settings
client = OpenAI(
    api_key=GEMINI_API_KEY, 
    base_url=GEMINI_BASE_URL
)

# --- Image Handling for Multimodal Request ---
# Read and base64-encode the image data
try:
    with open(IMAGE_PATH, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
except FileNotFoundError:
    print(f"Error: Image file not found at '{IMAGE_PATH}'")
    exit()

# Construct the messages list for multimodal input
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": PROMPT},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_data}"
                    # Adjust mime type (image/png) if your file is a different format like image/jpeg
                },
            },
        ],
    }
]

# --- Call the Gemini API via OpenAI Client ---
response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=messages
)

# --- Output the Result ---
print("--- Extracted Text from Image ---")
print(response.choices[0].message.content)
print("---------------------------------")