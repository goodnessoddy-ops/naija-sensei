"""One-time check: which Gemma 4 models can my API key actually use?"""
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

print("Available Gemma models:\n")
for model in client.models.list():
    name = model.name
    if "gemma" in name.lower():
        print(f"  {name}")