import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the key and strip hidden characters
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("❌ Missing OPENROUTER_API_KEY in your .env file.")

OPENROUTER_API_KEY = OPENROUTER_API_KEY.strip()  # Remove spaces/newlines

print(f"Key length: {len(OPENROUTER_API_KEY)}")
print(f"Key repr: {repr(OPENROUTER_API_KEY)}")

# Test API request
url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
}
data = {
    "model": "openai/gpt-4o-mini",
    "messages": [{"role": "user", "content": "Say hello"}],
    "temperature": 0,
}

try:
    r = requests.post(url, headers=headers, json=data)
    print("Status Code:", r.status_code)
    print(r.json())
    if r.status_code == 401:
        print("❌ Unauthorized! The key may be invalid or from the wrong account.")
except Exception as e:
    print("Request failed:", e)
