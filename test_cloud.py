"""Quick test: can we reach Gemma 4 26B in the cloud and get a Pidgin reply?"""
import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

MODEL = "gemma-4-26b-a4b-it"

print(f"Asking {MODEL}...")
start = time.time()

response = client.models.generate_content(
    model=MODEL,
    contents="Say hello in Nigerian Pidgin, two sentences max.",
)

elapsed = time.time() - start
print(f"\nReply (took {elapsed:.1f} seconds):\n")
print(response.text)