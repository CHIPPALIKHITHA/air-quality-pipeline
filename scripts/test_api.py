import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()                                  # reads your .env file
api_key = os.getenv("OPENAQ_API_KEY")

if not api_key:
    raise SystemExit("No API key found. Check your .env file.")

url = "https://api.openaq.org/v3/locations/8118"
headers = {"X-API-Key": api_key}               # how OpenAQ identifies you

response = requests.get(url, headers=headers, timeout=30)

print("Status code:", response.status_code)
print(json.dumps(response.json(), indent=2)[:1500])   # first 1500 characters