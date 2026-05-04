import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key: {api_key[:10]}...")

try:
    client = Groq(api_key=api_key)
    print("Client created.")
    
    print("Listing models...")
    models = client.models.list()
    for m in models.data:
        print(m.id)
except Exception as e:
    print(f"Error: {e}")
